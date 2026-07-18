#!/usr/bin/env bash
set -u

source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
cd /root/RelationAwareInstructScene/repos/respace

export PYTHONPATH=/root/RelationAwareInstructScene/repos/respace:${PYTHONPATH:-}
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export RESPACE_VANILLA_MODEL_ID=Qwen/Qwen2.5-7B-Instruct

TS=$(date +%Y%m%d_%H%M%S)
OUT=/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_seq_bedroom_n10_${TS}
LOG=/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_seq_bedroom_n10_${TS}.log
mkdir -p "$OUT"
mkdir -p "$OUT/respace_qwen_seq_bedroom_n10/1234" "$OUT/respace_qwen_seq_bedroom_n10/3456" "$OUT/respace_qwen_seq_bedroom_n10/5678"

{
  echo "TS=$TS"
  echo "OUT=$OUT"
  echo "LOG=$LOG"
  echo "RESPACE_VANILLA_MODEL_ID=$RESPACE_VANILLA_MODEL_ID"

  python -m py_compile src/respace.py src/utils.py src/pipeline.py

  python src/pipeline.py \
    --env .env.baseline \
    --pth-output "$OUT/respace_qwen_seq_bedroom_n10" \
    --room-type bedroom \
    --model-id gradient-spaces/respace-sg-llm-1.5b \
    --n-test-scenes 10 \
    --use-gpu \
    --use-vllm \
    --do-bedroom-testset \
    --do-seq-test \
    --do-icl-for-prompt \
    --do-class-labels-for-prompt \
    --do-prop-sampling-for-prompt \
    --icl-k 2 \
    --bon-llm 1
  RC=$?
  echo "QWEN_SEQ_RC=$RC"

  python3 - <<PY
import json, pathlib, statistics
out=pathlib.Path("$OUT/respace_qwen_seq_bedroom_n10")
metrics=[]
for p in sorted(out.glob("*_seq_metrics.json")):
    data=json.loads(p.read_text())
    for row in data:
        row=dict(row)
        row["_source"]=str(p)
        metrics.append(row)
summary={"out":str(out),"metric_files":len(list(out.glob("*_seq_metrics.json"))),"samples":len(metrics)}
for key in ["acc_seq","acc_add","acc_rem","n_steps","n_add_steps","n_rem_steps"]:
    vals=[m.get(key) for m in metrics if m.get(key) is not None]
    summary[key+"_mean"]=statistics.mean(vals) if vals else None
    summary[key+"_n"]=len(vals)
summary["first_samples"]=metrics[:3]
(out.parent/"summary_verified.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
PY

  exit $RC
} 2>&1 | tee "$LOG"
