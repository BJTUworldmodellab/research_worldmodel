#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/bin/activate respace
export LD_LIBRARY_PATH=/root/miniconda3/envs/respace/lib/python3.9/site-packages/torch/lib:/usr/local/cuda/lib64

cd /root/RelationAwareInstructScene/repos/commonscenes/scripts

echo "START all-room fullshape export $(date)"
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
  --room_type all \
  > /root/RelationAwareInstructScene/logs/commonscenes/eval_all_epoch195_export_fullshape_pt_20260713.log 2>&1
echo "DONE all-room fullshape export $(date)"
