#!/usr/bin/env bash
set -euo pipefail
LOG=/root/RelationAwareInstructScene/logs/respace_smoke_vllm_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export PYTHONPATH=.
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
mkdir -p /root/autodl-tmp/RelationAwareInstructScene/respace_outputs/smoke_bedroom_vllm
python src/pipeline.py \
  --env .env.baseline \
  --pth-output /root/autodl-tmp/RelationAwareInstructScene/respace_outputs/smoke_bedroom_vllm \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 1 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --icl-k 1 \
  --bon-llm 1
python - <<'PY'
from pathlib import Path
root=Path('/root/autodl-tmp/RelationAwareInstructScene/respace_outputs/smoke_bedroom_vllm')
print('OUTPUT_ROOT', root)
for p in sorted(root.rglob('*'))[:120]:
    if p.is_file():
        print('OUT_FILE', p, p.stat().st_size)
PY
echo "PASS respace smoke vllm completed"
echo "$LOG"
