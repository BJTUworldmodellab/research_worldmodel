# CommonScenes Baseline Environment Audit - 2026-07-10

## Verdict

`ymxlzgy/commonscenes` is a usable CommonScenes resource. It is the official NeurIPS 2023 implementation and includes:

- `v2_box`: the CommonScenes layout branch.
- `v2_full`: the full layout + shape branch.
- `scripts/eval_3dfront.py`: evaluation entry point.
- SG-FRONT download instructions.
- Public checkpoint and dataset links.

The main blocker is not GPU memory. The real risks are dependency setup, checkpoint disk space, and adapting SG-FRONT/CommonScenes inputs to our relation-aware evaluator.

## Remote Environment

| Item | Status |
|---|---|
| GPU | NVIDIA A100-PCIE-40GB |
| GPU memory | 40GB, currently idle |
| Driver / CUDA | Driver 590.48.01, CUDA 13.1 |
| Existing PyTorch env | `respace`: PyTorch 2.5.1+cu121, CUDA available |
| CPU RAM | 629GB, enough |
| System disk | 30GB, about 18GB free |
| Data disk | 120GB, about 29-30GB free during download |
| Existing raw data | `/root/autodl-tmp/RelationAwareInstructScene/raw_data/3D-FRONT`, about 55GB |
| Existing InstructScene data | `/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene`, about 6.7GB |
| CommonScenes repo | `/root/RelationAwareInstructScene/repos/commonscenes` |

## Download And Extraction Status

Assets were downloaded by:

```text
tmux session: commonscenes_assets
script: /root/RelationAwareInstructScene/server_setup/download_commonscenes_assets.sh
log: /root/RelationAwareInstructScene/logs/commonscenes/download_assets_20260710_150148.log
asset dir: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_assets
```

| Asset | Size | Status |
|---|---:|---|
| `SG_FRONT.zip` | 3.3MB | downloaded |
| `bbox.zip` | 12MB | downloaded |
| `vqvae_threedfront_best.pth` | 101MB | downloaded |
| `balancing.zip` | 9.95GB | downloaded |

The `balancing.zip` URL is accessible. To save disk, only the required evaluation checkpoints were extracted:

```text
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/checkpoint/model180.pth
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/checkpoint/model_stats_180.pkl
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/checkpoint/model195.pth
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/checkpoint/model_stats_195.pkl
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/args.json
```

A layout-only evaluation copy was created at:

```text
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all
```

The checkpoint is unchanged. The copied `args.json` disables `with_SDF` so the official evaluation can run without the missing `3D-FUTURE-SDF` shape grids.

## Dependency Status

The existing `respace` environment already has:

```text
numpy, scipy, yaml, torch, trimesh, cv2, pyrender, einops, clip
```

Installed into the existing `respace` environment:

```text
omegaconf, fvcore, h5py, PyMCubes, tensorboardx, termcolor, ftfy, regex, seaborn, imageio, scikit-image
```

CommonScenes README recommends Python 3.8, PyTorch 1.11.0, CUDA 11.3, and Pytorch3D. Our existing `respace` environment is Python 3.9 and PyTorch 2.5.1+cu121. For layout-only evaluation, lightweight local compatibility stubs were used for Open3D/PyTorch3D/Chamfer rendering imports:

```text
/root/RelationAwareInstructScene/server_setup/commonscenes_compat_layout_only
```

This is acceptable for `--visualize False --gen_shape False`, but it is not a full shape/rendering reproduction.

## Data Compatibility

The remote already has InstructScene-style processed bedroom data:

```text
/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene/threed_front_bedroom
/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene/threed_front.pkl
/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene/threed_front_bedroom/dataset_stats.txt
```

CommonScenes expects an ATISS-style `FRONT` directory containing:

```text
3D-FRONT
3D-FRONT_preprocessed
threed_front.pkl
3D-FRONT-texture
3D-FUTURE-model
3D-FUTURE-scene
3D-FUTURE-SDF
SG-FRONT json/txt files
bbox json/txt files
```

For layout-only `v2_box` evaluation, we should try to avoid the full SDF/shape branch and reuse existing InstructScene/ATISS-like processed data where possible.

Prepared CommonScenes data root:

```text
/root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT
```

It contains SG-FRONT and bbox metadata plus symlinks to existing 3D-FRONT and `threed_front.pkl`.

Dataset smoke test passed:

```text
log: /root/RelationAwareInstructScene/logs/commonscenes/dataset_smoke_20260710_1552.log
len: 162 bedroom val scenes
vocab objects: 23
vocab predicates: 16
```

## Need To Change GPU?

No. Keep A100 40GB.

| Task | A100 40GB |
|---|---:|
| Download/check resources | enough |
| Layout-only `v2_box` smoke test | enough |
| 20-100 bedroom scene baseline | enough |
| 162 bedroom scene baseline | likely enough |
| 370 all-room CommonScenes official eval | enough |
| Full retraining | not recommended |

## Need To Expand Disk?

For smoke tests, current disk is probably enough.

For a full clean reproduction, expand the data disk to at least:

```text
200GB, preferably 300GB
```

Reason: the existing raw 3D-FRONT data already uses about 55GB, and `balancing.zip` alone is about 9.95GB before extraction.

## Completed Evaluation

Official CommonScenes layout-only generation evaluation now runs.

Bedroom command:

```text
source /root/miniconda3/bin/activate respace
cd /root/RelationAwareInstructScene/repos/commonscenes/scripts
PYTHONPATH=/root/RelationAwareInstructScene/server_setup/commonscenes_compat_layout_only:/root/RelationAwareInstructScene/repos/commonscenes \
python eval_3dfront.py \
  --dataset /root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT \
  --exp /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all \
  --epoch 180 \
  --visualize False \
  --evaluate_diversity False \
  --num_samples 1 \
  --gen_shape False \
  --no_stool True \
  --room_type bedroom
```

Bedroom result:

```text
log: /root/RelationAwareInstructScene/logs/commonscenes/eval_bedroom_epoch180_layoutonly4_20260710_1635.log
scenes: 162
L/R: 0.99
F/B: 0.99
Bi/Sm: 0.97
Ta/Sh: 0.98
Stand: 1.00
Close: 0.83
Symm: 0.47
Total: 0.97
means of mean: 0.89
```

Epoch 195 was also reproduced on 2026-07-13:

```text
bedroom log: /root/RelationAwareInstructScene/logs/commonscenes/export_bedroom_epoch195_layoutonly_20260713_1443.log
bedroom boxes: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_bedroom_epoch195.json
bedroom official total: 0.97
bedroom means of mean: 0.90

all-room log: /root/RelationAwareInstructScene/logs/commonscenes/export_all_epoch195_layoutonly_20260713_1443.log
all-room boxes: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_all_epoch195.json
all-room official total: 0.96
all-room means of mean: 0.89
```

All-room result:

```text
log: /root/RelationAwareInstructScene/logs/commonscenes/eval_all_epoch180_layoutonly_probe_20260710_1656.log
scenes: 370
L/R: 0.98
F/B: 1.00
Bi/Sm: 0.97
Ta/Sh: 0.95
Stand: 0.99
Close: 0.77
Symm: 0.60
Total: 0.96
means of mean: 0.89
```

Prediction exports were produced with a copied, patched script:

```text
script: /root/RelationAwareInstructScene/repos/commonscenes/scripts/eval_3dfront_export_boxes.py
local patch helper: server_setup/patch_commonscenes_export_boxes.py
bedroom export log: /root/RelationAwareInstructScene/logs/commonscenes/export_bedroom_epoch180_layoutonly_final_20260710_1710.log
all-room export log: /root/RelationAwareInstructScene/logs/commonscenes/export_all_epoch180_layoutonly_20260710_1702.log
bedroom boxes: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_bedroom_epoch180.json
all-room boxes: /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_all_epoch180.json
```

Note: `boxes_large.json` is overwritten by each export run. Use the stable copied files above for downstream evaluation.

Single `--room_type livingroom` failed with an object embedding size mismatch:

```text
log: /root/RelationAwareInstructScene/logs/commonscenes/export_livingroom_epoch180_layoutonly_20260710_1650.log
checkpoint object embedding: 15 classes
livingroom dataset object embedding: 13 classes
```

Therefore this checkpoint should currently be reported as validated for `room_type all` and `room_type bedroom`, not for independently sliced livingroom/diningroom evaluation.

## Next Steps

1. Convert `boxes_all_epoch180.json` and `boxes_bedroom_epoch180.json` to the relation-aware evaluator format.
2. Run the same relation/overlap evaluator on CommonScenes predictions and on our method's saved predictions.
3. Only then put CommonScenes into the main comparison table.
4. Keep official CommonScenes metrics in a separate table because they are not the same metric as our selected-relation protocol.

## Baseline Positioning

CommonScenes is a valid external strong baseline because it is scene-graph conditioned. It is much more defensible than direct Qwen/ReSpace comparison, which had a task mismatch.

The current result is not yet a final fair-comparison result. It proves the external baseline is runnable and gives official CommonScenes constraint metrics. The fair paper-facing comparison still requires converting exported predictions into the same evaluator used for Relation-Aware InstructScene.

The final paper table should still separate:

```text
internal fair baselines: original layout, rule-based repair, no-floor-prior optimizer, floor-prior repair
external model baseline: CommonScenes v2_box layout branch
```
