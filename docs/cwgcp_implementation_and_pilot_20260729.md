# CW-GCP v0.2.1 实现与 531 记录 Pilot 报告

**日期：** 2026-07-29

**分支：** `codex/cwgcp-optimization`

**决策：** 实现与本地 CPU pilot 完成；论文主方法升级 **NO-GO**。

## 1. 本轮交付

- 实现置信度加权的全局关系约束投影、Hungarian 实例匹配、歧义降权和 slack；
- 实现稀疏编辑、单物体/场景总移动预算、确定性 multi-start SLSQP；
- 增加既有满足关系、精确旋转 OBB、边界、预算和外部安全的合取门控；
- 将 Collision-gated Floor-Prior 作为 warm start，而非未经证明的新算法结果；
- 将独立关系 evaluator 和谓词 schema 与优化器代码分离并冻结版本；
- 实现同移动预算的安全随机对照和无 confidence/slack 的 generic optimizer；
- 输出逐记录指标、修复布局、证书、输入/配置 hash、代码 commit 和 5,000 次
  scene-bootstrap。

## 2. 审核后修复

1. 将 `obb_only` 新候选实验与 `cached_fcl` 归档安全选择器明确分离；
2. 外部 callback 返回空值、NaN/Inf 或键不一致时 fail closed，且不能绕过 OBB；
3. 所有连续配置拒绝 NaN/Inf，迭代计数和 CLI 参数执行正值校验；
4. assignment 置信度改用“实际分配代价到最佳备选代价”的 gap；
5. 边界门同时约束连续 penalty 和 violation count；
6. 随机基线用最多 64 次拒绝采样匹配实际移动量（±5%）并保持 OBB 不劣；
7. 输入校验检测同一导出文件内重复 UID；跨模型/房间的同源 UID 使用复合
   `evaluation_uid`，避免把不同生成结果错误合并；
8. certificate 的 `input_hash` 覆盖布局、关系、边界、warm start、外部安全元数据
   和输入文件 provenance。

## 3. 数据与协议

- Bedroom 162、Dining room 177、Living room 192，共 531 条生成结果记录；
- 531 个复合 `evaluation_uid`，对应 500 个唯一源场景 UID；
- 708 个归档 repair-target relations；
- 所有方法使用相同导出记录和冻结独立 evaluator；
- CW-GCP 的移动上限取每条记录 Floor-Prior 的实际移动预算；
- bootstrap 单位为生成结果记录，5,000 次；
- 本机没有 `python-fcl`、3D-FUTURE mesh 和真实房间 polygon。

708 是本次三个 canonical JSON 的 repair-target 口径，不得与其他文档中的
808 或 1,296 口径混用。

## 4. 新候选实验：`obb_only`

该模式允许全局 solver 产生新布局，但只能声称通过精确 OBB 安全门，不能声称
mesh-safe。

| 方法 | 关系准确率 | 平均 OBB pairs | 平均 OBB overlap | 平均移动 |
|---|---:|---:|---:|---:|
| Baseline | 62.85% | 6.2505 | 1.1115 | 0.0000 |
| Collision-gated Floor-Prior | **67.66%** | 6.1789 | 1.0950 | 0.0957 |
| Movement-matched random | 63.42% | 6.1714 | 1.0974 | 0.0957 |
| Same-budget generic optimizer | 67.09% | 6.1902 | **1.0941** | 0.0534 |
| CW-GCP v0.2.1 | 67.09% | 6.1883 | **1.0942** | 0.0552 |

| 配对对比 | 准确率差 | 95% CI |
|---|---:|---:|
| CW-GCP − Baseline | +4.24 pp | [+2.76, +5.91] pp |
| CW-GCP − Floor-Prior | **−0.56 pp** | [−1.41, +0.14] pp |
| CW-GCP − Random | +3.67 pp | [+2.27, +5.17] pp |
| CW-GCP − Generic | 0.00 pp | [0.00, 0.00] pp |

- 接受 35/531：solver 9、Floor-Prior warm start 26，其余 496 安全回退；
- 公平 generic 对照使用完全相同的 warm start、预算、restarts 和 safety callback；
  它与 CW-GCP 的关系准确率相同，当前数据不能证明 confidence/slack 有额外贡献；
- CW-GCP/Floor-Prior 平均移动比 0.577，没有满足 movement-matched ±5% 的
  方法升级门；
- 三个房间相对 Floor-Prior 的点估计均为负；
- CPU solver signal：`false`。

## 5. 归档选择器实验：`cached_fcl`

该模式只识别有归档 FCL 结果的原始布局和 Floor-Prior warm start；新 solver
candidate 因无法重算 FCL 而 fail closed。因此它是守卫选择器，不是对全局求解器
mesh 安全性的验证。

| 方法 | 关系准确率 | 平均 mesh pairs | 平均 OBB pairs | 平均移动 |
|---|---:|---:|---:|---:|
| Collision-gated Floor-Prior | **67.66%** | **2.0640** | 6.1789 | 0.0957 |
| CW-GCP cached selector | 66.81% | 2.0829 | 6.2015 | 0.0495 |

相对 Floor-Prior 为 −0.85 pp，cluster-bootstrap 95% CI
[−1.70, −0.14] pp；选择 27 个
Floor-Prior warm start，504 个记录回退原始布局，没有选择新 solver candidate。

## 6. 投稿决策

CW-GCP 相对 baseline 和 movement-matched random 的 cluster-bootstrap 区间为正，
说明“关系感知的全局投影”是有价值的研究方向；但当前证据不支持替换主方法：

1. 相对 Floor-Prior 的总体 CI 未严格大于 0，三个房间点估计也均为负；
2. 实际平均移动只有 Floor-Prior 的 57.7%，不满足预注册 movement-match 门；
3. `cached_fcl` 选择器的准确率与 mesh collision pairs 都更差；
4. 新 solver candidates 尚无 FCL 重算、真实房间边界和人工 evaluator audit；
5. 类别级关系不能验证 mention-to-instance assignment 的真实准确率。
6. 公平 generic 对照与 CW-GCP 的关系准确率完全相同，尚无 confidence/slack
   组件带来额外收益的证据。

因此投稿主线继续使用 Collision-gated Floor-Prior。CW-GCP 只能作为：

- stronger optimizer baseline；
- 后续工作的候选算法与失败分析；
- 在远程 FCL、人工审计和冻结验证通过前，不进入摘要主 claim。

## 7. 复现

```powershell
python -m unittest tests.test_cwgcp -v

python scripts/run_cwgcp_pilot.py `
  --output-dir results/cwgcp_pilot/20260729_final_obb_only_generic `
  --bootstrap-samples 5000 `
  --include-generic `
  --safety-mode obb_only

python scripts/run_cwgcp_pilot.py `
  --output-dir results/cwgcp_pilot/20260729_final_cached_fcl_selector `
  --bootstrap-samples 5000 `
  --include-generic `
  --safety-mode cached_fcl
```

每个结果目录包含 `summary.md`、`summary.json`、`paired_scene_metrics.csv` 和
`certificates.jsonl`。

## 8. 重新评估升级的必要条件

1. 为全部新候选在冻结服务器环境重算 FCL；
2. 三类房间分层双标不少于 90 条关系，并报告一致率/Cohen's kappa；
3. 对重复类别场景建立 mention-to-instance 标注；
4. 获得真实房间 polygon 后重跑 boundary containment；
5. 在冻结验证集上相对 Floor-Prior 的总体 95% CI 下界严格大于 0、每类房间
   点估计为正、移动比在 [0.95, 1.05]、FCL 和 OBB 均不劣，才可升级。
