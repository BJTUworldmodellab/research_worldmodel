#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/respace
LOG=$ROOT/logs/strong_baseline_a100_compare/rebuild_asset_cache_and_smoke_$TS.log
OUT=$ROOT/results/strong_baseline_a100_compare/rebuild_asset_cache_and_smoke_$TS
mkdir -p "$OUT" "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
cd "$REPO"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export PYTHONPATH=.
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export HF_HUB_ENABLE_HF_TRANSFER=0
printf 'START %s\n' "$(date -Is)"
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader
printf 'DISK_BEFORE\n'; df -h /root /root/autodl-tmp || true
printf 'REBUILD_ASSET_CACHE_OFFICIAL_SCRIPT\n'
python ./src/preprocessing/3d-front/06_compute_embeds.py
printf 'CACHE_FILE\n'; ls -lh data/metadata/model_info_3dfuture_assets_embeds.pickle
printf 'SMOKE_UNOFFICIAL_SKIP_LLAMA\n'
export RESPACE_SKIP_GATED_LLAMA=1
set +e
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_smoke_bedroom_vllm" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 1 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --icl-k 1 \
  --bon-llm 1
RC=$?
set -e
printf 'SMOKE_RC=%s\n' "$RC"
printf 'OUTPUT_FILES\n'
find "$OUT" -maxdepth 6 -type f -printf '%p %s\n' | sort | head -n 300
printf '{"timestamp":"%s","asset_cache_rebuilt":true,"unofficial_skip_llama":true,"smoke_rc":%s,"log":"%s","out":"%s"}\n' "$TS" "$RC" "$LOG" "$OUT" > "$OUT/summary.json"
printf 'SUMMARY %s/summary.json\n' "$OUT"
exit "$RC"
