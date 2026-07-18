#!/usr/bin/env bash
set -euo pipefail
LOG=/root/RelationAwareInstructScene/logs/respace_ssr_download_$(date +%Y%m%d_%H%M%S).log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
mkdir -p /root/autodl-tmp/RelationAwareInstructScene/respace_data/dataset-ssr3dfront
ln -sfn /root/autodl-tmp/RelationAwareInstructScene/respace_data/dataset-ssr3dfront dataset-ssr3dfront
python - <<'PY'
import requests, zipfile
from pathlib import Path
url='https://hf-mirror.com/datasets/gradient-spaces/SSR-3DFRONT/resolve/main/raw_scenes.zip'
out=Path('/root/autodl-tmp/RelationAwareInstructScene/respace_data/raw_scenes.zip')
out.parent.mkdir(parents=True, exist_ok=True)
with requests.get(url, stream=True, timeout=60) as r:
    r.raise_for_status()
    total=int(r.headers.get('content-length') or 0)
    done=0
    with out.open('wb') as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                done += len(chunk)
                print('DOWNLOADED', done, 'OF', total, flush=True)
print('ZIP_SIZE', out.stat().st_size)
with zipfile.ZipFile(out, 'r') as z:
    z.extractall('dataset-ssr3dfront/')
print('EXTRACTED')
for p in Path('dataset-ssr3dfront').glob('**/*'):
    if p.is_file():
        print('FILE', p, p.stat().st_size)
PY
echo "PASS ssr dataset downloaded"
echo "$LOG"
