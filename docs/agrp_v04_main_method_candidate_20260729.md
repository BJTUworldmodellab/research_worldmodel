# AGRP v0.4 主方法候选记录

**日期：** 2026-07-29  
**目标：** 为 CCF-B 投稿寻找可替代 Collision-gated Floor-Prior 的主方法候选。  
**当前结论：** 这是历史探索记录。后续同预算控制实验表明，FA-PSP v0.3 在移动公平性和方法特异性上更适合作为主方法候选；AGRP v0.4 降级为 accuracy-movement Pareto ablation。

> 2026-07-29 更新：AGRP 的开发/locked-split 原始提升更大，但平均移动分别为 Floor-Prior 的 2.36 倍和 3.07 倍，且与其 generic control 持平。最终本地主方法决策见 `docs/fapsp_v03_main_method_candidate_20260729.md`。

## 方法定义

AGRP（Anchor-Gated Residual Projection）把 Collision-gated Floor-Prior 作为每条记录的 anchor、fallback 和比较基线，然后在固定预算内做 residual constrained projection：

1. 从原始 InstructScene 布局和 class-level relation proposals 出发；
2. 用 Floor-Prior 布局作为 warm start 和 anchor；
3. SLSQP 只搜索最多 3 个物体、总移动最多 3.6m、单物体最多 1.8m 的 XZ 平移；
4. 候选必须通过 anchor-preserving gate：
   - 不破坏 anchor 已满足的 relation；
   - 不增加 exact OBB collision pairs；
   - 不增加 exact OBB overlap area；
   - 不增加边界 violation；
   - 如启用外部 FCL，则必须 conjunctive fail-closed；
5. 如果没有候选通过 gate，则回退到 Floor-Prior anchor。

这不是生成器重训练方法，而是 post-generation layout constraint projection。

## 与 CW-GCP / FA-PSP 的区别

- CW-GCP v0.2.1：同 Floor-Prior 实际移动预算，531 记录上不超过 Floor-Prior。
- FA-PSP v0.3：加入 coverage-first 和 proposal-nudge，开发集有局部提升，但仍弱于更简单的 anchor-gated residual projection。
- AGRP v0.4：去掉过窄的 coverage-first/proposal-nudge，保留 anchor gate、warm-start refinement、candidate-matched random 控制，是当前最稳定的正信号版本。

## 开发 split 结果

路径：`results/cwgcp_pilot/20260729_agrp_v04_dev_fixedcap/`

- 222 generated records，209 source-scene clusters；
- Baseline：61.15%；
- Collision-gated Floor-Prior：65.88%；
- Candidate-matched random：61.82%；
- AGRP v0.4：68.92%；
- AGRP − Floor-Prior：+3.04 pp，95% cluster-bootstrap CI `[+1.35, +5.05]`；
- AGRP − random：+7.09 pp，95% CI `[+4.36, +9.97]`；
- selected source：199 anchor rollback，4 solver，19 warm-refine；
- mean movement：0.253m，Floor-Prior 为 0.107m，movement ratio 2.36；
- median runtime：0.115s/record，p95 0.658s/record。

## Locked validation split 结果

路径：`results/cwgcp_pilot/20260729_agrp_v04_validation_fixedcap/`

- 309 generated records，291 source-scene clusters；
- Baseline：64.08%；
- Collision-gated Floor-Prior：68.93%；
- Candidate-matched random：64.56%；
- AGRP v0.4：72.33%；
- AGRP − Floor-Prior：+3.40 pp，95% cluster-bootstrap CI `[+1.75, +5.19]`；
- AGRP − random：+7.77 pp，95% CI `[+5.00, +11.03]`；
- selected source：274 anchor rollback，8 solver，27 warm-refine；
- mean OBB collision pairs：6.003 vs Floor-Prior 6.107；
- mean OBB overlap area：1.068 vs Floor-Prior 1.122；
- mean movement：0.268m，Floor-Prior 为 0.087m，movement ratio 3.07；
- median runtime：0.087s/record，p95 0.618s/record。

## 当前 claim 边界

可以主张：

- 在已见 InstructScene repair-target 数据的 hash split 上，AGRP v0.4 相比 Collision-gated Floor-Prior 有稳定的 class-level relation accuracy 提升；
- AGRP v0.4 相比 candidate-matched random 有显著提升，说明不是“多移动随机扰动”即可得到同样收益；
- AGRP v0.4 在 OBB collision pairs 和 OBB overlap proxy 上不劣于 Floor-Prior。

不能主张：

- AGRP 已经是最终 paper main method；
- AGRP 已通过 mesh-level FCL 安全验证；
- AGRP 已在真正未见 source cohort 上确认；
- AGRP 改善 human visual quality；
- AGRP 解决 mention-level language grounding，因为当前数据只有 class-level relation proposals。

## 是否升级为主方法

当前状态：**主方法候选，暂不冻结为最终主方法。**

原因：

1. 当前 531 记录已被多轮开发查看，validation split 只能证明实现泛化，不能作为最终 confirmatory holdout；
2. 平均 movement 高于 Floor-Prior，主张必须是 Pareto 改进，而不是同移动预算改进；
3. 本地没有 FCL/mesh 环境，selected new candidates 还未做 mesh collision recomputation；
4. independent evaluator 还需要 human-audited subset；
5. generic/AGRP 口径需要在论文中统一：AGRP 本身就是 anchor-gated generic residual projection，不能再把同一算法当作反证 baseline。

## 下一步验收门

AGRP 可升级为最终主方法的最低条件：

1. 生成新的 confirmatory source cohort，和当前 500 source clusters 零重叠；
2. 冻结 commit、config、input manifest 和 evaluator 后一次性运行；
3. confirmatory cohort 上 AGRP − Floor-Prior ≥ +1.5 pp，cluster-bootstrap 95% CI 下界 > 0；
4. AGRP − candidate-matched random 的 95% CI 下界 > 0；
5. selected new candidates 的 remote FCL mesh collision pairs 不高于 Floor-Prior；
6. 至少 90 条 relation 的 human audit 支持 independent evaluator；
7. 论文 claim 明确写成 class-level post-generation constraint projection。
