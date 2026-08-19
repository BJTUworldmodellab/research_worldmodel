#!/usr/bin/env bash
set -uo pipefail
# FULL formal generation for one room (EG07 Phase 3, 20260814).
# Same checkpoint/seed/relation_source/repair_strategy/mesh_collision and frozen
# params as the passing smoke; only n_scenes switches 1 -> 0 (full post-filter).
# Usage: run_formal_room_20260814.sh <room> <vq_epoch>
ROOM="$1"; EPOCH="$2"
BASE=/root/autodl-tmp/relation_grounding
RT=$BASE/eg07_formal_20260813/runtime
RUN=$BASE/eg07_formal_20260813
SUFFIX="floor_prior_max1.8_mesh_p2_close0.75_far1.6"
LOG=$RUN/formal_${ROOM}_20260814.log

export NLTK_DATA=$BASE/cache/nltk_data
export PYTHONPATH=$RT
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

cd "$RT" || exit 1
echo "=== formal start room=$ROOM epoch=$EPOCH n_scenes=0 $(date '+%F %T') ===" > "$LOG"

/root/miniconda3/envs/instructscene_full/bin/python relation_aware_generate_sg.py \
  "configs/${ROOM}_sg_diffusion_vq_objfeat.yaml" \
  --tag "${ROOM}_sgdiffusion_vq_objfeat" \
  --fvqvae_tag threedfront_objfeat_vqvae --fvqvae_epoch 1999 \
  --sg2sc_tag "${ROOM}_sg2scdiffusion_objfeat" --sg2sc_epoch 1999 \
  --checkpoint_epoch "$EPOCH" \
  --n_scenes 0 --n_workers 0 --device 0 --seed 0 \
  --relation_source parsed \
  --repair_strategy floor_prior --repair_passes 2 \
  --max_repair_move 1.8 --repair_overlap_weight 1.0 \
  --close_distance 0.75 --far_distance 1.6 \
  --mesh_collision \
  --output_suffix "$SUFFIX" \
  --output_dir "$RT/out" >> "$LOG" 2>&1

RC=$?
echo "=== formal exit=$RC room=$ROOM $(date '+%F %T') ===" >> "$LOG"
exit $RC
