#!/usr/bin/env bash
set -euo pipefail
LOG=/root/RelationAwareInstructScene/logs/respace_model_download_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
mkdir -p "$HF_HOME"
mkdir -p /root/autodl-tmp/RelationAwareInstructScene/respace_ckpts/gradient-spaces
python - <<'PY'
from huggingface_hub import snapshot_download
from pathlib import Path
local = Path('/root/autodl-tmp/RelationAwareInstructScene/respace_ckpts/gradient-spaces/respace-sg-llm-1.5b')
local.mkdir(parents=True, exist_ok=True)
p = snapshot_download(
    repo_id='gradient-spaces/respace-sg-llm-1.5b',
    local_dir=str(local),
    local_dir_use_symlinks=False,
    resume_download=True,
)
print('MODEL_DIR', p)
for f in sorted(local.glob('*')):
    if f.is_file():
        print('MODEL_FILE', f.name, f.stat().st_size)
PY
mkdir -p ckpts/gradient-spaces
ln -sfn /root/autodl-tmp/RelationAwareInstructScene/respace_ckpts/gradient-spaces/respace-sg-llm-1.5b ckpts/gradient-spaces/respace-sg-llm-1.5b
ls -lh ckpts/gradient-spaces/respace-sg-llm-1.5b
echo "PASS respace model downloaded"
echo "$LOG"
