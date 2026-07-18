#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/InstructScene
STAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR"
LOG=$LOGDIR/reproduce_bedroom_strict_v100_${STAMP}.log
exec > >(tee "$LOG") 2>&1
source "$ROOT/activate_relation_scene.sh"
cd "$REPO"
SUFFIX="v100_strict_${STAMP}"
echo "[strict] start $(date) suffix=$SUFFIX"
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
  --output_suffix "$SUFFIX"
RESULT_DIR="$REPO/out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999"
RESULT_JSON=$(ls -t "$RESULT_DIR"/*${SUFFIX}*_eval_cfg1.0_1.0.json | head -n 1)
echo "[strict] result_json=$RESULT_JSON"
python - "$RESULT_JSON" <<'PY'
import json, sys
p=sys.argv[1]
d=json.load(open(p, encoding='utf-8'))
s=d.get('scores', d)
keys=['graph_relation_acc','baseline_relation_acc','repaired_relation_acc','parser_relation_recall','parser_relation_precision','avg_repair_movement','layout_overlap_ratio','repair_overlap_ratio','layout_out_of_bounds_rate','repair_out_of_bounds_rate','mesh_collision_scenes_evaluated']
print('per_scene_count', len(d.get('per_scene', [])))
for k in keys:
    if k in s: print(f'{k}={s[k]}')
if 'baseline_relation_acc' in s and 'repaired_relation_acc' in s:
    print('gain=', s['repaired_relation_acc']-s['baseline_relation_acc'])
PY
echo "[strict] PASS log=$LOG"
