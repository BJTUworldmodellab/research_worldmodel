#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/bin/activate respace
export PYOPENGL_PLATFORM=egl
export PYTHONPATH=/root/RelationAwareInstructScene/repos/commonscenes/scripts:/root/RelationAwareInstructScene/repos/commonscenes:${PYTHONPATH:-}
export LD_LIBRARY_PATH=/root/miniconda3/envs/respace/lib/python3.9/site-packages/torch/lib:/usr/local/cuda/lib64

cd /root/RelationAwareInstructScene/repos/commonscenes/scripts

sub=/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/room_subsets
root=/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair
renderer=/root/RelationAwareInstructScene/scripts/render_commonscenes_fullshape_pt_param.py
log=/root/RelationAwareInstructScene/logs/commonscenes
mkdir -p "$log"

for room in livingroom diningroom library; do
  python "$renderer" \
    --pt-dir "$sub/${room}_pt_epoch195" \
    --out-dir "$root/commonscenes_render_baseline_epoch195_${room}" \
    > "$log/render_baseline_epoch195_${room}_20260713.log" 2>&1

  python "$renderer" \
    --pt-dir "$root/fullshape_pt_epoch195_generic_gate_t1.5_${room}" \
    --out-dir "$root/commonscenes_render_ours_generic_gate_t1.5_epoch195_${room}" \
    > "$log/render_ours_generic_gate_t1.5_epoch195_${room}_20260713.log" 2>&1
done
