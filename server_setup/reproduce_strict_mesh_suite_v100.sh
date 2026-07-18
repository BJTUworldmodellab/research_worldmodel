#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/InstructScene
STAMP=$(date +%Y%m%d_%H%M%S)
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR"
LOG=$LOGDIR/reproduce_strict_mesh_suite_v100_${STAMP}.log
exec > >(tee "$LOG") 2>&1
source "$ROOT/activate_relation_scene.sh"
cd "$REPO"
ulimit -n 65535 || true
unset INSTRUCTSCENE_NO_MESH_LOAD
run_room() {
  local room=$1
  local epoch=$2
  local strategy=$3
  local maxmove=$4
  local suffix=$5
  local sg2sc=1999
  local tag="${room}_sgdiffusion_vq_objfeat"
  local sg2sc_tag="${room}_sg2scdiffusion_objfeat"
  local full_suffix="${suffix}_${STAMP}"
  echo "[room] start room=$room epoch=$epoch strategy=$strategy maxmove=$maxmove suffix=$full_suffix"
  python src/relation_aware_generate_sg.py configs/${room}_sg_diffusion_vq_objfeat.yaml \
    --tag "$tag" \
    --fvqvae_tag threedfront_objfeat_vqvae \
    --sg2sc_tag "$sg2sc_tag" \
    --checkpoint_epoch "$epoch" \
    --sg2sc_epoch "$sg2sc" \
    --n_scenes 0 \
    --n_workers 0 \
    --device 0 \
    --relation_source parsed \
    --repair_passes 2 \
    --close_distance 0.75 \
    --far_distance 1.6 \
    --repair_strategy "$strategy" \
    --max_repair_move "$maxmove" \
    --repair_overlap_weight 1.0 \
    --mesh_collision \
    --render_examples 4 \
    --output_suffix "$full_suffix"
  local result_dir="$REPO/out/${tag}/generated_scenes/epoch_$(printf '%05d' $epoch)"
  local result_json=$(ls -t "$result_dir"/*${full_suffix}*_eval_cfg1.0_1.0.json | head -n 1)
  echo "[room] result_json=$result_json"
  python - "$room" "$strategy" "$result_json" <<'PY'
import json, sys
room,strategy,p=sys.argv[1],sys.argv[2],sys.argv[3]
d=json.load(open(p,encoding='utf-8'))
s=d.get('scores',d)
base=s['baseline_relation_acc']; rep=s['repaired_relation_acc']
print('SUMMARY', strategy, room, 'scenes', len(d.get('per_scene', [])), 'baseline', base, 'repair', rep, 'gain', rep-base, 'avg_move', s.get('avg_repair_movement'), 'mesh_scenes', s.get('mesh_collision_scenes_evaluated'), 'base_mesh_pair', s.get('layout_mesh_collision_pair_rate'), 'repair_mesh_pair', s.get('repair_mesh_collision_pair_rate'), 'mesh_delta', s.get('repair_mesh_collision_pair_rate')-s.get('layout_mesh_collision_pair_rate'))
PY
}
for spec in "bedroom 1999" "livingroom 1459" "diningroom 1239"; do
  set -- $spec
  run_room "$1" "$2" direct 0 strict_direct_mesh_p2
  run_room "$1" "$2" floor_prior 1.8 strict_floorprior_max1p8_mesh_p2
done
echo "[strict_mesh_suite] PASS log=$LOG"
