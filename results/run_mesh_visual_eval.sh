#!/usr/bin/env bash
set -euo pipefail

cd /root/RelationAwareInstructScene/repos/InstructScene
source /root/RelationAwareInstructScene/activate_relation_scene.sh
ulimit -n 65535 || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export OMP_NUM_THREADS=1

run_room() {
  local room="$1"
  local config="$2"
  local tag="$3"
  local sg2sc_tag="$4"
  local epoch="$5"
  local sg2sc_epoch="$6"
  local log="/root/RelationAwareInstructScene/logs/${room}_mesh_visual_$(date +%Y%m%d_%H%M%S).log"
  echo "===== ${room} mesh+visual evaluation started $(date '+%F %T') =====" | tee -a "$log"
  python src/relation_aware_generate_sg.py "$config" \
    --tag "$tag" \
    --fvqvae_tag threedfront_objfeat_vqvae \
    --sg2sc_tag "$sg2sc_tag" \
    --checkpoint_epoch "$epoch" \
    --sg2sc_epoch "$sg2sc_epoch" \
    --n_scenes 0 \
    --n_workers 0 \
    --device 0 \
    --relation_source parsed \
    --repair_passes 2 \
    --close_distance 0.75 \
    --far_distance 1.6 \
    --mesh_collision \
    --render_examples 8 2>&1 | tee -a "$log"

  local save_dir="out/${tag}/generated_scenes/epoch_$(printf '%05d' "$epoch")"
  cp "${save_dir}/relation_aware_parsed_eval_cfg1.0_1.0.txt" \
    "${save_dir}/relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.txt"
  cp "${save_dir}/relation_aware_parsed_eval_cfg1.0_1.0.json" \
    "${save_dir}/relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.json"
  echo "===== ${room} mesh+visual evaluation finished $(date '+%F %T') =====" | tee -a "$log"
}

run_room bedroom \
  configs/bedroom_sg_diffusion_vq_objfeat.yaml \
  bedroom_sgdiffusion_vq_objfeat \
  bedroom_sg2scdiffusion_objfeat \
  1999 \
  1999

run_room livingroom \
  configs/livingroom_sg_diffusion_vq_objfeat.yaml \
  livingroom_sgdiffusion_vq_objfeat \
  livingroom_sg2scdiffusion_objfeat \
  1459 \
  1999

run_room diningroom \
  configs/diningroom_sg_diffusion_vq_objfeat.yaml \
  diningroom_sgdiffusion_vq_objfeat \
  diningroom_sg2scdiffusion_objfeat \
  1239 \
  1999
