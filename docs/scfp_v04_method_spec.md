# SCFP v0.4 方法规范

**日期：** 2026-07-29  
**状态：** 实现完成 / 论文晋级待验证
**目标：** 为当前主线寻找比 Collision-gated Floor-Prior 更强、但仍可审计的后处理主方法。

> SCFP = Safety-Certified Feasible Projection。
> 这一版的核心变化不是再做更复杂的 proposal 规则，而是把“可行域”本身定义清楚：
> 先把 Floor-Prior 作为 anchor，再只在严格可行域内做数值投影。

## 1. 一句话定义

SCFP v0.4 是一个 training-free 的布局后处理器：它把 Collision-gated Floor-Prior 当作 anchor，把候选生成器降级为数值初始化器，然后在统一可行域里选择词典序更优的投影；若不存在支配 anchor 的可行候选，投影结果就是 anchor 本身。

## 2. 为什么要有这一版

前一轮探索已经说明：

- 只修一个局部几何公式，通常只能改变少量记录的选择；
- 继续在已见 531 records 上调参，不会把方法变成可投稿的主方法；
- 真正缺的不是更多启发式，而是一个能被审稿人理解和检查的“统一可行域”。

因此，SCFP v0.4 不再把方法贡献定义为“更聪明的 nudging”，而定义为“更严格的安全投影”。

## 3. 方法边界

SCFP v0.4 只做以下事情：

1. 以 Collision-gated Floor-Prior 布局 \(X^F\) 作为 anchor；
2. 对原始布局 \(X^0\) 和关系提议 \(R\) 做数值初始化；
3. 在统一可行域内优化一个布局候选；
4. 如果没有候选比 anchor 更好，就返回 anchor 本身。

SCFP v0.4 不做以下事情：

- 不重新训练生成器；
- 不引入房型专属规则；
- 不做 relation-specific edit set；
- 不把 evaluator 放进优化循环；
- 不在已见 531 records 上继续调参并声称验证。

## 4. 输入、输出与 anchor

### 输入

- 原始布局 \(X^0\)；
- 关系集合 \(R\)；
- Floor-Prior / Collision-gated Floor-Prior 布局 \(X^F\)；
- 对象尺寸、对象类别、朝向，以及可选的可信房间边界；
- 固定的预算、阈值和随机种子。

### 输出

- 修复布局 \(X^\star\)；
- 或者在没有严格改进时输出 \(X^F\)；
- 以及一份可复现证书，记录输入哈希、配置哈希、seed、约束残差、证明义务和调用方提供的 commit provenance。

### Anchor 语义

Floor-Prior 不再只是比较基线，而是：

- 可行解 anchor；
- 数值初始化的起点；
- 无支配可行候选时的恒等投影结果，而不是事后安全回退。

这保证了方法的默认行为是保守的。

Anchor 使用
`collision-gated-floor-prior-v2-fail-closed`：只要 original 或 repair
任一 cached mesh 结果不可用，就保留 original。冻结的 531 条 canonical
记录两侧 mesh 结果均可用，因此该版本化硬化不改变既有 canonical
选择，只修正未来缺失数据时的行为。

## 5. 统一可行域

SCFP v0.4 的可行域不是单一阈值，而是以下约束的交集。

### 5.1 movement 与 edit 约束

- 总移动量不超过冻结上限；
- 单物体移动量不超过冻结上限；
- 被编辑对象数不超过冻结 edit cap。

这些约束用于阻止“靠更大位移换提升”。

### 5.2 previously satisfied relation preservation

对 anchor 已满足的关系，SCFP v0.4 不允许候选把它们破坏掉。

这条约束的优先级高于继续挪动对象来追求局部覆盖。

### 5.3 exact OBB non-regression

候选不得增加：

- exact OBB collision pairs；
- exact OBB overlap area。
- 任意新的 exact OBB collision pair；
- 任意 anchor 已有 collision pair 的单对 overlap area。

其中后两条把聚合安全升级为 pairwise contact monotonicity：

\[
\mathcal C(X) \subseteq \mathcal C(X^F), \qquad
\forall (i,j)\in\mathcal C(X^F),\
a_{ij}(X)\le a_{ij}(X^F)+\epsilon.
\]

这能拒绝“消除一个旧碰撞、同时制造一个同面积新碰撞”的 pair-swap 反例。这里的 OBB 是硬可行性约束，不是 soft regularizer。

### 5.4 boundary constraint

房间边界是可选硬门控：

- 当调用方提供可信边界时，候选的 boundary penalty 和 violation count 不得相对 anchor 变差；
- 当没有可信边界时，证书必须标记该约束不可用，且论文不得声称真实边界安全。

### 5.5 external safety fail-closed

如果调用方请求外部安全检查，例如远程 FCL，则它和本地几何门控必须合取：

- 任一检查失败，候选直接失败；
- 不允许外部 callback 覆盖本地门控；
- callback 对任一候选不可用或报错时，该候选失败；
- confirmatory promotion 不允许缓存 anchor 结果替代新候选重算。

## 6. 候选生成：只允许数值初始化

SCFP v0.4 不把候选生成看成算法核心，而看成数值初始化。

当前冻结实现允许的初始化器包括：

- Collision-gated Floor-Prior anchor / warm start；
- 单 proposal 的 deterministic pair projection（含 close-direction cone-ball 投影）；
- 固定 seed 的 SLSQP local restarts。

不允许的初始化器包括：

- room-specific heuristics；
- 多 proposal 拼接式 nudging；
- 依赖 evaluator 反馈的闭环搜索。

单 proposal initializer 只是求解器初始化，不作为方法贡献单独 claim。独立评估器也不进入候选生成或选择闭环。

## 7. 词典序目标

候选在可行域内按以下顺序排序：

1. coverage；
2. weighted violation；
3. exact OBB collision pairs 与 overlap area；
4. 可用时的 boundary / external safety 代价；
5. movement；
6. edit count。

解释如下：

- coverage 先于一切，因为如果覆盖不足，后续代价都没有意义；
- weighted violation 只在 coverage 同级时比较；
- exact OBB 优先于 movement，因为安全非退化比“少动一点”更重要；
- movement 优先于 edit count，因为 edit count 只是在 tie-break 中进一步约束稀疏性。

如果某个候选没有比 anchor 更好的最优前缀，anchor 直接胜出。

这里“支配 anchor”要求关系前缀严格改善：coverage 增加，或在
coverage 不变时 weighted violation 的下降量严格大于冻结的
`improvement_epsilon`。OBB、boundary、external safety、movement 和
edit count 用于可行性认证与候选间 tie-break，不能单独触发一次布局
修改。

令 \(\mathcal I(X^0,X^F,R)\) 为冻结初始化器和局部求解器产生的有限
候选集，\(\mathrm{Cert}(X;X^F)\) 为第 5 节的完整可行性证书，
\(\succ_R\) 为上述关系前缀支配关系，则实现的投影算子是：

\[
\mathcal F_{\mathcal I} =
\{X\in\mathcal I:
\mathrm{Cert}(X;X^F)=1 \land X\succ_R X^F\},
\]

\[
\Pi_{\mathrm{SCFP}}(X^0,X^F,R)=
\begin{cases}
\operatorname*{lexmin}\limits_{X\in\mathcal F_{\mathcal I}}
L_{\mathrm{lex}}(X), & \mathcal F_{\mathcal I}\neq\varnothing,\\
X^F, & \mathcal F_{\mathcal I}=\varnothing.
\end{cases}
\]

这是一个确定性的 candidate-set projection；它的保证来自证书和
anchor 的可行性，而不是对连续非凸问题作全局最优承诺。

## 8. 主方法行为

SCFP v0.4 的决策规则是：

1. 生成一组冻结的数值初始化并运行局部连续求解；
2. 为每个候选计算完整约束证书；
3. 只保留严格可行且支配 anchor 的候选；
4. 按词典序选择最优候选；
5. 如果没有严格改进，返回 Floor-Prior anchor。

这意味着 SCFP v0.4 不是“总能修改布局”的方法，而是“只在能严格改进时修改”的方法。

实现上，SLSQP 直接处理连续 movement budget；relation preservation、
exact OBB、boundary 和外部黑盒安全则在每个候选求解后统一认证。因而
SCFP 保证“最终返回结果属于声明的可行域”，但不声称 SLSQP 已把所有
黑盒约束光滑地编码进内部迭代，也不声称找到连续可行域的全局最优解。
更准确的实现描述是：**局部候选优化 → 全约束认证 → 词典序选择或返回
anchor**。

为兼容旧接口，`accepted=false` 仍表示“没有修改布局”，不表示投影
失败。SCFP 证书另行记录 `projection_succeeded`、`layout_modified` 和
`selected_solution.role`，以区分可行的 anchor 恒等投影与候选失败。

## 9. 实施门槛

SCFP v0.4 只有在下面这些实现门全部满足时，才允许进入任何正式结果目录：

- 配置文件冻结；
- 输入 manifest 冻结；
- evaluator 版本冻结；
- 代码 commit 冻结；
- 证书包含输入哈希、配置哈希和 commit；
- 任一候选失败都不得替换 anchor；
- 任何 NaN / Inf 都视为失败。

## 10. 论文晋级门槛

SCFP v0.4 只有在以下门都通过后，才能考虑替代当前主方法：

1. 新 confirmatory cohort 与当前已见 500 source clusters 零重叠；
2. 独立 evaluator 完成冻结，并通过 human audit；
3. 所有被接受候选完成 remote FCL 重算；
4. 在 confirmatory cohort 上相对 Collision-gated Floor-Prior 的 pooled 提升为正，且 95% CI 下界 > 0；
5. 三个房型的点估计都为正；
6. movement ratio 在冻结区间内；
7. exact OBB 和 external safety 均不劣；
8. 不再依赖已见 531 records 的调参结果来宣称验证。

如果任何一条不满足，SCFP v0.4 只能作为探索性候选或失败分析，不能作为论文默认主方法。

## 11. 允许的论文表述

如果未来晋级成功，论文可以写成：

> SCFP is a safety-certified feasible projection layer that uses Collision-gated Floor-Prior as a conservative anchor and improves relation coverage only when it can do so without degrading exact OBB or external safety checks.

在晋级之前，只能写“proposed design”或“exploratory candidate”，不能写“demonstrated improvement”。

## 12. 当前结论

SCFP v0.4 的实现、证书和合成性质测试已经落地，但尚未取得论文晋级证据。

它目前证明的是“方法可审计、可冻结，并能拒绝接触对交换与单对恶化反例”，不是“在新数据上已经优于当前主方法”。论文默认方法仍为 Collision-gated Floor-Prior。

当前 exact OBB 证书是 XZ 平面 oriented-footprint 的精确多边形相交，
不是完整 3D mesh / FCL 安全证书；后者仍需对每个新候选远程重算。
