# CommonScenes Reproduction And Comparison - 2026-07-13

## Scope

This note records the most complete CommonScenes reproduction reached on the current AutoDL server, then compares it with the existing Relation-Aware InstructScene evidence.

Important: CommonScenes official constraint metrics and our selected-relation evaluator are not the same metric. They should not be merged into one leaderboard number until CommonScenes predictions are converted to our evaluator protocol.

## Remote Environment

```text
host: autodl-container-9ed51187fa-8d1ca17f
gpu: NVIDIA A100-PCIE-40GB, 40GB
env: conda respace, Python 3.9, PyTorch 2.5.1+cu121
data disk: /root/autodl-tmp, 170GB total, about 60GB free after extracting model195
```

The GPU and disk are sufficient for layout-only CommonScenes evaluation. Full shape/rendering reproduction is still incomplete because the run does not have the full `3D-FUTURE-SDF` shape-grid data or a full Open3D/PyTorch3D rendering stack.

## CommonScenes Assets

```text
repo: /root/RelationAwareInstructScene/repos/commonscenes
asset dir: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_assets
data root: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT
model root: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all
compat stubs: /root/RelationAwareInstructScene/server_setup/commonscenes_compat_layout_only
```

Downloaded/extracted assets:

```text
SG_FRONT.zip
bbox.zip
vqvae_threedfront_best.pth
balancing.zip
model180.pth + model_stats_180.pkl
model195.pth + model_stats_195.pkl
```

The layout-only experiment copy keeps the checkpoint unchanged but sets `with_SDF=false` in the copied `args.json` to avoid requiring missing SDF shape grids.

## Commands

The reproduced command pattern is:

```bash
source /root/miniconda3/bin/activate respace
cd /root/RelationAwareInstructScene/repos/commonscenes/scripts
PYTHONPATH=/root/RelationAwareInstructScene/server_setup/commonscenes_compat_layout_only:/root/RelationAwareInstructScene/repos/commonscenes \
python eval_3dfront_export_boxes.py \
  --dataset /root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT \
  --exp /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all \
  --epoch 195 \
  --visualize False \
  --evaluate_diversity False \
  --num_samples 1 \
  --gen_shape False \
  --no_stool True \
  --room_type all \
  --export_3d True
```

`eval_3dfront_export_boxes.py` is a copied version of the official script with one added export block. The metric path is otherwise the official CommonScenes evaluator.

## CommonScenes Official Results

| Split | Epoch | Scenes | L/R | F/B | Bi/Sm | Ta/Sh | Stand | Close | Symm | Total | Mean-of-means | Log | Export |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| bedroom | 180 | 162 | 0.99 | 0.99 | 0.97 | 0.98 | 1.00 | 0.83 | 0.47 | 0.97 | 0.89 | `/root/RelationAwareInstructScene/logs/commonscenes/eval_bedroom_epoch180_layoutonly4_20260710_1635.log` | `/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_bedroom_epoch180.json` |
| all-room | 180 | 370 | 0.98 | 1.00 | 0.97 | 0.95 | 0.99 | 0.77 | 0.60 | 0.96 | 0.89 | `/root/RelationAwareInstructScene/logs/commonscenes/eval_all_epoch180_layoutonly_probe_20260710_1656.log` | `/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_all_epoch180.json` |
| bedroom | 195 | 162 | 0.98 | 0.99 | 0.98 | 0.98 | 0.99 | 0.83 | 0.53 | 0.97 | 0.90 | `/root/RelationAwareInstructScene/logs/commonscenes/export_bedroom_epoch195_layoutonly_20260713_1443.log` | `/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_bedroom_epoch195.json` |
| all-room | 195 | 370 | 0.98 | 0.99 | 0.97 | 0.95 | 0.99 | 0.77 | 0.60 | 0.96 | 0.89 | `/root/RelationAwareInstructScene/logs/commonscenes/export_all_epoch195_layoutonly_20260713_1443.log` | `/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_all_epoch195.json` |

Observation: epoch180 and epoch195 are stable. The strongest CommonScenes layout-only official result is bedroom epoch195 by mean-of-means, but all checked checkpoints report the same total score at the first two decimals.

## Existing Relation-Aware InstructScene Results

These are from the existing InstructScene protocol and should be reported separately from the CommonScenes official table.

| Room | Scenes | Relations | Baseline layout acc | Direct relation-aware acc | Absolute gain |
|---|---:|---:|---:|---:|---:|
| Bedroom | 162 | 245 | 0.7388 | 0.8735 | +0.1347 |
| Living room | 192 | 294 | 0.5510 | 0.7415 | +0.1905 |
| Dining room | 177 | 269 | 0.5948 | 0.7844 | +0.1896 |

Collision-gated variant:

| Room | Baseline acc | Direct repair acc | Collision-gated acc | Gated gain | Baseline mesh pair rate | Gated mesh pair rate |
|---|---:|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | 0.8449 | +0.1061 | 0.070244 | 0.064878 |
| Living room | 0.5510 | 0.7415 | 0.6871 | +0.1361 | 0.031257 | 0.030540 |
| Dining room | 0.5948 | 0.7844 | 0.7212 | +0.1264 | 0.034229 | 0.033154 |

Source:

```text
/root/RelationAwareInstructScene/docs/relation_aware_instructscene_experiment_report.md
```

## Comparison Interpretation

CommonScenes is now a much better external baseline than the earlier Qwen/ReSpace attempts because it is scene-graph-conditioned and has an official indoor scene layout evaluator.

However, the current comparison is still not a same-protocol model-vs-model comparison:

- CommonScenes official metrics evaluate SG-FRONT relationship constraints on CommonScenes outputs.
- Relation-Aware InstructScene metrics evaluate selected explicit instruction relations on InstructScene outputs.
- CommonScenes has high official constraint satisfaction, but that does not directly answer whether it satisfies our selected instruction relations.
- Our method shows a clear within-protocol improvement over its own InstructScene baseline, but that is not the same as beating CommonScenes.

Paper-safe claim:

```text
CommonScenes was successfully reproduced as an external scene-graph-conditioned baseline under its official layout-only evaluation. Its official relation-constraint satisfaction is high and stable across epoch180 and epoch195. Our Relation-Aware InstructScene method should be compared against CommonScenes only after converting CommonScenes predictions into the same selected-relation evaluation protocol.
```

Unsafe claim:

```text
Do not claim that our method outperforms CommonScenes from the current numbers alone.
```

## Same-Output Repair Comparison

To make the comparison more meaningful, a post-hoc relation repair was applied directly to the exported CommonScenes epoch195 layouts. This uses the same CommonScenes triples and the same exported boxes before and after repair.

Script:

```text
local: server_setup/evaluate_commonscenes_repair.py
remote: /root/RelationAwareInstructScene/server_setup/evaluate_commonscenes_repair_v2.py
```

Outputs:

```text
/root/RelationAwareInstructScene/results/commonscenes_repair_compare_20260713/boxes_bedroom_epoch195_repair_v2_p2_summary.json
/root/RelationAwareInstructScene/results/commonscenes_repair_compare_20260713/boxes_bedroom_epoch195_repair_v2_gated_p2_summary.json
/root/RelationAwareInstructScene/results/commonscenes_repair_compare_20260713/boxes_all_epoch195_repair_v2_p2_summary.json
/root/RelationAwareInstructScene/results/commonscenes_repair_compare_20260713/boxes_all_epoch195_repair_v2_gated_p2_summary.json
```

The local evaluator is a lightweight reproduction of the CommonScenes relation rules over exported denormalized boxes. Its absolute numbers are close to, but not exactly the same as, the official script because it uses an AABB footprint proxy for overlap/close distance. It is valid for before-vs-after comparison on the same exported layouts, but the official table above remains the authoritative CommonScenes reproduction.

| Split | Scenes | CommonScenes exported layout | Direct repair | Gated repair | Accepted scenes | Rejected scenes |
|---|---:|---:|---:|---:|---:|---:|
| bedroom epoch195 | 162 | 0.9813 | 0.9828 | 0.9844 | 159 | 3 |
| all-room epoch195 | 370 | 0.9734 | 0.9726 | 0.9763 | 345 | 25 |

Predicate-level effects:

| Split | Variant | Left | Right | Front | Behind | Close by | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| bedroom | CommonScenes | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.8923 | 0.9813 |
| bedroom | direct repair | 0.9962 | 0.9982 | 0.9928 | 0.9926 | 0.9731 | 0.9828 |
| bedroom | gated repair | 1.0000 | 1.0000 | 0.9982 | 0.9982 | 0.9692 | 0.9844 |
| all-room | CommonScenes | 0.9994 | 0.9987 | 0.9990 | 0.9993 | 0.8731 | 0.9734 |
| all-room | direct repair | 0.9849 | 0.9900 | 0.9943 | 0.9927 | 0.9459 | 0.9726 |
| all-room | gated repair | 0.9974 | 0.9993 | 0.9986 | 0.9990 | 0.9427 | 0.9763 |

Interpretation:

- CommonScenes is already very strong under explicit relation constraints.
- Direct repair greatly improves `close by`, but can slightly damage already-satisfied left/right/front/behind constraints.
- Gated repair is the safer variant: it keeps most of the `close by` gain while improving total satisfaction on both bedroom and all-room.
- The gain is small in absolute terms because the baseline is already near saturation, but it is a fairer test of the repair idea than comparing unrelated metrics.

## Remaining Work For Fair Comparison

1. Replace the lightweight AABB proxy with a direct call into CommonScenes `helpers.metrics_3dfront.validate_constrains` for exact official-rule before-vs-after evaluation.
2. Build a taxonomy/predicate bridge from CommonScenes object labels and predicates to the InstructScene selected-relation evaluator.
3. Convert `boxes_bedroom_epoch195.json` and `boxes_all_epoch195.json` into the same per-scene structure used by `relation_aware_generate_sg.py`.
4. Run the exact same relation verifier on:
   - CommonScenes predictions,
   - original InstructScene layout,
   - Relation-Aware InstructScene direct repair,
   - Relation-Aware InstructScene collision-gated repair.
5. Report official CommonScenes metrics as supporting evidence, not as the main fairness table.

## Files To Upload

Recommended local additions/updates:

```text
docs/commonscenes_environment_audit_20260710.md
docs/commonscenes_reproduction_comparison_20260713.md
server_setup/patch_commonscenes_export_boxes.py
server_setup/evaluate_commonscenes_repair.py
server_setup/commonscenes_compat_layout_only/
server_setup/download_commonscenes_assets.sh
```

Recommended remote artifacts to preserve outside git or document as reproducibility paths:

```text
/root/RelationAwareInstructScene/logs/commonscenes/export_bedroom_epoch195_layoutonly_20260713_1443.log
/root/RelationAwareInstructScene/logs/commonscenes/export_all_epoch195_layoutonly_20260713_1443.log
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_bedroom_epoch195.json
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_all_epoch195.json
```
