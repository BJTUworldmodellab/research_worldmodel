#!/usr/bin/env bash
set -euo pipefail
LOG=/root/RelationAwareInstructScene/logs/respace_no_github_clip_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
python -V
python -m pip install -U 'pip<25' 'setuptools>=70.1,<75' wheel
python -m pip install openai-clip ftfy regex tqdm
python - <<'PY'
import clip
print('CLIP_READY', getattr(clip,'__file__','unknown'))
PY
python - <<'PY'
from pathlib import Path
src=Path('requirements.txt')
out=Path('/tmp/respace_requirements_no_clip.txt')
lines=[]
for line in src.read_text().splitlines():
    if line.strip().startswith('clip @ git+'):
        continue
    lines.append(line)
out.write_text('\n'.join(lines)+'\n')
print(out)
PY
python -m pip install --no-build-isolation -r /tmp/respace_requirements_no_clip.txt --extra-index-url https://download.pytorch.org/whl/cu121
python - <<'PY'
mods=['torch','transformers','datasets','vllm','trimesh','dotenv','shapely','clip']
for m in mods:
    try:
        mod=__import__(m)
        print('IMPORT_OK', m, getattr(mod,'__version__','na'))
    except Exception as e:
        print('IMPORT_FAIL', m, repr(e))
        raise
try:
    import flash_attn
    print('IMPORT_OK flash_attn', getattr(flash_attn,'__version__','na'))
except Exception as e:
    print('IMPORT_FAIL flash_attn', repr(e))
    raise
import torch
print('CUDA_AVAILABLE', torch.cuda.is_available())
print('GPU', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none')
PY
echo "PASS respace no-github-clip env fixed"
echo "$LOG"
