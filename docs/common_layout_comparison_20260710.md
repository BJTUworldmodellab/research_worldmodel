# Common Layout-Metric Comparison - 2026-07-10

## Bottom Line

I completed a same-evaluator comparison between the original relation-aware floor-prior output and the Qwen/ReSpace outputs.

This is a shared geometric/layout evaluator. It is not a semantic target-relation accuracy evaluator. The comparison answers: "Are the produced layouts similarly dense, non-empty, in-bounds, and overlapping?" It does not yet answer: "Did each method satisfy the exact text relation target?"

## Inputs

| Method | Input |
|---|---|
| Original baseline layout | `results/floor_prior_remote/bedroom_sgdiffusion_vq_objfeat_epoch_01999_relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json`, `layout_boxes` |
| Original repaired floor-prior | Same JSON, `repair_boxes` |
| Qwen/ReSpace full-scene | `results/respace_remote/qwen_full_bedroom_n10_20260709_235431/respace_qwen_bedroom_vllm_n10` |
| Qwen/ReSpace add-only | `results/respace_remote/qwen_addonly_bedroom_n10_multiseed_20260710_045939/respace_qwen_addonly_bedroom_n10_multiseed` |

## Outputs

| Artifact | Path |
|---|---|
| Evaluator script | `scripts/compare_common_layout_metrics.py` |
| CSV summary | `results/tables/common_layout_metrics_20260710.csv` |
| JSON summary | `results/tables/common_layout_metrics_20260710.json` |

## Executed Command

```powershell
$py='C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$orig=(Get-ChildItem results\floor_prior_remote -File | Where-Object { $_.Name -like 'bedroom*floor_prior_max1.8_mesh_p2*.json' } | Select-Object -First 1 -ExpandProperty FullName)
& $py scripts\compare_common_layout_metrics.py `
  --original-json "$orig" `
  --qwen-full-dir results\respace_remote\qwen_full_bedroom_n10_20260709_235431\respace_qwen_bedroom_vllm_n10 `
  --qwen-add-dir results\respace_remote\qwen_addonly_bedroom_n10_20260710_041303\respace_qwen_addonly_bedroom_n10 `
  --out-csv results\tables\common_layout_metrics_20260710.csv `
  --out-json results\tables\common_layout_metrics_20260710.json
```

## Key Metrics

| Method | Scenes | Non-empty | Avg objects | Overlap pairs / scene | Footprint overlap ratio | OOB center rate |
|---|---:|---:|---:|---:|---:|---:|
| Original baseline layout | 162 | 1.000 | 5.346 | 0.907 | 0.0461 | 0.000 |
| Original repaired floor-prior | 162 | 1.000 | 5.346 | 0.926 | 0.0439 | 0.000 |
| Qwen/ReSpace full-scene | 30 | 1.000 | 4.700 | 2.000 | 0.0505 | 0.000 |
| Qwen/ReSpace add-only | 30 | 1.000 | 3.567 | 0.967 | 0.0350 | 0.000 |

## Interpretation

1. All compared outputs are non-empty and in-bounds under this evaluator.
2. The original floor-prior repair slightly reduces footprint overlap ratio compared with its own baseline: `0.0461 -> 0.0439`.
3. Qwen/ReSpace full-scene has fewer objects on average than the original bedroom set, but more overlap pairs per scene: `2.000` versus about `0.91`.
4. Qwen/ReSpace add-only has the lowest overlap ratio in this table, but it also has the fewest objects on average, so this should be interpreted as a sparse add-only layout check rather than a stronger semantic result.
5. These geometric results do not contradict the original relation-accuracy gain. They measure a different property: layout compactness/collision tendency, not target relation satisfaction.

## Current Comparison Status

| Question | Current answer |
|---|---|
| Can Qwen/ReSpace run without gated Llama? | Yes. |
| Can Qwen/ReSpace produce non-empty bedroom scenes? | Yes: full-scene 30/30, add-only 10/10. |
| Is Qwen/ReSpace stable on strict sequential editing? | Partly. Completed seed 1234 had `acc_seq=0.6042`; long removal retry made full run inefficient. |
| Does original floor-prior still have relation-accuracy evidence? | Yes: previous 1062-scene table shows average relation-accuracy gain about 0.119. |
| Do we now have a same-machine comparison? | Yes for geometry/layout metrics; no for target semantic relation accuracy. |

## Still Unreliable

1. ReSpace full-scene and add-only samples are still smaller than the original 162-scene bedroom floor-prior set.
2. The common evaluator uses geometry/layout metrics, not target relation labels.
3. The ReSpace logs still show `raw_model.glb` path warnings, so mesh-level metrics remain less reliable than box-level footprint metrics.
4. Claude Code was asked to perform the work using `ssh autodl-current`, but it stayed silent and did not create remote tmux sessions or artifacts. I stopped it and completed the evaluator directly.

## Next Experiment

For the final paper-quality claim, build a relation-target adapter:

1. Save or reconstruct the exact ReSpace prompts/commands for each generated scene.
2. Parse target relations from those prompts where relation language exists.
3. Score both original outputs and ReSpace outputs with the same target-relation evaluator.
4. Keep this common layout-metric table as a safety/quality table, not the main semantic comparison.

## Upload Recommendation

Upload:

```text
scripts/compare_common_layout_metrics.py
results/tables/common_layout_metrics_20260710.csv
results/tables/common_layout_metrics_20260710.json
docs/common_layout_comparison_20260710.md
visual/common_layout_comparison_20260710.html
results/respace_remote/qwen_full_bedroom_n10_20260709_235431/
results/respace_remote/qwen_addonly_bedroom_n10_multiseed_20260710_045939/
server_setup/run_respace_qwen_addonly_bedroom_n10_multiseed.sh
```

Do not upload credentials, tokens, raw datasets, or model weights.
