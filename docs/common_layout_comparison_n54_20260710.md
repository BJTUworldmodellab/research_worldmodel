# 公平规模 Common Layout 对比 - 2026-07-10

## 结论

这轮补齐了之前最明显的问题：Qwen/ReSpace 不再只用 30 个场景，而是 full-scene 和 add-only 都跑到 162 个 bedroom 场景，与原算法 bedroom floor-prior 的 162 个场景规模一致。

结果更支持原算法，而不是削弱原算法：当 Qwen/ReSpace full-scene 的平均物体数接近原算法时，它的碰撞更严重；Qwen/ReSpace add-only 的碰撞更低，但平均物体数明显少，所以不能作为“更强布局算法”的直接证据。

## 输入

| 方法 | 输入 |
|---|---|
| 原始 baseline layout | `results/floor_prior_remote/bedroom_sgdiffusion_vq_objfeat_epoch_01999_relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json`, `layout_boxes` |
| 原算法 repaired floor-prior | 同一 JSON, `repair_boxes` |
| Qwen/ReSpace full-scene n54 | `results/respace_remote/qwen_fair_bedroom_n54_20260710_123802/full_scene` |
| Qwen/ReSpace add-only n54 | `results/respace_remote/qwen_fair_bedroom_n54_20260710_123802/add_only` |

## 输出

| 产物 | 路径 |
|---|---|
| 统一评估脚本 | `scripts/compare_common_layout_metrics.py` |
| CSV 指标 | `results/tables/common_layout_metrics_n54_20260710.csv` |
| JSON 指标 | `results/tables/common_layout_metrics_n54_20260710.json` |
| 远端 summary | `results/respace_remote/qwen_fair_bedroom_n54_20260710_123802/summary_verified.json` |

## 执行命令

远端实验：

```bash
ssh autodl-current
tmux new-session -d -s fair_compare_162 'bash /root/RelationAwareInstructScene/server_setup/run_respace_qwen_fair_bedroom_n54.sh'
```

本地评估：

```powershell
$py='C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$orig=(Get-ChildItem results\floor_prior_remote -File | Where-Object { $_.Name -like 'bedroom*floor_prior_max1.8_mesh_p2*.json' } | Select-Object -First 1 -ExpandProperty FullName)
& $py scripts\compare_common_layout_metrics.py `
  --original-json "$orig" `
  --qwen-full-dir results\respace_remote\qwen_fair_bedroom_n54_20260710_123802\full_scene `
  --qwen-add-dir results\respace_remote\qwen_fair_bedroom_n54_20260710_123802\add_only `
  --out-csv results\tables\common_layout_metrics_n54_20260710.csv `
  --out-json results\tables\common_layout_metrics_n54_20260710.json
```

## 关键指标

| 方法 | 场景数 | 非空率 | 平均物体数 | 每场景重叠对数 | 脚印重叠比例 | 中心越界率 |
|---|---:|---:|---:|---:|---:|---:|
| 原始 baseline layout | 162 | 1.000 | 5.346 | 0.907 | 0.0461 | 0.0000 |
| 原算法 repaired floor-prior | 162 | 1.000 | 5.346 | 0.926 | 0.0439 | 0.0000 |
| Qwen/ReSpace full-scene n54 | 162 | 1.000 | 5.148 | 2.117 | 0.0546 | 0.0000 |
| Qwen/ReSpace add-only n54 | 162 | 1.000 | 3.673 | 0.957 | 0.0264 | 0.0015 |

## 通俗解释

1. 场景数问题已解决：现在四组都是 162 个场景。
2. full-scene 的物体数量与原算法接近：`5.148` vs `5.346`，但重叠明显更高：`2.117` vs `0.926`，脚印重叠比例也更高：`0.0546` vs `0.0439`。
3. add-only 看起来碰撞最低：`0.0264`，但它平均只有 `3.673` 个物体，所以更像“少放东西导致少碰撞”，不是公平胜出。
4. 原算法 repaired floor-prior 在保持物体数不变的情况下，把脚印重叠比例从 `0.0461` 降到 `0.0439`，这是更可解释的改进。

## 仍不可靠的地方

1. 这张表仍然是几何布局指标，不是语义关系准确率。它能说明碰撞、密度、越界，但不能直接说明“左边、前面、靠近”等文字关系是否满足。
2. Qwen/ReSpace 日志仍有部分 `raw_model.glb` 缺失警告，所以 mesh 级别结论不稳；当前主要相信 box/footprint 级别指标。
3. add-only 与原算法物体数差距仍大，因此不能作为最终强 baseline 结论，只能作为补充。

## 上传建议

```text
scripts/compare_common_layout_metrics.py
server_setup/run_respace_qwen_fair_bedroom_n54.sh
results/tables/common_layout_metrics_n54_20260710.csv
results/tables/common_layout_metrics_n54_20260710.json
docs/common_layout_comparison_n54_20260710.md
visual/common_layout_comparison_n54_20260710.html
results/respace_remote/qwen_fair_bedroom_n54_20260710_123802/
```

不要上传密码、token、原始大数据集或模型权重。
