#!/usr/bin/env bash
set -euo pipefail
LOG=/root/RelationAwareInstructScene/logs/respace_torch_first_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
python -V
python -m pip install -U 'pip<25' 'setuptools>=70.1,<75' wheel
python -m pip install --extra-index-url https://download.pytorch.org/whl/cu121 'torch==2.5.1+cu121' 'torchvision==0.20.1+cu121' 'torchaudio==2.5.1+cu121'
python - <<'PY'
import torch
print('TORCH_READY', torch.__version__, torch.version.cuda, torch.cuda.is_available())
print('GPU', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')
PY
python -m pip install --no-build-isolation -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121
python - <<'PY'
mods=['torch','transformers','datasets','vllm','trimesh','dotenv','shapely','clip','flash_attn']
for m in mods:
    try:
        mod=__import__(m)
        print('IMPORT_OK', m, getattr(mod,'__version__','na'))
    except Exception as e:
        print('IMPORT_FAIL', m, repr(e))
        raise
import torch
print('CUDA_AVAILABLE', torch.cuda.is_available())
print('GPU', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')
PY
echo "PASS respace torch-first env fixed"
echo "$LOG"
