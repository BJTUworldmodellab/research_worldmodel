#!/usr/bin/env bash
# Phase-2 AutoDL setup for SDGScenes strong-baseline experiments.
# Uses Python venv instead of micromamba because some AutoDL networks stall on micromamba streaming downloads.

set -Eeuo pipefail
umask 077

WORK_ROOT="${WORK_ROOT:-/root/autodl-tmp/rg-sota-cloud}"
VENV_DIR="${VENV_DIR:-$WORK_ROOT/venvs/relation-sdg}"
PYTORCH_INDEX_URL="${PYTORCH_INDEX_URL:-https://download.pytorch.org/whl/cu128}"
PYTORCH_PACKAGES="${PYTORCH_PACKAGES:-torch torchvision torchaudio}"
SKIP_DEEPSEEK_CONFIG="${SKIP_DEEPSEEK_CONFIG:-1}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$WORK_ROOT"/{logs,manifests,scripts,.secrets,repos,data/raw,data/external,data/processed,artifacts,runs,outputs,doc,venvs}
mkdir -p "$WORK_ROOT"/{tmp,pip-cache}
export TMPDIR="$WORK_ROOT/tmp"
export PIP_CACHE_DIR="$WORK_ROOT/pip-cache"
LOG_FILE="$WORK_ROOT/logs/phase2_venv_${STAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[phase2] start: $STAMP"
echo "[phase2] work root: $WORK_ROOT"
echo "[phase2] venv: $VENV_DIR"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi | tee "$WORK_ROOT/manifests/phase2_nvidia_smi_${STAMP}.txt"
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv \
    | tee "$WORK_ROOT/manifests/phase2_gpu_query_${STAMP}.csv"
fi

echo "[phase2] creating Python venv"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel

echo "[phase2] installing scientific/runtime packages from PyPI"
python -m pip install --prefer-binary \
  numpy \
  scipy \
  pandas \
  pyyaml \
  tqdm \
  rich \
  shapely \
  networkx \
  scikit-learn \
  matplotlib \
  seaborn \
  trimesh \
  pillow \
  imageio \
  opencv-python-headless \
  scikit-image \
  einops \
  joblib

echo "[phase2] installing PyTorch runtime from: $PYTORCH_INDEX_URL"
python -m pip install \
  --no-cache-dir \
  --timeout 120 \
  --retries 3 \
  $PYTORCH_PACKAGES \
  --index-url "$PYTORCH_INDEX_URL"

echo "[phase2] running CUDA smoke test"
python - <<'PY' | tee "$WORK_ROOT/manifests/phase2_torch_cuda_smoke_${STAMP}.txt"
import torch

print("torch_version", torch.__version__)
print("torch_cuda", torch.version.cuda)
print("cuda_available", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available")
print("device", torch.cuda.get_device_name(0))
print("capability", torch.cuda.get_device_capability(0))
x = torch.randn((256, 256), device="cuda")
y = x @ x.T
torch.cuda.synchronize()
print("cuda_matmul_mean", float(y.mean().detach().cpu()))
PY

echo "[phase2] installing ML utility packages"
python -m pip install --prefer-binary \
  clip-anytorch \
  sentence-transformers \
  transformers \
  accelerate \
  open3d

python -m pip freeze | tee "$WORK_ROOT/manifests/phase2_pip_freeze_${STAMP}.txt"

echo "[phase2] installing Node.js 20+ and Claude Code"
if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 18 ? 0 : 1)'; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
node --version | tee "$WORK_ROOT/manifests/phase2_node_version_${STAMP}.txt"
npm --version | tee "$WORK_ROOT/manifests/phase2_npm_version_${STAMP}.txt"
npm install -g @anthropic-ai/claude-code
claude --version | tee "$WORK_ROOT/manifests/phase2_claude_code_version_${STAMP}.txt" || true

echo "[phase2] configuring DeepSeek environment for Claude Code"
SECRET_ENV="$WORK_ROOT/.secrets/deepseek_claude.env"
if [[ "$SKIP_DEEPSEEK_CONFIG" == "1" ]]; then
  echo "[phase2] SKIP_DEEPSEEK_CONFIG=1; no API key requested or stored."
elif [[ ! -s "$SECRET_ENV" ]]; then
  if [[ -z "${DEEPSEEK_API_KEY:-}" && -z "${ANTHROPIC_AUTH_TOKEN:-}" ]]; then
    echo "Paste DeepSeek API key for Claude Code. Input is hidden and will be saved only to $SECRET_ENV."
    read -r -s -p "DeepSeek API key: " DEEPSEEK_API_KEY
    echo
  fi
  TOKEN_VALUE="${ANTHROPIC_AUTH_TOKEN:-${DEEPSEEK_API_KEY:-}}"
  {
    echo "export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic"
    printf 'export ANTHROPIC_AUTH_TOKEN=%q\n' "$TOKEN_VALUE"
    printf 'export ANTHROPIC_API_KEY=%q\n' "$TOKEN_VALUE"
    echo "export ANTHROPIC_MODEL=deepseek-v4-pro[1m]"
    echo "export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]"
    echo "export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]"
    echo "export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash"
    echo "export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash"
    echo "export CLAUDE_CODE_EFFORT_LEVEL=max"
  } > "$SECRET_ENV"
  chmod 600 "$SECRET_ENV"
fi

cat > "$WORK_ROOT/scripts/run_claude_deepseek.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
WORK_ROOT="${WORK_ROOT:-/root/autodl-tmp/rg-sota-cloud}"
if [[ -s "$WORK_ROOT/.secrets/deepseek_claude.env" ]]; then
  source "$WORK_ROOT/.secrets/deepseek_claude.env"
else
  echo "Missing $WORK_ROOT/.secrets/deepseek_claude.env. Run scripts/setup_deepseek_claude_env.sh first." >&2
  exit 2
fi
cd "${1:-$WORK_ROOT/repos}"
exec claude
SH
chmod +x "$WORK_ROOT/scripts/run_claude_deepseek.sh"

cat > "$WORK_ROOT/scripts/setup_deepseek_claude_env.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
WORK_ROOT="${WORK_ROOT:-/root/autodl-tmp/rg-sota-cloud}"
SECRET_ENV="$WORK_ROOT/.secrets/deepseek_claude.env"
mkdir -p "$WORK_ROOT/.secrets"
chmod 700 "$WORK_ROOT/.secrets"
read -r -s -p "DeepSeek API key: " DEEPSEEK_API_KEY
echo
{
  echo "export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic"
  printf 'export ANTHROPIC_AUTH_TOKEN=%q\n' "$DEEPSEEK_API_KEY"
  printf 'export ANTHROPIC_API_KEY=%q\n' "$DEEPSEEK_API_KEY"
  echo "export ANTHROPIC_MODEL=deepseek-v4-pro[1m]"
  echo "export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]"
  echo "export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]"
  echo "export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash"
  echo "export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash"
  echo "export CLAUDE_CODE_EFFORT_LEVEL=max"
} > "$SECRET_ENV"
chmod 600 "$SECRET_ENV"
echo "Wrote $SECRET_ENV (secret not printed)."
SH
chmod +x "$WORK_ROOT/scripts/setup_deepseek_claude_env.sh"

if [[ ! -s "$WORK_ROOT/manifests/raw_data_manifest.tsv" ]]; then
  cat > "$WORK_ROOT/manifests/raw_data_manifest.tsv" <<'TSV'
asset_id	dataset_name	source_url	license_or_terms	acquisition_method	download_command_sha256	original_path	canonical_path	bytes	sha256	mtime_utc	registered_at_utc	split	notes
TSV
fi

cat > "$WORK_ROOT/scripts/register_raw_file.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $# -lt 5 ]]; then
  echo "usage: register_raw_file.sh <dataset_name> <source_url> <license_or_terms> <split> <path> [notes]" >&2
  exit 2
fi
WORK_ROOT="${WORK_ROOT:-/root/autodl-tmp/rg-sota-cloud}"
MANIFEST="$WORK_ROOT/manifests/raw_data_manifest.tsv"
DATASET_NAME="$1"
SOURCE_URL="$2"
LICENSE_OR_TERMS="$3"
SPLIT="$4"
FILE_PATH="$5"
NOTES="${6:-}"
CANON="$(readlink -f "$FILE_PATH")"
BYTES="$(stat -c '%s' "$CANON")"
SHA="$(sha256sum "$CANON" | awk '{print $1}')"
MTIME="$(date -u -d "@$(stat -c '%Y' "$CANON")" +%Y-%m-%dT%H:%M:%SZ)"
REGISTERED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ASSET_ID="${DATASET_NAME}_${SHA:0:12}"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  "$ASSET_ID" "$DATASET_NAME" "$SOURCE_URL" "$LICENSE_OR_TERMS" "manual_or_scripted" "" \
  "$FILE_PATH" "$CANON" "$BYTES" "$SHA" "$MTIME" "$REGISTERED" "$SPLIT" "$NOTES" >> "$MANIFEST"
echo "$ASSET_ID $SHA $CANON"
SH
chmod +x "$WORK_ROOT/scripts/register_raw_file.sh"

cat > "$WORK_ROOT/scripts/activate_relation_sdg.sh" <<SH
#!/usr/bin/env bash
source "$VENV_DIR/bin/activate"
export WORK_ROOT="$WORK_ROOT"
echo "Activated relation-sdg venv at $VENV_DIR"
SH
chmod +x "$WORK_ROOT/scripts/activate_relation_sdg.sh"

echo "[phase2] done"
echo "[phase2] activate with: source $WORK_ROOT/scripts/activate_relation_sdg.sh"
echo "[phase2] configure DeepSeek with: $WORK_ROOT/scripts/setup_deepseek_claude_env.sh"
echo "[phase2] run Claude with: $WORK_ROOT/scripts/run_claude_deepseek.sh $WORK_ROOT/repos"
