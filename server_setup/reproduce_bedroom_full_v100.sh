#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/InstructScene
STAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR"
LOG=$LOGDIR/reproduce_bedroom_full_v100_${STAMP}.log
exec > >(tee "$LOG") 2>&1
source "$ROOT/activate_relation_scene.sh"
cd "$REPO"
SUFFIX="v100_full_${STAMP}"
echo "[full] start $(date) suffix=$SUFFIX"
python src/relation_aware_generate_sg.py configs/bedroom_sg_diffusion_vq_objfeat.yaml \
  --tag bedroom_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae \
  --sg2sc_tag bedroom_sg2scdiffusion_objfeat \
  --checkpoint_epoch 1999 \
  --sg2sc_epoch 1999 \
  --n_scenes 0 \
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
echo "[full] result_json=$RESULT_JSON"
echo "[full] result_txt=$RESULT_TXT"
python - "$RESULT_JSON" <<'PY'
import json, sys
p=sys.argv[1]
d=json.load(open(p, encoding='utf-8'))
s=d.get('scores', d)
print('per_scene_count', len(d.get('per_scene', [])))
for k,v in sorted(s.items()):
    if isinstance(v, (int,float)):
        print(f'{k}={v}')
PY
echo "[full] PASS"
echo "[full] log=$LOG"
