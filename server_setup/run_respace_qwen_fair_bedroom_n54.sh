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
OUT=/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_fair_bedroom_n54_${TS}
LOG=/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_fair_bedroom_n54_${TS}.log
FULL_OUT="$OUT/full_scene"
ADD_OUT="$OUT/add_only"
mkdir -p "$(dirname "$LOG")"
for seed in 1234 3456 5678; do
  mkdir -p "$FULL_OUT/$seed" "$ADD_OUT/$seed"
done

exec > >(tee -a "$LOG") 2>&1

echo "START=$(date -Is)"
echo "HOST=$(hostname)"
echo "OUT=$OUT"
echo "LOG=$LOG"
echo "RESPACE_VANILLA_MODEL_ID=$RESPACE_VANILLA_MODEL_ID"
nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv,noheader || true

python -m py_compile src/respace.py src/utils.py src/pipeline.py
COMPILE_RC=$?
echo "COMPILE_RC=$COMPILE_RC"

echo "RUN_MODE=full_scene"
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$FULL_OUT" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 54 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --do-icl-for-prompt \
  --do-class-labels-for-prompt \
  --do-prop-sampling-for-prompt \
  --icl-k 2 \
  --bon-llm 1
FULL_RC=$?
echo "FULL_RC=$FULL_RC"

echo "RUN_MODE=add_only"
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$ADD_OUT" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 54 \
  --use-gpu \
  --use-vllm \
  --do-bedroom-testset \
  --do-icl-for-prompt \
  --do-class-labels-for-prompt \
  --do-prop-sampling-for-prompt \
  --icl-k 2 \
  --bon-llm 1
ADD_RC=$?
echo "ADD_RC=$ADD_RC"

export OUT FULL_OUT ADD_OUT LOG COMPILE_RC FULL_RC ADD_RC
python3 - <<'PY'
import json
import os
import pathlib
import statistics


def summarize(mode, root):
    root = pathlib.Path(root)
    rows = []
    for path in sorted(root.rglob("*.json")):
        row = {"path": str(path), "seed": path.parent.name}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            objects = data.get("objects") or []
            row.update({"ok": bool(objects), "objects": len(objects), "error": None})
        except Exception as exc:
            row.update({"ok": False, "objects": None, "error": str(exc)})
        rows.append(row)
    counts = [r["objects"] for r in rows if isinstance(r["objects"], int)]
    by_seed = {}
    for row in rows:
        by_seed.setdefault(row["seed"], []).append(row)
    return {
        "mode": mode,
        "root": str(root),
        "total_json": len(rows),
        "nonempty": sum(1 for r in rows if r["ok"]),
        "empty": sum(1 for r in rows if not r["ok"]),
        "avg_objects": statistics.mean(counts) if counts else None,
        "min_objects": min(counts) if counts else None,
        "max_objects": max(counts) if counts else None,
        "by_seed": {
            seed: {
                "json": len(seed_rows),
                "nonempty": sum(1 for r in seed_rows if r["ok"]),
                "objects": [r["objects"] for r in seed_rows],
            }
            for seed, seed_rows in sorted(by_seed.items())
        },
        "rows": rows,
    }


summary = {
    "out": os.environ["OUT"],
    "log": os.environ["LOG"],
    "compile_rc": int(os.environ.get("COMPILE_RC", "999")),
    "full_rc": int(os.environ.get("FULL_RC", "999")),
    "add_rc": int(os.environ.get("ADD_RC", "999")),
    "full_scene": summarize("full_scene", os.environ["FULL_OUT"]),
    "add_only": summarize("add_only", os.environ["ADD_OUT"]),
}
summary_path = pathlib.Path(os.environ["OUT"]) / "summary_verified.json"
summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print(f"SUMMARY={summary_path}")
PY
SUMMARY_RC=$?
echo "SUMMARY_RC=$SUMMARY_RC"
echo "END=$(date -Is)"

TOTAL_JSON=$(find "$OUT" -type f -name '*.json' | wc -l)
if [ "$TOTAL_JSON" -gt 1 ]; then
  exit 0
fi
exit 2
