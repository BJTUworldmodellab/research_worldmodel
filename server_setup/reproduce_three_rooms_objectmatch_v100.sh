#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/InstructScene
STAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR"
LOG=$LOGDIR/reproduce_three_rooms_objectmatch_v100_${STAMP}.log
exec > >(tee "$LOG") 2>&1
source "$ROOT/activate_relation_scene.sh"
cd "$REPO"
export INSTRUCTSCENE_NO_MESH_LOAD=1
run_room() {
  local room=$1
  local epoch=$2
  local sg2sc=1999
  local tag="${room}_sgdiffusion_vq_objfeat"
  local sg2sc_tag="${room}_sg2scdiffusion_objfeat"
  local suffix="v100_objectmatch_${STAMP}"
  echo "[room] start room=$room epoch=$epoch suffix=$suffix"
  python src/relation_aware_generate_sg.py configs/${room}_sg_diffusion_vq_objfeat.yaml \
    --tag "$tag" \
    --fvqvae_tag threedfront_objfeat_vqvae \
    --sg2sc_tag "$sg2sc_tag" \
    --checkpoint_epoch "$epoch" \
    --sg2sc_epoch "$sg2sc" \
    --n_scenes 0 \
    --device 0 \
    --relation_source parsed \
    --repair_passes 2 \
    --close_distance 0.75 \
    --far_distance 1.6 \
    --repair_strategy direct \
    --output_suffix "$suffix"
  local result_dir="$REPO/out/${tag}/generated_scenes/epoch_$(printf '%05d' $epoch)"
  local result_json=$(ls -t "$result_dir"/*${suffix}*_eval_cfg1.0_1.0.json | head -n 1)
  echo "[room] result_json=$result_json"
  python - "$room" "$result_json" <<'PY'
import json, sys
room,p=sys.argv[1],sys.argv[2]
d=json.load(open(p,encoding='utf-8'))
s=d.get('scores',d)
base=s['baseline_relation_acc']; rep=s['repaired_relation_acc']
print('SUMMARY', room, 'scenes', len(d.get('per_scene', [])), 'baseline', base, 'repair', rep, 'gain', rep-base, 'parser_recall', s.get('parser_relation_recall'), 'layout_overlap', s.get('layout_overlap_ratio'), 'repair_overlap', s.get('repair_overlap_ratio'))
PY
}
run_room bedroom 1999
run_room livingroom 1459
run_room diningroom 1239
echo "[three_rooms] PASS log=$LOG"
