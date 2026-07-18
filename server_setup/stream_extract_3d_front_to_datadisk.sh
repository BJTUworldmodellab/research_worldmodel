#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
TMP=/root/autodl-tmp/RelationAwareInstructScene
DEST=$TMP/raw_data
LOGDIR=$ROOT/logs
mkdir -p "$LOGDIR" "$DEST"
source "$ROOT/activate_accel.sh" >/dev/null 2>&1 || true
free_gb=$(df -Pk /root/autodl-tmp | awk 'NR==2 {printf "%.1f", $4/1024/1024}')
echo "[extract] free GB on /root/autodl-tmp: $free_gb"
python - <<'PY'
from pathlib import Path
p=Path('/root/autodl-tmp/RelationAwareInstructScene/raw_data')
print('[extract] dest', p, 'exists', p.exists())
PY
if ! command -v bsdtar >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y libarchive-tools
fi
url=$(python - <<'PY'
from huggingface_hub import hf_hub_url
print(hf_hub_url(repo_id='chenguolin/InstructScene_dataset', filename='3D-FRONT.zip', repo_type='dataset'))
PY
)
echo "[extract] url=$url"
echo "[extract] streaming zip to $DEST"
curl -L "$url" | bsdtar -xvf - -C "$DEST"
echo "[extract] extracted top-level:"
find "$DEST" -maxdepth 2 -type d | sort | sed -n '1,80p'
ln -sfn "$DEST/3D-FRONT" "$ROOT/repos/InstructScene/dataset/3D-FRONT"
echo "[extract] dataset symlink:"
ls -lah "$ROOT/repos/InstructScene/dataset/3D-FRONT"
df -h /root/autodl-tmp
