# CW-GCP：置信度加权的全局约束投影

**版本：** v0.2.1 CPU/OBB 实现
**日期：** 2026-07-29
**状态：** 已完成 531 场景本地 pilot；方法升级 NO-GO，目前不是论文已验证贡献
**适用范围：** 冻结的 InstructScene/CommonScenes 输出上的 training-free 最终布局修复

> 2026-07-29 实现说明：仓库已加入 `src/cwgcp/`、独立实现的
> `src/independent_eval/cwgcp_layout_evaluator.py` 和
> `scripts/run_cwgcp_pilot.py`。v0.2 使用 Collision-gated Floor-Prior
> 作为 warm start，并修复了初版设计中的前后方向、稀疏编辑集合、既有关系保护、
> 精确 OBB gate 和类别级 proposal gate 问题。审核后又分离了 `obb_only` 新候选
> 实验和 `cached_fcl` 归档选择器，并补齐外部回调 fail-closed、输入校验、随机
> movement-match 与完整证书 hash。新候选 pilot 达到 67.09% 关系准确率，
> Floor-Prior 为 67.66%，配对差 −0.56 pp，cluster-bootstrap 95% CI
> [−1.41, +0.14] pp；
> 缓存 FCL 选择器也只有 66.81%。使用相同 warm start、预算和安全门的 generic
> 对照同样为 67.09%，因此当前证据也不能证明 confidence/slack 的额外贡献。
> 因此不升级论文主方法。

## 1. 两句话定义

现有 Floor-Prior 逐关系、逐对象地做局部贪心移动，容易受到对象匹配错误、约束冲突和“修复器与评估器共享逻辑”的影响。
CW-GCP（Confidence-Weighted Global Constraint Projection）把全部显式关系一次性写成带置信度和松弛量的全局约束，在移动预算内联合优化布局，并用与关系评分解耦的碰撞、越界和扰动门控选择安全解。

## 2. 为什么需要升级

当前仓库证据支持 Floor-Prior 是有效的保守修复器，但还存在四个直接影响投稿的弱点：

1. **局部贪心：** 按关系顺序修复，后一次移动可能破坏前一次关系，无法显式处理冲突约束。
2. **对象指代：** 当前对象配对主要依赖类别和空间近邻，同类多实例场景容易选错 subject/object。
3. **解析噪声：** 每条解析关系被近似等权处理，错误或低置信关系可能触发大幅移动。
4. **评估耦合：** 修复和部分关系评价共享规则，容易被 reviewer 质疑为优化自己的指标。

新增的 SDGScenes-inspired smoke result 进一步说明，全局约束优化可能是一个强控制基线；但该结果当前使用 simplified horizontal metric 和 AABB overlap，不能直接替代主实验。

## 3. 设计目标与非目标

### 3.1 设计目标

- 同时处理一个场景内的全部显式关系，而不是逐条贪心修复；
- 在解析错误或约束冲突时允许有代价的 slack，而不是强行满足；
- 保持 training-free、generator-agnostic 和 XZ floor-plane edit；
- 将关系优化器、物理安全门控和独立论文 evaluator 分离；
- 输出逐场景 repair certificate，便于复现、失败分析和审稿。

### 3.2 非目标

- 不生成新物体，不改变类别、尺寸、材质或资产；
- v0.1 不修改 Y、高度、support hierarchy 和 mesh geometry；
- 不声称解决 implicit commonsense、affordance、reachability 或 human preference；
- 不把独立 evaluator 放入优化循环，否则它就不再独立。

## 4. 输入与输出

### 输入

- 初始布局 \(X^0=\{x_i,z_i,y_i,s_i,\theta_i,c_i\}_{i=1}^{N}\)；
- 显式关系集合 \(R=\{(u_k,p_k,v_k,q_k)\}_{k=1}^{M}\)；
- 解析置信度 \(q_k\in[0,1]\)；
- 房间边界多边形 \(B\)；
- 每个对象的移动预算 \(b_i\) 和场景总移动预算 \(B_{\mathrm{move}}\)；
- 固定的关系阈值、碰撞配置和随机种子。

### 输出

- 修复布局 \(X^\star\) 或原始布局回退 \(X^0\)；
- repair certificate：
  - 被接受、拒绝和使用 slack 的约束；
  - 每个对象的位移；
  - 优化前后内部关系能量；
  - OBB/FCL 碰撞、越界、总移动和编辑对象数；
  - 配置 hash、代码 commit、输入 hash、seed 和终止原因。

## 5. 阶段 A：实例级对象匹配

对每个语言 mention 与同类对象建立二部图，不再直接选择最近对象。匹配代价为：

\[
C_{mi} =
\alpha_{\text{cat}}C_{\text{category}}
+\alpha_{\text{ord}}C_{\text{ordinal}}
+\alpha_{\text{ref}}C_{\text{reference}}
+\alpha_{\text{geo}}C_{\text{geometry}}.
\]

使用 Hungarian assignment 得到一对一匹配；当最佳与次佳代价差小于阈值
\(\delta_{\text{amb}}\) 时，将该关系置信度降为：

\[
\tilde q_k=q_k\cdot
\operatorname{clip}\left(
\frac{C_{2}-C_{1}}{\delta_{\text{amb}}},0,1
\right).
\]

这样，同类多实例中的不确定指代不会被当作硬约束。

## 6. 阶段 B：带 slack 的全局投影

只优化每个对象的 floor-plane displacement：

\[
\Delta_i=(\Delta x_i,\Delta z_i),\qquad
X=X^0+\Delta.
\]

Y、高度、尺寸、类别和 yaw 在 v0.1 中保持不变。

### 6.1 关系违反量

每个关系使用非负 margin violation \(v_k(X)\)。示例：

\[
\begin{aligned}
v_{\text{left}} &=
\max(0,m_{\text{lr}}-(x^-_v-x^+_u)),\\
v_{\text{front}} &=
\max(0,m_{\text{fb}}-(z^-_v-z^+_u)),\\
v_{\text{near}} &=
\max(0,d_{uv}-\tau_{\text{near}}),\\
v_{\text{far}} &=
\max(0,\tau_{\text{far}}-d_{uv}).
\end{aligned}
\]

其中 \(x^-,x^+,z^-,z^+\) 来自旋转后的 OBB footprint，而不是只用中心点。

### 6.2 优化目标

\[
\begin{aligned}
\min_{\Delta,s\ge 0}\quad
J(X,s) = &
\lambda_r\sum_{k=1}^{M}
\tilde q_k\,\rho\left(\max(0,v_k(X)-s_k)\right)\\
&+\lambda_s\sum_{k=1}^{M}\tilde q_k s_k
+\lambda_c C_{\text{OBB}}(X)
+\lambda_b C_{\text{boundary}}(X)\\
&+\lambda_m\sum_{i=1}^{N}
\operatorname{Huber}\left(\|\Delta_i\|_2/b_i\right)
+\lambda_0\sum_i \mathbf{1}[\|\Delta_i\|_2>\epsilon].
\end{aligned}
\]

约束为：

\[
\|\Delta_i\|_2\le b_i,\qquad
\sum_i\|\Delta_i\|_2\le B_{\mathrm{move}}.
\]

含义：

- \(C_{\text{OBB}}\)：旋转 footprint 的平滑碰撞/重叠代理；
- \(C_{\text{boundary}}\)：OBB 顶点越出房间多边形的惩罚；
- Huber movement：鼓励小移动但不过度惩罚少数必要移动；
- \(L_0\) 近似项：减少被编辑对象数；
- slack \(s_k\)：在解析错误或冲突关系下允许有成本地放弃约束。

## 7. 阶段 C：信赖域多起点求解

v0.2.1 使用 deterministic multi-start SLSQP，不引入学习模型，并把
Collision-gated Floor-Prior 作为一个可行 warm start。warm start 不会绕过关系、
预算或安全门。`obb_only` 模式对新候选使用精确旋转 OBB 多边形 gate；
`cached_fcl` 模式则额外要求候选必须匹配具有归档 FCL 结果的原始布局或
Floor-Prior warm start。两个 gate 为合取关系，外部 callback 不能绕过 OBB。

```text
Algorithm CW-GCP(X0, parsed_relations, room, config):
    R = resolve_instances_with_assignment(parsed_relations, X0)
    R = attach_confidence_and_detect_conflicts(R)

    candidate_set = {X0}
    for restart in deterministic_restarts(seed, K):
        X = initialize_inside_trust_region(X0, restart)
        radius = config.initial_trust_radius

        for outer_iter in 1..T:
            X_new, slack = solve_global_projection(
                X0=X0,
                init=X,
                relations=R,
                movement_budget=config.movement_budget,
                trust_radius=radius,
            )

            if internal_energy(X_new) < internal_energy(X):
                X = X_new
                radius = min(radius * 1.25, max_radius)
            else:
                radius = radius * 0.5

            if radius < min_radius or converged:
                break

        candidate_set.add(X)

    feasible = []
    for X in candidate_set:
        safety = physical_safety_metrics(X)
        if pareto_gate(X0, X, safety, config):
            feasible.add(X)

    if feasible is empty:
        return X0, rollback_certificate()

    Xstar = lexicographic_select(
        feasible,
        keys=[
            relation_violation,
            mesh_collision_pairs,
            out_of_bounds,
            total_movement,
            edited_object_count,
        ],
    )
    return Xstar, build_repair_certificate(X0, Xstar, R)
```

## 8. 阶段 D：Pareto 安全门控

候选解只有同时满足以下条件才可被接受：

1. 内部关系 violation 至少下降 \(\epsilon_r\)；
2. FCL mesh collision pair count 不增加；
3. OBB overlap 和 out-of-bound 不超过冻结容差；
4. 总移动与最大单物体移动均不超预算；
5. 编辑对象数不超过 \(K_{\mathrm{edit}}\)；
6. 所有数值有限，无 NaN/Inf。

重要边界：

- FCL/边界/移动可作为方法的安全门控；
- 独立关系 evaluator 只能在输出冻结后运行；
- 论文主表必须同时报告“全部场景”和“被门控接受场景”，避免只展示成功子集。

## 9. 独立审计边界

最终论文 evaluator \(E_{\mathrm{ind}}\) 必须满足：

- 位于独立模块，不能 import 修复器的 relation predicate；
- 阈值、对象匹配和 relation 计算独立实现并预先冻结；
- 在查看 CW-GCP 最终结果前完成版本冻结；
- 对三个房间的分层人工子集报告一致率或 Cohen's kappa；
- 输出 scene-level paired records，供 bootstrap 使用。

正确的数据流：

```text
Parser/Proposal Verifier -> CW-GCP -> Frozen Layouts
                                      |
                                      +-> FCL/Bounds Safety Report
                                      |
                                      +-> Independent Evaluator (paper metric)
                                      |
                                      +-> Human Audit Subset
```

## 10. 默认 pilot 配置

| 参数 | 建议初值 | pilot 搜索范围 |
|---|---:|---:|
| restart 数 \(K\) | 4 | 1, 4 |
| outer iteration \(T\) | 5 | 3, 5 |
| 单物体最大移动 | 1.8 m | 固定，与现主方法一致 |
| 场景平均移动预算 | movement-matched | 主方法均值的 ±5% |
| \(\lambda_r\) | 10 | 5, 10 |
| \(\lambda_s\) | 4 | 2, 4, 8 |
| \(\lambda_c\) | 20 | 10, 20 |
| \(\lambda_b\) | 20 | 固定 |
| \(\lambda_m\) | 1 | 0.5, 1 |
| \(K_{\mathrm{edit}}\) | 3 | 2, 3 |
| seed | 0, 1, 2 | 固定三种子 |

pilot 不能用最终测试结果挑阈值。建议使用开发子集调参，冻结后只运行一次最终 validation。

## 11. 必须做的对照和消融

| 实验 | 回答的问题 | 验收信号 |
|---|---|---|
| 原始 InstructScene | 生成器基线 | 固定输入 |
| Collision-gated Floor-Prior | 当前主方法 | 复现现有趋势 |
| movement-matched random | 移动本身是否带来增益 | CW-GCP 显著优于 random |
| same-budget generic optimizer | 全局优化是否足够解释增益 | 当前为 67.09% 对 67.09%，未证明 confidence/slack 额外价值 |
| CW-GCP without confidence | 置信度是否必要 | 多实例/低置信子集更差 |
| CW-GCP without slack | 冲突处理是否必要 | 冲突场景失败率更高 |
| CW-GCP without physical gate | 安全门控是否必要 | collision/OOB 更差 |
| nearest-pair vs assignment | 实例匹配是否必要 | 多实例子集显著改善 |
| parser vs oracle relations | 解析器损失上界 | 给出 parser gap |

## 12. 48 小时 pilot 的 GO / NO-GO

### 方法升级 GO

同时满足：

- 三个房间的独立 evaluator 平均增益均为正；
- relation gain 的 paired 95% CI 总体下界严格大于 0；
- 三个房间相对 Floor-Prior 的点估计均为正；
- CW-GCP/Floor-Prior 实际移动比位于 [0.95, 1.05]；
- 至少有一个新 solver candidate 被安全接受，而非只选择 warm start；
- FCL mesh collision pair rate 不劣于 Floor-Prior；
- 失败率不超过 2%，且全部失败可安全回退；
- 单场景 CPU 中位运行时间不超过 1 秒，或给出可接受解释。

### 方法升级 NO-GO

任一成立：

- 只有共享 evaluator 上变好，独立 evaluator 无增益；
- 优势完全来自更大移动预算；
- generic optimizer 在同预算下等价或更好，新增组件无消融价值；
- 物理碰撞或失败率显著恶化；
- 需要大规模调参才能在不同房间保持正增益。

NO-GO 时不继续包装新算法，回到 Collision-gated Floor-Prior，并把 CW-GCP 作为 stronger baseline 或失败分析。

## 13. 可支持的论文贡献

只有在上述实验完成后，才建议把方法 claim 升级为：

1. 一种 training-free、全局而非逐关系贪心的最终布局约束投影；
2. 用置信度和 slack 显式处理解析不确定性与冲突关系；
3. 在独立 evaluator 下改善关系满足度，同时保持移动和物理安全的 Pareto 约束；
4. 通过 repair certificate 提供逐场景可审计性。

当前阶段只能写“proposed design”，不能写“we demonstrate”或“significantly improves”。

## 14. 最强 reviewer 质疑与应对

**质疑：** 这只是把已有规则放进通用优化器，不构成足够新颖的方法。

**应对标准：**

- 用 same-budget generic optimizer 作为强基线，不回避；
- 通过 assignment、confidence、slack 和 physical gate 的逐项消融证明不是优化器本身；
- 报告多约束冲突、多实例对象和解析低置信三个困难子集；
- 如果这些组件没有稳定增益，主动降级为系统/实证贡献，不夸大算法新颖性。
