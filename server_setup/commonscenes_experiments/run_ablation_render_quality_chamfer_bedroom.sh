#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/bin/activate respace
export PYOPENGL_PLATFORM=egl
export PYTHONPATH=/root/RelationAwareInstructScene/repos/commonscenes/scripts:/root/RelationAwareInstructScene/repos/commonscenes:${PYTHONPATH:-}
export LD_LIBRARY_PATH=/root/miniconda3/envs/respace/lib/python3.9/site-packages/torch/lib:/usr/local/cuda/lib64

root=/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair
base_pt=/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195
base_png=/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom/png
base_glb=/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom/glb
renderer=/root/RelationAwareInstructScene/scripts/render_commonscenes_fullshape_pt_param.py
quality=/root/RelationAwareInstructScene/scripts/compare_commonscenes_outputs_quality.py
chamfer=/root/RelationAwareInstructScene/scripts/compute_commonscenes_glb_chamfer_param.py
log=/root/RelationAwareInstructScene/logs/commonscenes
mkdir -p "$log"

cd /root/RelationAwareInstructScene/repos/commonscenes/scripts

for t in 0.8 1.2; do
  ours_pt="$root/commonscenes_ours_generic_gate_t${t}_pt_epoch195_bedroom"
  ours_render="$root/commonscenes_render_ours_generic_gate_t${t}_epoch195_bedroom"
  quality_out="$root/commonscenes_ours_generic_gate_t${t}_compare_epoch195_bedroom"
  chamfer_out="$root/commonscenes_ours_generic_gate_t${t}_mesh_metrics_epoch195_bedroom"

  python "$renderer" \
    --pt-dir "$ours_pt" \
    --out-dir "$ours_render" \
    > "$log/render_ours_generic_gate_t${t}_epoch195_bedroom_20260714.log" 2>&1

  python "$quality" \
    --base-pt "$base_pt" \
    --ours-pt "$ours_pt" \
    --base-png "$base_png" \
    --ours-png "$ours_render/png" \
    --out-dir "$quality_out" \
    > "$log/quality_ours_generic_gate_t${t}_epoch195_bedroom_20260714.log" 2>&1

  python "$chamfer" \
    --base-glb "$base_glb" \
    --ours-glb "$ours_render/glb" \
    --out-dir "$chamfer_out" \
    > "$log/chamfer_ours_generic_gate_t${t}_epoch195_bedroom_20260714.log" 2>&1
done
