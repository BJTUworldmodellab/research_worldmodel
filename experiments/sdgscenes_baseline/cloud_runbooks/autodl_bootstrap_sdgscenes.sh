#!/usr/bin/env bash
# AutoDL cloud bootstrap for the SDGScenes defensive/strong-baseline track.
# Safe by default: no passwords, API keys, or raw licensed datasets are committed.

set -Eeuo pipefail
umask 077

if [[ -z "${WORK_ROOT:-}" ]]; then
  if [[ -d /root/autodl-tmp ]]; then
    WORK_ROOT="/root/autodl-tmp/rg-sota-cloud"
  else
    WORK_ROOT="/root/rg-sota-cloud"
  fi
fi
PROJECT_REPO="${PROJECT_REPO:-}"
PROJECT_BRANCH="${PROJECT_BRANCH:-main}"
PROJECT_DIR="${PROJECT_DIR:-$WORK_ROOT/repos/project}"
PYTHON_VERSION="${PYTHON_VERSION:-3.10}"
RUN_NAME="${RUN_NAME:-sdgscenes_strong_baseline}"
PYTORCH_INDEX_URL="${PYTORCH_INDEX_URL:-https://download.pytorch.org/whl/cu128}"
PYTORCH_PACKAGES="${PYTORCH_PACKAGES:-torch torchvision torchaudio}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p \
  "$WORK_ROOT"/{repos,data/raw,data/external,data/processed,artifacts,runs,logs,manifests,notion,prompts,claude,.secrets,scripts}

LOG_FILE="$WORK_ROOT/logs/bootstrap_${STAMP}.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[bootstrap] start: $STAMP"
echo "[bootstrap] work root: $WORK_ROOT"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "[bootstrap] ERROR: run this script as root on the AutoDL instance." >&2
  exit 1
fi

echo "[bootstrap] recording machine provenance"
{
  echo "timestamp_utc: $STAMP"
  echo "hostname: $(hostname)"
  echo "kernel: $(uname -a)"
  echo "user: $(id)"
  echo "work_root: $WORK_ROOT"
  echo "autodl_data_disk_hint: use /root/autodl-tmp when available"
} > "$WORK_ROOT/manifests/machine_fingerprint_${STAMP}.txt"

if [[ -f /etc/os-release ]]; then
  cp /etc/os-release "$WORK_ROOT/manifests/os_release_${STAMP}.txt"
fi

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi | tee "$WORK_ROOT/manifests/nvidia_smi_${STAMP}.txt"
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv \
    | tee "$WORK_ROOT/manifests/gpu_query_${STAMP}.csv"
else
  echo "[bootstrap] WARNING: nvidia-smi not found yet."
fi

df -h | tee "$WORK_ROOT/manifests/disk_${STAMP}.txt"
free -h | tee "$WORK_ROOT/manifests/memory_${STAMP}.txt"

echo "[bootstrap] installing base system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  bash-completion \
  build-essential \
  ca-certificates \
  cmake \
  curl \
  ffmpeg \
  git \
  git-lfs \
  gnupg \
  htop \
  jq \
  libgl1 \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender1 \
  lsb-release \
  nano \
  ninja-build \
  openssh-client \
  pkg-config \
  python3 \
  python3-pip \
  python3-venv \
  rsync \
  screen \
  tmux \
  tree \
  unzip \
  vim \
  wget \
  zip

git lfs install --system || true

echo "[bootstrap] installing GitHub CLI if missing"
if [[ "${SKIP_GH_INSTALL:-0}" == "1" ]]; then
  echo "[bootstrap] SKIP_GH_INSTALL=1; skipping GitHub CLI install."
elif ! command -v gh >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/etc/apt/keyrings/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list
  apt-get update
  apt-get install -y gh
fi
gh --version | tee "$WORK_ROOT/manifests/gh_version_${STAMP}.txt" || true

echo "[bootstrap] installing micromamba if missing"
if ! command -v micromamba >/dev/null 2>&1; then
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xvj -C /usr/local/bin --strip-components=1 bin/micromamba
fi
micromamba --version | tee "$WORK_ROOT/manifests/micromamba_version_${STAMP}.txt"

echo "[bootstrap] creating Python environment"
export MAMBA_ROOT_PREFIX="$WORK_ROOT/micromamba"
micromamba create -y -n relation-sdg -c conda-forge "python=${PYTHON_VERSION}" pip setuptools wheel
micromamba run -n relation-sdg python -m pip install --upgrade pip
micromamba run -n relation-sdg python -m pip install \
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
  open3d \
  pillow \
  imageio \
  opencv-python-headless

echo "[bootstrap] installing PyTorch runtime from: $PYTORCH_INDEX_URL"
echo "[bootstrap] PyTorch packages: $PYTORCH_PACKAGES"
micromamba run -n relation-sdg python -m pip install \
  $PYTORCH_PACKAGES \
  --index-url "$PYTORCH_INDEX_URL"

micromamba run -n relation-sdg python - <<'PY' | tee "$WORK_ROOT/manifests/torch_cuda_smoke_${STAMP}.txt"
import torch

print("torch_version", torch.__version__)
print("torch_cuda", torch.version.cuda)
print("cuda_available", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit("CUDA is not available in relation-sdg env")

print("device", torch.cuda.get_device_name(0))
print("capability", torch.cuda.get_device_capability(0))
x = torch.randn((128, 128), device="cuda")
y = x @ x.T
torch.cuda.synchronize()
print("cuda_matmul_mean", float(y.mean().detach().cpu()))
PY

micromamba run -n relation-sdg python -m pip install \
  clip-anytorch \
  sentence-transformers \
  transformers \
  accelerate

micromamba run -n relation-sdg python -m pip freeze \
  | tee "$WORK_ROOT/manifests/pip_freeze_relation_sdg_${STAMP}.txt"

echo "[bootstrap] installing Node.js 20+ and Claude Code"
if ! command -v node >/dev/null 2>&1 || ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 18 ? 0 : 1)'; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
node --version | tee "$WORK_ROOT/manifests/node_version_${STAMP}.txt"
npm --version | tee "$WORK_ROOT/manifests/npm_version_${STAMP}.txt"
npm install -g @anthropic-ai/claude-code
claude --version | tee "$WORK_ROOT/manifests/claude_code_version_${STAMP}.txt" || true

echo "[bootstrap] configuring DeepSeek environment for Claude Code"
SECRET_ENV="$WORK_ROOT/.secrets/deepseek_claude.env"
if [[ "${SKIP_DEEPSEEK_CONFIG:-0}" == "1" ]]; then
  echo "[bootstrap] SKIP_DEEPSEEK_CONFIG=1; DeepSeek env configuration skipped."
  echo "[bootstrap] Later, create $SECRET_ENV with ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN/API_KEY, and DeepSeek model variables."
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
echo "[bootstrap] DeepSeek env file exists at $SECRET_ENV (not printed)."

echo "[bootstrap] writing raw-data manifest helpers"
cat > "$WORK_ROOT/manifests/raw_data_manifest.tsv" <<'TSV'
asset_id	dataset_name	source_url	license_or_terms	acquisition_method	download_command_sha256	original_path	canonical_path	bytes	sha256	mtime_utc	registered_at_utc	split	notes
TSV

cat > "$WORK_ROOT/scripts/register_raw_file.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
if [[ $# -lt 5 ]]; then
  echo "usage: register_raw_file.sh <dataset_name> <source_url> <license_or_terms> <split> <path> [notes]" >&2
  exit 2
fi
DATASET_NAME="$1"
SOURCE_URL="$2"
LICENSE_OR_TERMS="$3"
SPLIT="$4"
FILE_PATH="$5"
NOTES="${6:-}"
if [[ -z "${WORK_ROOT:-}" ]]; then
  if [[ -d /root/autodl-tmp ]]; then
    WORK_ROOT="/root/autodl-tmp/rg-sota-cloud"
  else
    WORK_ROOT="/root/rg-sota-cloud"
  fi
fi
MANIFEST="$WORK_ROOT/manifests/raw_data_manifest.tsv"
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

cat > "$WORK_ROOT/scripts/start_traced_session.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
if [[ -z "${WORK_ROOT:-}" ]]; then
  if [[ -d /root/autodl-tmp ]]; then
    WORK_ROOT="/root/autodl-tmp/rg-sota-cloud"
  else
    WORK_ROOT="/root/rg-sota-cloud"
  fi
fi
NAME="${1:-sdgscenes}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$WORK_ROOT/logs"
echo "Starting tmux session: ${NAME}_${STAMP}"
echo "Terminal transcript: $WORK_ROOT/logs/${NAME}_${STAMP}.typescript"
tmux new-session -s "${NAME}_${STAMP}" "cd '$WORK_ROOT'; script -f '$WORK_ROOT/logs/${NAME}_${STAMP}.typescript'"
SH
chmod +x "$WORK_ROOT/scripts/start_traced_session.sh"

echo "[bootstrap] cloning project repository if provided"
if [[ -n "$PROJECT_REPO" ]]; then
  if [[ -d "$PROJECT_DIR/.git" ]]; then
    git -C "$PROJECT_DIR" fetch --all --prune
    git -C "$PROJECT_DIR" checkout "$PROJECT_BRANCH" || true
    git -C "$PROJECT_DIR" pull --ff-only || true
  else
    git clone --recursive --branch "$PROJECT_BRANCH" "$PROJECT_REPO" "$PROJECT_DIR" \
      || git clone --recursive "$PROJECT_REPO" "$PROJECT_DIR"
  fi
  git -C "$PROJECT_DIR" rev-parse HEAD | tee "$WORK_ROOT/manifests/project_git_head_${STAMP}.txt"
  git -C "$PROJECT_DIR" status --short | tee "$WORK_ROOT/manifests/project_git_status_${STAMP}.txt"
else
  echo "[bootstrap] PROJECT_REPO not set. Clone your GitHub repo later into $PROJECT_DIR."
fi

cat > "$WORK_ROOT/.gitignore_research_outputs_template" <<'EOF'
# Large or licensed raw data: keep outside GitHub unless license explicitly permits redistribution.
data/raw/
data/external/
data/processed/

# Heavy run outputs. Commit only selected small summaries, configs, and manifests.
runs/
artifacts/renders/
artifacts/meshes/
artifacts/checkpoints/

# Secrets
.secrets/
*.key
*.pem
*.token
*.env
EOF

cat > "$WORK_ROOT/scripts/sync_safe_artifacts_to_github.sh" <<'SH'
#!/usr/bin/env bash
set -Eeuo pipefail
if [[ -z "${WORK_ROOT:-}" ]]; then
  if [[ -d /root/autodl-tmp ]]; then
    WORK_ROOT="/root/autodl-tmp/rg-sota-cloud"
  else
    WORK_ROOT="/root/rg-sota-cloud"
  fi
fi
PROJECT_DIR="${PROJECT_DIR:-$WORK_ROOT/repos/project}"
if [[ ! -d "$PROJECT_DIR/.git" ]]; then
  echo "No git repo at $PROJECT_DIR" >&2
  exit 1
fi
cd "$PROJECT_DIR"
mkdir -p cloud_archive
rsync -a --exclude '*.typescript' "$WORK_ROOT/manifests/" "cloud_archive/manifests/"
rsync -a "$WORK_ROOT/notion/" "cloud_archive/notion/"
rsync -a "$WORK_ROOT/prompts/" "cloud_archive/prompts/"
git status --short
echo
echo "Review above. This script intentionally syncs manifests/prompts/notion drafts only, not raw datasets."
read -r -p "Commit and push safe artifacts? Type YES: " CONFIRM
if [[ "$CONFIRM" != "YES" ]]; then
  echo "Aborted."
  exit 0
fi
git add cloud_archive .gitignore || true
git commit -m "Archive SDGScenes cloud baseline traces" || true
git push
SH
chmod +x "$WORK_ROOT/scripts/sync_safe_artifacts_to_github.sh"

echo "[bootstrap] done"
echo "[bootstrap] log: $LOG_FILE"
echo "[bootstrap] next:"
echo "  1) source $SECRET_ENV"
echo "  2) cd $WORK_ROOT/repos/project"
echo "  3) claude"
echo "  4) paste/use the SDGScenes Claude Code prompt"
