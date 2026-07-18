#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/bin/activate respace
export LD_LIBRARY_PATH=/root/miniconda3/envs/respace/lib/python3.9/site-packages/torch/lib:/usr/local/cuda/lib64

cd /root/RelationAwareInstructScene/repos/commonscenes/scripts

for room in livingroom diningroom library; do
  echo "START ${room} $(date)"
  PYTHONPATH=/root/RelationAwareInstructScene/repos/commonscenes \
  python eval_3dfront_export_fullshape_pt.py \
    --dataset /root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT \
    --exp /root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all \
    --epoch 195 \
    --visualize False \
    --evaluate_diversity False \
    --num_samples 1 \
    --gen_shape True \
    --export_3d True \
    --no_stool True \
    --room_type "${room}" \
    > "/root/RelationAwareInstructScene/logs/commonscenes/eval_${room}_epoch195_export_fullshape_pt_20260713.log" 2>&1
  echo "DONE ${room} $(date)"
done
