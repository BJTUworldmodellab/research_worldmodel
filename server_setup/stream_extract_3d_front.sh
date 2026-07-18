#!/usr/bin/env bash
set -euo pipefail
ROOT="${RELATION_ROOT:-/root/RelationAwareInstructScene}"
TMP="${RELATION_TMP_ROOT:-/root/autodl-tmp/RelationAwareInstructScene}"
cd "$ROOT"
source "$ROOT/activate_accel.sh" >/dev/null 2>&1 || true
free_gb=$(df -Pk /root/autodl-tmp | awk 'NR==2 {printf "%.1f", $4/1024/1024}')
echo "[3d-front] free GB on /root/autodl-tmp: ${free_gb}"
echo "[3d-front] Refusing to stream-extract unless ALLOW_RISKY_3DFRONT_EXTRACT=1 is set. Recommended: use 100G/150G+ data disk."
if [ "${ALLOW_RISKY_3DFRONT_EXTRACT:-0}" != "1" ]; then
  exit 2
fi
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y libarchive-tools
python - <<'PY'
from huggingface_hub import hf_hub_url
print(hf_hub_url(repo_id='chenguolin/InstructScene_dataset', filename='3D-FRONT.zip', repo_type='dataset'))
PY
url=$(python - <<'PY'
from huggingface_hub import hf_hub_url
print(hf_hub_url(repo_id='chenguolin/InstructScene_dataset', filename='3D-FRONT.zip', repo_type='dataset'))
PY
)
mkdir -p "$ROOT/raw_data"
curl -L "$url" | bsdtar -xvf - -C "$ROOT/raw_data"
