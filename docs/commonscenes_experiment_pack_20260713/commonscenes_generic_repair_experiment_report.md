# CommonScenes Generic Repair 实验报告

日期：2026-07-13  
实验对象：CommonScenes bedroom split，162 个场景  
最终主方法：`generic relation-aware repair + movement/collision gate`，阈值 `t=1.5`

## 1. 实验结论

本轮实验已经去掉 `official-search` 相关结果。主方法不调用 CommonScenes 官方 evaluator，不根据官方分数决定是否修复，只使用通用几何关系、移动距离、边界和碰撞惩罚。

主结论：

- `generic-gate t1.5` 相比 CommonScenes baseline 提升通用关系满足率：`0.9813 -> 0.9844`。
- 碰撞 penalty 下降：`164.012 -> 161.487`。
- 视觉扰动很小：平均 SSIM `0.9980`，平均 PSNR `80.29 dB`。
- 改动很克制：只改动 `1.38%` 的 box，平均中心位移 `0.0155m`。
- CommonScenes 官方分数作为外部评估略降：`0.9732 -> 0.9696`。这说明主方法没有针对官方 evaluator 特化，也提醒论文中不能声称它提升 CommonScenes 官方指标。

推荐论文表述：

> Our generic relation-aware repair improves general geometric relation consistency and reduces collision while preserving rendered and mesh-level geometry. We report the CommonScenes official constraint score only as an external diagnostic metric, not as an optimization target.

## 2. 实验数据与产物整理

本地报告包：

```text
docs/commonscenes_experiment_pack_20260713/
  data/
    generic_gate_t0.8_repair_summary.json
    generic_gate_t1.2_repair_summary.json
    generic_gate_t1.5_repair_summary.json
    generic_gate_t1.5_quality_summary.json
    generic_gate_t1.5_mesh_chamfer_summary.json
    official_eval_generic_gate_summary.json
  commonscenes_generic_repair_experiment_report.md
```

远端核心产物：

```text
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195
/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_pt_epoch195_bedroom
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_render_ours_generic_gate_t1.5_epoch195_bedroom
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_compare_epoch195_bedroom
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_mesh_metrics_epoch195_bedroom
```

远端日志：

```text
/root/RelationAwareInstructScene/logs/commonscenes/eval_bedroom_epoch195_export_fullshape_pt_20260713.log
/root/RelationAwareInstructScene/logs/commonscenes/render_baseline_epoch195_bedroom_20260713.log
/root/RelationAwareInstructScene/logs/commonscenes/render_ours_generic_gate_t15_epoch195_bedroom_20260713.log
/root/RelationAwareInstructScene/logs/commonscenes/compare_ours_generic_gate_t15_epoch195_bedroom_20260713.log
/root/RelationAwareInstructScene/logs/commonscenes/mesh_chamfer_generic_gate_t15_epoch195_bedroom_20260713.log
/root/RelationAwareInstructScene/logs/commonscenes/eval_official_generic_gate_epoch195_bedroom_20260713.log
```

## 3. 环境与数据状态

已补齐的环境：

- `Open3D`
- `PyTorch3D`
- CommonScenes Chamfer CUDA extension
- 3D-FUTURE SDF 数据
- CommonScenes full-shape generation path
- GLB/PNG rendering path

数据量：

| 项目 | 数量 |
|---|---:|
| baseline full-shape `.pt` | 162 |
| baseline rendered PNG | 162 |
| generic-gate t1.5 `.pt` | 162 |
| generic-gate t1.5 PNG | 162 |
| generic-gate t1.5 GLB | 162 |
| GLB Chamfer 有效场景 | 162 |

## 4. 方法说明

### 4.1 CommonScenes baseline

CommonScenes baseline 使用官方 checkpoint `epoch195` 生成 bedroom 场景：

- boxes
- angles
- generated SDF
- full-shape `.pt`
- rendered PNG
- GLB scene

### 4.2 Generic-Gate 主方法

主方法只在 CommonScenes 输出后做后处理，不改模型权重、不重新训练。

处理流程：

```text
CommonScenes boxes + generated SDF
  -> generic relation-aware repair
  -> movement/collision/boundary gate
  -> repaired boxes + original generated SDF
  -> same renderer
  -> PNG / GLB / metrics
```

使用的通用规则：

- `left/right/front/behind` 方向关系
- `close by` 平面距离
- 最大移动距离阈值
- 碰撞 penalty
- 边界 penalty
- 移动距离 penalty

不使用：

- CommonScenes 官方 `validate_constrains` 作为接受条件
- 测试集官方分数作为优化目标
- official-search 结果作为主结论

## 5. 阈值消融实验

阈值表示单个物体允许的最大中心移动距离。

| 阈值 | 接受场景 | edits | 通用关系 Total | 碰撞 penalty | 改动 box 比例 | 平均位移 | 最大位移 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0 | 0 | 0.9813 | 164.012 | 0 | 0 | 0 |
| t=0.8 | 3 | 3 | 0.9818 | 163.575 | 0.26% | 0.0018m | 0.7267m |
| t=1.2 | 13 | 13 | 0.9839 | 162.251 | 1.12% | 0.0100m | 1.1974m |
| t=1.5 | 16 | 16 | 0.9844 | 161.487 | 1.38% | 0.0155m | 1.4904m |

选择 `t=1.5` 的原因：

- 通用关系 Total 最高。
- 碰撞 penalty 最低。
- 改动比例仍然很小。
- 最大位移低于 1.5m，视觉扰动可控。

## 6. 外部官方指标评估

CommonScenes 官方 constraint score 只作为外部评估，不参与主方法决策。

| 方法 | 官方 Total | 官方 mean-of-means | close by | symmetrical to |
|---|---:|---:|---:|---:|
| baseline | 0.9732 | 0.9276 | 0.8308 | 0.5250 |
| generic-gate t0.8 | 0.9723 | 0.9264 | 0.8231 | 0.5250 |
| generic-gate t1.2 | 0.9708 | 0.9280 | 0.8000 | 0.5750 |
| generic-gate t1.5 | 0.9696 | 0.9261 | 0.7846 | 0.5750 |

解释：

- 主方法没有针对 CommonScenes 官方 evaluator 优化，所以官方 Total 略降。
- `symmetrical to` 有提升，但 `close by` 下降，导致 Total 下降。
- 这应在论文中如实报告，避免把通用几何修复误写成官方指标提升方法。

## 7. 渲染质量指标

仅对最终主方法 `generic-gate t1.5` 做完整渲染质量评估。

| 指标 | 数值 |
|---|---:|
| scenes_pt | 162 |
| scenes_png | 162 |
| changed_box_ratio | 1.38% |
| mean_center_movement | 0.0155m |
| max_center_movement | 1.4904m |
| mean_abs_pixel_diff | 0.1695 |
| mean_changed_pixel_ratio | 0.1777% |
| mean_ssim | 0.9980 |
| mean_psnr | 80.29 dB |

解释：

- 渲染图几乎保持一致。
- 修复主要改变少量布局关系，不会大面积破坏视觉结果。
- 这支持“低扰动后处理”的论点。

## 8. GLB / Mesh 几何扰动

基于 baseline GLB 与 generic-gate GLB 的 scene-level 点云 Chamfer。

采样方式：

- 每个 GLB 场景采样约 2500 个 surface points。
- 使用双向 nearest-neighbor distance。
- 统计 scene-level Chamfer。

结果：

| 指标 | 数值 |
|---|---:|
| valid scenes | 162 |
| mean Chamfer | 0.1288 |
| median Chamfer | 0.1134 |
| max Chamfer | 0.6706 |
| mean baseline-to-generic | 0.0642 |
| mean generic-to-baseline | 0.0645 |

解释：

- 几何差异存在，但整体幅度较小。
- 因为 generic-gate 只移动少量 box，SDF 形状本身不变，所以差异主要来自物体位置变化，而不是形状崩坏。

## 9. 执行命令摘要

baseline full-shape 导出：

```bash
cd /root/RelationAwareInstructScene/repos/commonscenes/scripts
PYTHONPATH=/root/RelationAwareInstructScene/repos/commonscenes \
python eval_3dfront_export_fullshape_pt.py \
  --dataset /root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT \
  --exp /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all \
  --epoch 195 \
  --visualize False \
  --evaluate_diversity False \
  --num_samples 1 \
  --gen_shape True \
  --export_3d True \
  --no_stool True \
  --room_type bedroom
```

generic-gate 阈值扫描：

```bash
python /root/RelationAwareInstructScene/scripts/repair_commonscenes_fullshape_pt_generic_gate.py \
  --pt-dir /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195 \
  --layout-json /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_bedroom_epoch195.json \
  --out-dir /root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_pt_epoch195_bedroom \
  --passes 2 \
  --max-move 1.5
```

generic-gate 渲染：

```bash
python /root/RelationAwareInstructScene/scripts/render_commonscenes_fullshape_pt_param.py \
  --pt-dir /root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_pt_epoch195_bedroom \
  --out-dir /root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_render_ours_generic_gate_t1.5_epoch195_bedroom
```

图像质量对比：

```bash
python /root/RelationAwareInstructScene/scripts/compare_commonscenes_outputs_quality.py \
  --base-pt /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195 \
  --ours-pt /root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_pt_epoch195_bedroom \
  --base-png /root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom/png \
  --ours-png /root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_render_ours_generic_gate_t1.5_epoch195_bedroom/png \
  --out-dir /root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_compare_epoch195_bedroom
```

GLB Chamfer：

```bash
python /root/RelationAwareInstructScene/scripts/compute_commonscenes_glb_chamfer.py
```

## 10. 可靠性与局限

可靠性：

- 162 个场景完整跑通。
- baseline 和 generic-gate 使用同一批 full-shape SDF。
- baseline 和 generic-gate 使用同一 renderer。
- 已有布局关系、碰撞、渲染图、GLB 几何多维指标。
- official evaluator 只作为外部评估，不作为优化目标。

局限：

- 目前只跑 bedroom split。
- CommonScenes 官方 Total 略降，不能声称主方法提升官方指标。
- Chamfer 是 scene-level GLB 采样指标，不是物体语义对齐 Chamfer。
- 还没有回到原始 InstructScene/Respace 实验集验证泛化。
- 还没有多随机种子。

## 11. 下一步实验建议

优先级最高：

1. 回到原始实验集跑 `generic-gate t1.5`，确认不会破坏原结论。
2. 在 CommonScenes 上补 livingroom / diningroom / library 或 all-room。
3. 做 object-level Chamfer，而不是只做 scene-level GLB Chamfer。
4. 做多 seed 或不同采样子集，确认 t=1.5 不是偶然。
5. 把脚本整理成一键复现入口。

论文表格建议：

- 主表：baseline vs generic-gate t1.5。
- 消融表：t0.8 / t1.2 / t1.5。
- 外部指标表：CommonScenes official score，只标注为 evaluation-only。
- 附录：失败/下降原因分析，尤其是 official close-by 指标下降。

## 12. 建议上传到 GitHub 的内容

应上传：

```text
scripts/repair_commonscenes_fullshape_pt_generic_gate.py
scripts/render_commonscenes_fullshape_pt_param.py
scripts/compare_commonscenes_outputs_quality.py
scripts/compute_commonscenes_glb_chamfer.py
docs/commonscenes_experiment_pack_20260713/
```

不建议上传：

```text
*.pt 全量文件
PNG/GLB 全量渲染目录
3D-FUTURE-SDF 数据
CommonScenes checkpoint
```

可选上传：

```text
少量代表性 PNG/GLB 样例
summary JSON
HTML/Markdown 报告
```

## 13. 最终判断

如果目标是论文可靠性，当前最稳的主结果是：

```text
CommonScenes baseline vs generic-gate t1.5
```

这个结果不依赖 official-search，不特化官方 evaluator，能支持以下较稳妥的论文结论：

> 通用关系感知后处理可以在低视觉扰动下改善几何关系一致性并降低碰撞，但它不保证提升 CommonScenes 官方约束指标。

## 14. Other-Room Completion: LivingRoom / DiningRoom / Library

This section was added after completing the requested cross-room supplement. The official single-room CommonScenes export entry failed for `livingroom` because the room-specific class list changed the model embedding size. To keep the checkpoint and class vocabulary consistent, the full-shape baseline was exported with `--room_type all`, then filtered into exact room subsets:

- LivingRoom: 52 scenes
- DiningRoom: 69 scenes
- Library: 56 scenes

The repair setting was unchanged from the main result: `generic-gate t1.5`, `--passes 2`, no official-search.

| room | scenes | baseline generic total | repaired generic total | delta | collision penalty baseline -> repaired | changed box ratio | mean move | mean SSIM | mean PSNR | mean GLB Chamfer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| livingroom | 52 | 0.970915 | 0.973113 | +0.002198 | 54.798 -> 51.841 | 0.036545 | 0.037404 | 0.994654 | 61.967 | 0.131053 |
| diningroom | 69 | 0.968892 | 0.970467 | +0.001575 | 103.200 -> 99.130 | 0.023392 | 0.018451 | 0.998741 | 77.319 | 0.087553 |
| library | 56 | 0.958588 | 0.964019 | +0.005431 | 72.028 -> 68.498 | 0.040541 | 0.038693 | 0.996117 | 56.616 | 0.130930 |

Main interpretation: the same generic repair rule gives small but consistent relation-score gains and collision-penalty reductions across these three non-bedroom room types. Visual changes remain limited by SSIM and changed-box ratio, but the maximum object movement can still approach the 1.5m gate, so per-scene inspection remains necessary for the largest-change cases.

Commands used:

```bash
bash /root/RelationAwareInstructScene/scripts/run_export_all_rooms_fullshape.sh
bash /root/RelationAwareInstructScene/scripts/run_repair_other_rooms_t15.sh
bash /root/RelationAwareInstructScene/scripts/run_render_other_rooms_t15.sh
python /root/RelationAwareInstructScene/scripts/compare_commonscenes_outputs_quality.py ...
python /root/RelationAwareInstructScene/scripts/compute_commonscenes_glb_chamfer_param.py ...
```

Remote artifact roots:

```text
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/room_subsets
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/fullshape_pt_epoch195_generic_gate_t1.5_{livingroom,diningroom,library}
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_render_baseline_epoch195_{livingroom,diningroom,library}
/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_render_ours_generic_gate_t1.5_epoch195_{livingroom,diningroom,library}
```

Local summary JSONs:

```text
docs/commonscenes_experiment_pack_20260713/data/other_rooms/
```

Reliability notes:

- These are still post-processing repairs over CommonScenes generated scenes, not retraining.
- The full-shape export took about two hours on the current AutoDL card; this is a reproducibility cost.
- The comparison is valid as same-renderer, same-scene baseline vs repaired output, but it is not yet a human preference study.
- Scene-level GLB Chamfer measures geometric change, not semantic correctness by itself.
