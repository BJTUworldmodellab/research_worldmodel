#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
ROOT=/root/RelationAwareInstructScene
OUT=$ROOT/results/strong_baseline_a100_compare/$TS
LOG=$ROOT/logs/strong_baseline_a100_compare/audit_$TS.log
mkdir -p "$OUT" "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1

echo "AUDIT_TS=$TS"
echo "OUT=$OUT"
echo "LOG=$LOG"

echo "## System"
hostname
nvidia-smi --query-gpu=name,memory.total,compute_cap,driver_version --format=csv,noheader

echo "## Paths"
ls -ld /root/RelationAwareInstructScene /root/RelationAwareInstructScene/repos/respace /root/autodl-tmp/RelationAwareInstructScene || true

echo "## ReSpace env import smoke"
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
python - <<'PY'
from pathlib import Path
import torch
print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))
mods=['transformers','datasets','vllm','trimesh','dotenv','shapely','clip','xformers','nltk']
for m in mods:
    try:
        mod=__import__(m)
        print('IMPORT_OK', m, getattr(mod,'__version__','na'))
    except Exception as e:
        print('IMPORT_FAIL', m, repr(e))
checks={
 'respace_ckpt_config':'ckpts/gradient-spaces/respace-sg-llm-1.5b/config.json',
 'respace_ckpt_weights':'ckpts/gradient-spaces/respace-sg-llm-1.5b/model.safetensors',
 'ssr_bedroom_split':'dataset-ssr3dfront/splits/bedroom_splits.pkl',
 'ssr_livingroom_split':'dataset-ssr3dfront/splits/livingroom_splits.pkl',
 'asset_metadata':'data/metadata/model_info_3dfuture_assets.json',
 'asset_metadata_scaled':'data/metadata/model_info_3dfuture_assets_scaled.json',
 'asset_metadata_prompts':'data/metadata/model_info_3dfuture_assets_prompts.json',
 'asset_embed_cache':'data/metadata/model_info_3dfuture_assets_embeds.pickle',
 'eval_viz_cache':'eval/viz'
}
for k,v in checks.items():
    p=Path(v)
    print('CHECK', k, 'OK' if p.exists() else 'MISSING', v, p.stat().st_size if p.exists() and p.is_file() else '')
PY

echo "## Try official A100 ReSpace vLLM smoke"
export PYTHONPATH=.
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
SMOKE_OUT=$OUT/respace_smoke_bedroom_vllm
mkdir -p "$SMOKE_OUT"
set +e
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$SMOKE_OUT" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 1 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --icl-k 1 \
  --bon-llm 1
SMOKE_RC=$?
set -e
echo "SMOKE_RC=$SMOKE_RC"
find "$SMOKE_OUT" -maxdepth 4 -type f -printf 'SMOKE_FILE %p %s\n' | sort | head -n 200 || true

echo "## Existing relation-aware baseline metrics"
find /root/RelationAwareInstructScene/results -maxdepth 4 -type f | grep -E 'csv|json|html|log' | sort | tail -n 120 || true

echo "## Summary JSON"
python - <<PY
import json, pathlib
summary={
 'timestamp':'$TS',
 'gpu':'NVIDIA A100-PCIE-40GB',
 'official_respace_smoke_rc':$SMOKE_RC,
 'log':'$LOG',
 'out':'$OUT',
 'blocking_items':[
   'meta-llama/Meta-Llama-3.1-8B-Instruct tokenizer requires authorized Hugging Face token',
   'data/metadata/model_info_3dfuture_assets_embeds.pickle missing (~174MB official ReSpace asset embedding cache)'
 ],
 'interpretation':'A100 resolves V100 BF16/FlashAttention/vLLM hardware blocker; official ReSpace comparison still not reliable until gated tokenizer and asset embedding cache are provided.'
}
path=pathlib.Path('$OUT/summary.json')
path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
print(path)
print(json.dumps(summary, indent=2, ensure_ascii=False))
PY

echo "PASS audit script completed with smoke rc $SMOKE_RC"
echo "LOG=$LOG"
echo "OUT=$OUT"
