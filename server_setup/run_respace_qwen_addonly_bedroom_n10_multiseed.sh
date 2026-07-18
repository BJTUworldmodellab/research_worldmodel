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
OUT=/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_multiseed_${TS}
LOG=/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_multiseed_${TS}.log
mkdir -p "$OUT/respace_qwen_addonly_bedroom_n10_multiseed/1234" \
         "$OUT/respace_qwen_addonly_bedroom_n10_multiseed/3456" \
         "$OUT/respace_qwen_addonly_bedroom_n10_multiseed/5678"

{
  echo "TS=$TS"
  echo "OUT=$OUT"
  echo "LOG=$LOG"
  echo "RESPACE_VANILLA_MODEL_ID=$RESPACE_VANILLA_MODEL_ID"
  python -m py_compile src/respace.py src/utils.py src/pipeline.py
  python src/pipeline.py \
    --env .env.baseline \
    --pth-output "$OUT/respace_qwen_addonly_bedroom_n10_multiseed" \
    --room-type bedroom \
    --model-id gradient-spaces/respace-sg-llm-1.5b \
    --n-test-scenes 10 \
    --use-gpu \
    --use-vllm \
    --do-bedroom-testset \
    --do-icl-for-prompt \
    --do-class-labels-for-prompt \
    --do-prop-sampling-for-prompt \
    --icl-k 2 \
    --bon-llm 1
  RC=$?
  echo "QWEN_ADDONLY_MULTI_RC=$RC"
  python3 - <<PY
import json, pathlib, statistics
out=pathlib.Path("$OUT/respace_qwen_addonly_bedroom_n10_multiseed")
rows=[]
for p in sorted(out.glob("*/*.json")):
    try:
        data=json.loads(p.read_text())
    except Exception as exc:
        rows.append({"path":str(p),"seed":p.parent.name,"ok":False,"error":str(exc),"objects":None})
        continue
    objs=data.get("objects") or []
    rows.append({"path":str(p),"seed":p.parent.name,"ok":bool(objs),"objects":len(objs)})
by_seed={}
for r in rows:
    by_seed.setdefault(r["seed"], []).append(r)
summary={
    "out":str(out),
    "total_json":len(rows),
    "nonempty":sum(1 for r in rows if r["ok"]),
    "empty":sum(1 for r in rows if not r["ok"]),
    "avg_objects_nonempty":statistics.mean([r["objects"] for r in rows if r["ok"]]) if any(r["ok"] for r in rows) else None,
    "by_seed":{seed:{"json":len(v),"nonempty":sum(1 for r in v if r["ok"]),"objects":[r["objects"] for r in v]} for seed,v in sorted(by_seed.items())},
    "rows":rows,
}
(out.parent/"summary_verified.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
print(json.dumps(summary,indent=2))
PY
  exit $RC
} 2>&1 | tee "$LOG"
