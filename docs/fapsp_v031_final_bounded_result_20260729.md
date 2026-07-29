# FA-PSP v0.3.1 最后一轮有界优化结果

**日期：** 2026-07-29  
**投稿目标：** CCF-B，优先 Eurographics 2027 Full Papers / CGF  
**结论：** 不升级。保留 FA-PSP v0.3 作为首选本地探索性候选；论文默认主方法仍为 Collision-gated Floor-Prior。

## 1. 本轮改了什么

FA-PSP v0.3.1 只引入一个预注册机制：**Cone-Ball Close Projection**。

v0.3 对 `closely left/right/in front of/behind` 的处理先把对象对推到 45° 方向锥，再径向缩进 close-distance ball。径向缩放会同时缩小 additive semantic margin，可能让候选重新离开方向锥。

v0.3.1 改为把对象对的相对位移一次投影到以下集合的交集：

\[
\mathcal{C}=
\left\{
(a,b):
a\ge |b|+m,\quad
a^2+b^2\le d_{\mathrm{close}}^2
\right\}.
\]

若投影目标超过连续移动预算，算法保留 Floor-Prior anchor，只沿 anchor 到投影目标的 residual ray 取最大预算可行步长。预算后若关系仍不可行，该候选直接丢弃。其余预算、阈值、编辑集、排序和 OBB gate 均不变。

## 2. 冻结协议与复现

- 实现 commit：`837272ebfe0555b3d92276ae4e73a70bdd9b33d1`
- source-tree SHA256：`3a1d8938f093b0314e184cd8d78bd7429ac5229a92fe68f45dc91859af536bd5`
- 输入 manifest：`configs/cwgcp_v031_input_manifest.json`
- 结果目录：`results/cwgcp_dev/20260729_H_cone_ball_commit837272e_controls`
- 222 generated records，209 source clusters，296 target relations
- source-cluster paired bootstrap：20,000 次
- `relevant_tree_clean=true`
- `frozen_input_manifest.inputs_match=true`
- `frozen_protocol_run=true`

复现命令：

```powershell
python scripts/run_cwgcp_pilot.py `
  --output-dir results/cwgcp_dev/20260729_H_cone_ball_commit837272e_controls `
  --method-profile fapsp_v031 `
  --budget-policy anchor_plus_residual `
  --anchor-residual-cap 0.10 `
  --total-movement-cap 3.6 `
  --edit-cap 3 `
  --semantic-margin 0.02 `
  --split dev `
  --split-salt cwgcp-v03-main-method-20260729 `
  --development-fraction 0.4 `
  --restarts 2 `
  --outer-iterations 2 `
  --solver-max-iterations 80 `
  --bootstrap-samples 20000 `
  --random-match candidate `
  --include-generic `
  --include-nudge-ablation `
  --include-v03-ablation
```

## 3. 完整结果

| 指标 | FA-PSP v0.3.1 | FA-PSP v0.3 | Floor-Prior | Generic | No-nudge |
|---|---:|---:|---:|---:|---:|
| 关系满足 | 202/296 | 202/296 | 195/296 | 195/296 | 195/296 |
| 关系准确率 | 68.243% | 68.243% | 65.878% | 65.878% | 65.878% |
| mean movement | 0.10882 | 0.11003 | 0.10732 | 0.11904 | 0.10732 |
| mean OBB pairs | 6.2703 | 6.2703 | 6.2793 | 6.2523 | 6.2793 |
| mean OBB overlap | 1.05553 | 1.05541 | 1.05686 | 1.04892 | 1.05686 |

关键 paired 结果：

- v0.3.1 − Floor-Prior：`+2.365 pp`，95% CI `[+0.669,+4.531] pp`
- v0.3.1 − generic：`+2.365 pp`，95% CI `[+0.671,+4.502] pp`
- v0.3.1 − no-nudge：`+2.365 pp`，95% CI `[+0.671,+4.514] pp`
- v0.3.1 − frozen v0.3：`0.000 pp`，95% CI `[-1.003,+1.003] pp`
- v0.3.1 − candidate-matched random：`+6.419 pp`，95% CI `[+3.691,+9.375] pp`
- W/L/T 相对 Floor-Prior：`6/0/216`
- W/L/T 相对 v0.3：`1/1/220`
- movement ratio 相对 Floor-Prior：`1.0139`
- exact OBB pair/area 逐记录恶化：`0/0`

房型结果：

| 房型 | 相对 Floor 点估计 | selected activation | eligible activation |
|---|---:|---:|---:|
| bedroom | 0.000 pp | 0/66 = 0.00% | 0/11 = 0.00% |
| diningroom | +5.505 pp | 5/80 = 6.25% | 5/19 = 26.32% |
| livingroom | +1.136 pp | 1/76 = 1.32% | 1/25 = 4.00% |
| overall | +2.365 pp | 6/222 = 2.70% | 6/55 = 10.91% |

## 4. 为什么不升级

预注册 hard gate 要求全部同时通过。v0.3.1 失败于：

1. bedroom 相对 Floor-Prior 的点估计为 0，不是正数；
2. 相对 frozen v0.3 没有机制特异提升，95% CI 跨 0；
3. overall activation 为 2.70%，低于 10%；
4. bedroom 和 livingroom activation 低于每房型 5%。

它通过了移动预算、零 Floor relation-loss、逐场景 OBB 非退化、generic/no-nudge/random controls，但这些不足以证明它优于 v0.3。

## 5. 得到的有效结论

- Cone-Ball 修复是数学上正确、可复现的实现改进，但没有形成更强的总体方法。
- 它把一个 bedroom gain 换成一个 diningroom gain，最终总体关系数不变；这说明收益仍由少量场景决定。
- 相比 v0.3，v0.3.1 平均移动下降约 1.10%，但关系效果无提升，适合作为负机制消融，不适合作为新主方法。
- 当前瓶颈已经不是再修一个局部投影公式，而是 OBB gate、class-level proposal semantics 和新数据泛化证据。

## 6. 后续任务

停止在已见 531 records 上继续设计第四个机制或按房型调参。后续只推进能改变论文可信度的任务：

1. 生成与已见 500 source clusters 零重叠的 confirmatory cohort；
2. 对 frozen v0.3 selected candidates 和新 cohort 做远程 FCL 重算；
3. 完成独立 evaluator 的分层人工审计；
4. 在新 cohort 上一次性运行 seeds 0/1/2 和 20k paired cluster bootstrap；
5. 仅当这些外部门全部通过，才把 `configs/paper_main.yaml` 的默认方法从 Collision-gated Floor-Prior 升级为 FA-PSP v0.3。

## 7. 结果文件哈希

- `summary.json`: `07952377ea37bdc933510c01c10ab483e289c018ed669e42657acaa73f2877e0`
- `summary.md`: `19571dcbd01877be6b9464a52d79e06e7bde136aea54406f58f4a016aa405cc4`
- `paired_scene_metrics.csv`: `ef3c915b78a93eb22d3d3688a70f0ae21f7b21fb107b94e9f6efbd1f4f5f989c`
- `certificates.jsonl`: `8b2f0a496adc02ebbd9e22f834eb953865311b5529becf18e286e2eac7e8587d`
