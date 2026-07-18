#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/InstructScene
STAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR"
LOG=$LOGDIR/reproduce_minimal_v100_${STAMP}.log
exec > >(tee "$LOG") 2>&1

source "$ROOT/activate_relation_scene.sh"
cd "$REPO"

echo "[repro] start $(date)"
echo "[repro] repo=$REPO"
echo "[repro] log=$LOG"
echo "[repro] disk"
df -h / /root/autodl-tmp

echo "[repro] gpu"
nvidia-smi

echo "[repro] torch cuda check"
python - <<'PY'
import torch
print('torch', torch.__version__)
print('cuda_available', torch.cuda.is_available())
print('device_count', torch.cuda.device_count())
assert torch.cuda.is_available(), 'CUDA is not available'
print('device_name', torch.cuda.get_device_name(0))
x = torch.randn(1024, 1024, device='cuda')
y = x @ x
print('cuda_matmul_ok', tuple(y.shape), float(y[0, 0].detach().cpu()))
PY

echo "[repro] light smoke"
"$ROOT/server_setup/smoke_test_light.sh"

echo "[repro] relation-aware bedroom parsed minimal run"
SUFFIX="v100_repro_${STAMP}"
python src/relation_aware_generate_sg.py configs/bedroom_sg_diffusion_vq_objfeat.yaml \
  --tag bedroom_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae \
  --sg2sc_tag bedroom_sg2scdiffusion_objfeat \
  --checkpoint_epoch 1999 \
  --sg2sc_epoch 1999 \
  --n_scenes 16 \
  --device 0 \
  --relation_source parsed \
  --repair_passes 2 \
  --close_distance 0.75 \
  --far_distance 1.6 \
  --repair_strategy direct \
  --output_suffix "$SUFFIX" \
  --skip_object_matching

RESULT_DIR="$REPO/out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999"
RESULT_JSON=$(ls -t "$RESULT_DIR"/*${SUFFIX}*_eval_cfg1.0_1.0.json | head -n 1)
RESULT_TXT=$(ls -t "$RESULT_DIR"/*${SUFFIX}*_eval_cfg1.0_1.0.txt | head -n 1)

echo "[repro] result_json=$RESULT_JSON"
echo "[repro] result_txt=$RESULT_TXT"

echo "[repro] metrics summary"
python - "$RESULT_JSON" <<'PY'
import json, sys
p = sys.argv[1]
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)
scores = data.get('scores', data)
keys = [
    'graph_relation_acc', 'layout_relation_acc', 'repair_relation_acc',
    'layout_relation_acc_easy', 'repair_relation_acc_easy',
    'repair_edits', 'repair_skipped', 'avg_repair_movement',
    'layout_overlap_ratio', 'repair_overlap_ratio',
    'layout_overlap_pairs_per_scene', 'repair_overlap_pairs_per_scene',
    'layout_out_of_bounds_center_rate', 'repair_out_of_bounds_center_rate',
    'mesh_collision_scenes_evaluated'
]
print('file', p)
for k in keys:
    if k in scores:
        print(f'{k}={scores[k]}')
print('per_scene_count', len(data.get('per_scene', [])))
if 'layout_relation_acc' in scores and 'repair_relation_acc' in scores:
    print('repair_gain=', scores['repair_relation_acc'] - scores['layout_relation_acc'])
PY

echo "[repro] PASS minimal V100 reproduction completed"
echo "[repro] log=$LOG"
