#!/usr/bin/env bash
set -euo pipefail
LOG=/root/RelationAwareInstructScene/logs/respace_env_fix_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
python -V
python -m pip install -U 'pip<25' 'setuptools<75' wheel
python -m pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121
python - <<'PY'
mods=['torch','transformers','datasets','vllm','trimesh','dotenv','shapely','clip']
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
echo "PASS respace env fixed"
echo "$LOG"
