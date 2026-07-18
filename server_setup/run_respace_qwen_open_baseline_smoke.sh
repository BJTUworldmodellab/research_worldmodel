#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/respace
LOG=$ROOT/logs/strong_baseline_a100_compare/qwen_open_baseline_smoke_$TS.log
OUT=$ROOT/results/strong_baseline_a100_compare/qwen_open_baseline_smoke_$TS
mkdir -p "$OUT/respace_qwen_bedroom_vllm/1234" "$OUT/respace_qwen_bedroom_vllm/3456" "$OUT/respace_qwen_bedroom_vllm/5678" "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
cd "$REPO"
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export PYTHONPATH=.
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export RESPACE_VANILLA_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
unset RESPACE_SKIP_GATED_LLAMA || true
printf 'START %s\n' "$(date -Is)"
printf 'OPEN_BASELINE_MODEL=%s\n' "$RESPACE_VANILLA_MODEL_ID"
printf 'ENV_STAGE2 %s\n' "$(grep '^PTH_STAGE_2_DEDUP=' .env.baseline || true)"
ls -lh data/metadata/model_info_3dfuture_assets_embeds.pickle
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader
set +e
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_qwen_bedroom_vllm" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 1 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --icl-k 1 \
  --bon-llm 1 \
  --seed-only 1234
RC=$?
set -e
printf 'QWEN_SMOKE_RC=%s\n' "$RC"
find "$OUT" -maxdepth 8 -type f -printf '%p %s\n' | sort | head -n 300
printf '{"timestamp":"%s","open_baseline_model":"%s","rc":%s,"log":"%s","out":"%s"}\n' "$TS" "$RESPACE_VANILLA_MODEL_ID" "$RC" "$LOG" "$OUT" > "$OUT/summary.json"
printf 'SUMMARY %s/summary.json\n' "$OUT"
exit "$RC"
