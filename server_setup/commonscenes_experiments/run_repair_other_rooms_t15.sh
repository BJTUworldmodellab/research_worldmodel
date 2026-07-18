#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/bin/activate respace
cd /root/RelationAwareInstructScene

layout=/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing_layoutonly/all/results/boxes_all_epoch195.json
sub=/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/room_subsets
out=/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair
log=/root/RelationAwareInstructScene/logs/commonscenes
mkdir -p "$log"

python /root/RelationAwareInstructScene/scripts/repair_commonscenes_fullshape_pt_generic_gate.py \
  --pt-dir "$sub/livingroom_pt_epoch195" \
  --layout-json "$layout" \
  --out-dir "$out/fullshape_pt_epoch195_generic_gate_t1.5_livingroom" \
  --max-move 1.5 \
  --passes 2 \
  > "$log/repair_generic_gate_t1.5_livingroom_20260713.log" 2>&1

python /root/RelationAwareInstructScene/scripts/repair_commonscenes_fullshape_pt_generic_gate.py \
  --pt-dir "$sub/diningroom_pt_epoch195" \
  --layout-json "$layout" \
  --out-dir "$out/fullshape_pt_epoch195_generic_gate_t1.5_diningroom" \
  --max-move 1.5 \
  --passes 2 \
  > "$log/repair_generic_gate_t1.5_diningroom_20260713.log" 2>&1

python /root/RelationAwareInstructScene/scripts/repair_commonscenes_fullshape_pt_generic_gate.py \
  --pt-dir "$sub/library_pt_epoch195" \
  --layout-json "$layout" \
  --out-dir "$out/fullshape_pt_epoch195_generic_gate_t1.5_library" \
  --max-move 1.5 \
  --passes 2 \
  > "$log/repair_generic_gate_t1.5_library_20260713.log" 2>&1
