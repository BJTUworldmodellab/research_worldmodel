#!/usr/bin/env bash
set -euo pipefail
TS=$(date +%Y%m%d_%H%M%S)
LOG=/root/RelationAwareInstructScene/logs/respace_asset_cache_${TS}.log
exec > >(tee -a "$LOG") 2>&1
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
python -m pip install -q gdown -i https://pypi.tuna.tsinghua.edu.cn/simple || true
mkdir -p data/metadata
OUT=data/metadata/model_info_3dfuture_assets_embeds.pickle
if [ -s "$OUT" ]; then
  echo "CACHE_EXISTS $OUT $(stat -c%s "$OUT")"
else
  echo "DOWNLOADING_OFFICIAL_ASSET_CACHE"
  gdown --fuzzy 'https://drive.google.com/file/d/1T-4cwzNrR2MAAPyxsHrcNhNHh4HXc4vY/view?usp=sharing' -O "$OUT" || \
  gdown 'https://drive.google.com/uc?id=1T-4cwzNrR2MAAPyxsHrcNhNHh4HXc4vY' -O "$OUT"
fi
ls -lh "$OUT" || true
python - <<'PY'
from pathlib import Path
p=Path('data/metadata/model_info_3dfuture_assets_embeds.pickle')
print('ASSET_CACHE', p.exists(), p.stat().st_size if p.exists() else 0)
if p.exists() and p.stat().st_size < 100_000_000:
    raise SystemExit('asset cache too small, likely failed download')
PY
echo "PASS asset cache ready"
echo "LOG=$LOG"
