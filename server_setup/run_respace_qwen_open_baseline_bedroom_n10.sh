#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/respace
LOG=$ROOT/logs/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_$TS.log
OUT=$ROOT/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_$TS
SCENES=$OUT/respace_qwen_bedroom_vllm_n10
mkdir -p "$SCENES/1234" "$SCENES/3456" "$SCENES/5678" "$(dirname "$LOG")"
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
printf 'ROOM=bedroom N_TEST_SCENES=10 SEEDS=1234,3456,5678\n'
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader
set +e
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$SCENES" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 10 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --do-icl-for-prompt \
  --do-class-labels-for-prompt \
  --do-prop-sampling-for-prompt \
  --icl-k 2 \
  --bon-llm 1
RC=$?
set -e
printf 'QWEN_N10_RC=%s\n' "$RC"
printf 'OUTPUT_COUNTS\n'
find "$SCENES" -mindepth 2 -maxdepth 2 -type f -name '*.json' -printf '%h\n' | sort | uniq -c
find "$OUT" -maxdepth 8 -type f -printf '%p %s\n' | sort | head -n 300
printf '{"timestamp":"%s","open_baseline_model":"%s","room":"bedroom","n_test_scenes":10,"seeds":[1234,3456,5678],"rc":%s,"log":"%s","out":"%s","scenes":"%s"}\n' "$TS" "$RESPACE_VANILLA_MODEL_ID" "$RC" "$LOG" "$OUT" "$SCENES" > "$OUT/summary.json"
printf 'SUMMARY %s/summary.json\n' "$OUT"
exit "$RC"
