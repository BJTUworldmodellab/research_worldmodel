# FA-PSP v0.3 主方法候选与后续任务

**日期：** 2026-07-29
**投稿目标：** CCF-B，优先 Eurographics 2027 Full Papers / CGF
**当前决策：** FA-PSP v0.3 是首选本地主方法候选；最终投稿升级仍为 NO-GO。

## 1. 方法是什么

FA-PSP（Floor-Anchored Proposal-Set Projection）是在生成后做小幅、可回退的布局约束投影，不重新训练生成器。

给定原始布局 \(X^0\) 和通过 collision gate 的 Floor-Prior 布局 \(X^F\)，每个场景的总移动预算为

\[
B(X)=\min\left(3.6,\;\lVert X^F-X^0\rVert_{2,1}+0.10\right).
\]

方法按以下顺序工作：

1. 把 \(X^F\) 设为 anchor、比较基线和失败回退；
2. 对 anchor 尚未满足的 class-level relation proposal，生成跨过冻结 margin 的确定性 proposal-nudge 候选；
3. 同时保留 Floor warm-start refinement 和 SLSQP residual projection 作为候选生成器；
4. 候选必须严格增加 proposal coverage，不能破坏 anchor 已满足关系；
5. 候选不能增加 exact OBB collision pairs、overlap area、边界 violation，也不能越过移动和编辑数预算；
6. 如果启用 FCL，mesh gate 与本地几何 gate 合取并 fail closed；
7. 按“覆盖数、连续 violation、OBB、安全、移动量”词典序选择；没有合格候选就原样返回 \(X^F\)。

当 anchor 已满足全部 proposal 时，求解器直接返回 anchor。该快速路径不改变输出，只避免无意义优化。

## 2. 为什么它比 AGRP 更适合作为主方法

| 开发证据 | FA-PSP v0.3 | AGRP v0.4 |
|---|---:|---:|
| 相对 Floor-Prior 关系提升 | +2.365 pp | +3.041 pp |
| 95% cluster-bootstrap CI 下界 | +0.671 pp | +1.351 pp |
| 平均移动 / Floor-Prior | **1.025×** | 2.360× |
| 相对 generic | **+2.365 pp** | 0.000 pp |
| clean mechanism ablation | `−nudge` 回落到 Floor | 无独立正信号 |
| 主叙事 | 有界、方法特异的 guarded projection | 更大移动下的 Pareto optimizer |

AGRP 的 raw accuracy 更高，但它没有证明特定机制优于同构 generic，并且移动量明显更大。FA-PSP 的绝对提升略小，却同时满足移动公平性、因果消融和三房型正方向，更符合 B 会主方法需要的可解释性。

## 3. 冻结开发结果

证据目录：`results/cwgcp_dev/20260729_E_selected_commit078f0c9_controls/`

- frozen implementation commit：`078f0c99ab157339bdce47d40edbfd81932c6690`
- source tree hash：`9d6e764c782e039c27c3ba3a2b2dfc32cfee9bd52b36ca41ee801bdcb1d632ec`
- `relevant_tree_clean=true`
- 222 generated records，209 source clusters，296 target relations
- FA-PSP：202/296，68.243%
- Floor-Prior：195/296，65.878%
- same-budget generic：195/296，65.878%
- `−proposal-nudge`：195/296，65.878%
- FA-PSP − Floor：+2.365 pp，95% CI `[+0.671,+4.545]`
- FA-PSP − generic：+2.365 pp，95% CI `[+0.671,+4.498]`
- FA-PSP − `−nudge`：+2.365 pp，95% CI `[+0.671,+4.467]`
- FA-PSP − candidate-matched random：+6.419 pp，95% CI `[+3.716,+9.396]`
- 房型点估计：bedroom +1.010 pp，diningroom +4.587 pp，livingroom +1.136 pp
- W/L/T 相对 Floor：6/0/216
- mean movement ratio：1.0252
- exact OBB pair/overlap 逐记录恶化：0/0
- runtime：median 0.0056 s，p95 2.2047 s

这些数字是开发证据，不是确认性 holdout。现有仓库所有 InstructScene-style JSON 都与已见 500 source clusters 重叠。

## 4. 当前可以和不可以 claim 什么

可以：

> 在已见 InstructScene 开发 cohort 上，FA-PSP 以相对 Floor-Prior 2.5% 的平均移动增量，提高冻结 class-level relation evaluator 的关系满足率，并在 exact OBB proxy 下保持逐场景非劣。

不能：

- 不得写成 untouched validation 或 confirmatory result；
- 不得声称 mesh-safe，直到 selected candidates 全部远程 FCL 重算；
- 不得声称 human visual quality 提升；
- 不得声称 mention-level instance grounding；
- 不得声称 global solver 是已验证贡献：当前 6 个收益全部来自 proposal nudge；
- 不得声称 SOTA。

## 5. 投稿前任务、目标与验收标准

| 优先级 | 任务 | 目标 | 交付物 | 验收标准 |
|---|---|---|---|---|
| P0 | 新 confirmatory cohort | 消除已见 500 clusters 的开发泄漏 | 冻结 manifest、overlap audit、输入 hash | 至少 500 unique source clusters、约 700 relations；UID、instruction、content hash 与开发集交集均为 0 |
| P0 | 远程 FCL 重算 | 验证 6 个及新 cohort 全部 selected candidates 的 mesh 安全 | FCL receipt、环境 hash、逐场景 pair 表 | 覆盖率 100%；每个候选不比 Floor anchor 增加 mesh collision pairs |
| P0 | 一次性确认实验 | 验证真实泛化 | seeds 0/1/2、20k cluster bootstrap、冻结 summary | 相对 Floor ≥+1.5 pp 且 CI 下界 >0；三个 seed 点估计均 >0；movement ratio 位于 [0.95,1.05] |
| P0 | 人工 evaluator audit | 校准 class-level evaluator | 至少 180 条双人盲标及裁决表 | Cohen's κ ≥0.70；evaluator 对裁决标签 accuracy ≥85% |
| P1 | 机制覆盖率 | 判断是否能从 guarded selector 升级为普适主方法 | 困难子集与 activation 报告 | overall 新候选选择率 ≥10%、每房型 ≥5%；否则论文明确称 guarded projector |
| P1 | 多实例审计 | 限定 proposal-set existential semantics 的风险 | 至少 90 个同类多实例 mention 标注 | assignment 优于 nearest-pair；否则删除 grounding/assignment 贡献 |
| P1 | 论文与表格替换 | 让方法、claim、数字完全一致 | 主表、消融表、方法节、limitations | 所有数字自动来自 frozen summary；不混用 AGRP/CW-GCP/Floor 指标 |
| P2 | 匿名复现包 | 降低 artifact review 风险 | clean-env smoke log、README、命令清单 | 新环境单命令产生同 schema 输出；无私有路径、密钥或身份信息 |

## 6. GO / NO-GO

本地算法与 OBB 开发门：**GO**。
最终论文主方法升级：**NO-GO**。

只有 P0 四项全部通过后，才能把 `configs/paper_main.yaml` 中的默认主方法从 Collision-gated Floor-Prior 切换为 FA-PSP。

## 7. v0.3.1 后续有界尝试

预注册的 Cone-Ball Close Projection 已完成，详见
`docs/fapsp_v031_final_bounded_result_20260729.md`。它在相同 222-record
冻结协议上仍为 202/296，与 v0.3 完全持平；相对 v0.3 的 paired 95% CI
为 `[-1.003,+1.003] pp`，activation 仍为 6/222。该 successor 未通过
机制特异和 activation gates，因此不替换本文件冻结的 FA-PSP v0.3。
