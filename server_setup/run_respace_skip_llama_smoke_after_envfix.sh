#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/respace
LOG=$ROOT/logs/strong_baseline_a100_compare/skip_llama_smoke_envfix_$TS.log
OUT=$ROOT/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_$TS
mkdir -p "$OUT" "$(dirname "$LOG")"
mkdir -p "$OUT/respace_smoke_bedroom_vllm/1234" "$OUT/respace_smoke_bedroom_vllm/3456" "$OUT/respace_smoke_bedroom_vllm/5678"
exec > >(tee -a "$LOG") 2>&1
cd "$REPO"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export PYTHONPATH=.
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export RESPACE_SKIP_GATED_LLAMA=1
printf 'START %s\n' "$(date -Is)"
printf 'ENV_FIX %s\n' "$(grep '^PTH_STAGE_2_DEDUP=' .env.baseline)"
ls -lh data/metadata/model_info_3dfuture_assets_embeds.pickle
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader
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
find "$OUT" -maxdepth 8 -type f -printf '%p %s\n' | sort | head -n 300
printf '{"timestamp":"%s","env_fix":true,"asset_cache_rebuilt":true,"unofficial_skip_llama":true,"smoke_rc":%s,"log":"%s","out":"%s"}\n' "$TS" "$RC" "$LOG" "$OUT" > "$OUT/summary.json"
printf 'SUMMARY %s/summary.json\n' "$OUT"
exit "$RC"
