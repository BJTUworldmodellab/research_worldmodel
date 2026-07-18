#!/usr/bin/env bash
set -euo pipefail

ROOT="${RELATION_ROOT:-/root/RelationAwareInstructScene}"
TMP_ROOT="${RELATION_TMP_ROOT:-/root/autodl-tmp/RelationAwareInstructScene}"
REPO="${ROOT}/repos/InstructScene"
REQ="${ROOT}/server_setup/relation_scene_requirements.txt"

echo "[setup] root: ${ROOT}"
echo "[setup] tmp : ${TMP_ROOT}"

mkdir -p "${ROOT}/repos" \
         "${ROOT}/raw_data" \
         "${ROOT}/outputs" \
         "${ROOT}/logs" \
         "${ROOT}/scripts" \
         "${ROOT}/archive" \
         "${TMP_ROOT}/datasets" \
         "${TMP_ROOT}/instructscene_out"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "[warn] nvidia-smi not found"
fi

if [ ! -d "${REPO}/.git" ]; then
  if [ -n "${INSTRUCTSCENE_REPO_URL:-}" ]; then
    echo "[setup] cloning InstructScene from ${INSTRUCTSCENE_REPO_URL}"
    git clone "${INSTRUCTSCENE_REPO_URL}" "${REPO}"
  else
    echo "[warn] ${REPO} does not exist and INSTRUCTSCENE_REPO_URL is not set"
    echo "[warn] clone/copy InstructScene into ${REPO}, then rerun this script"
  fi
fi

if [ -d "${REPO}" ]; then
  mkdir -p "${REPO}/dataset"
  ln -sfn "${TMP_ROOT}/datasets/InstructScene" "${REPO}/dataset/InstructScene"
  ln -sfn "${ROOT}/raw_data/3D-FRONT" "${REPO}/dataset/3D-FRONT"
  ln -sfn "${TMP_ROOT}/instructscene_out" "${REPO}/out"

  if [ -f "${ROOT}/relation_aware_generate_sg.py" ]; then
    cp "${ROOT}/relation_aware_generate_sg.py" "${REPO}/src/relation_aware_generate_sg.py"
  elif [ -f "${ROOT}/results/relation_aware_generate_sg.py" ]; then
    cp "${ROOT}/results/relation_aware_generate_sg.py" "${REPO}/src/relation_aware_generate_sg.py"
  else
    echo "[warn] relation_aware_generate_sg.py not found under ${ROOT}"
  fi
fi

if [ -f "${ROOT}/run_mesh_visual_eval.sh" ]; then
  chmod +x "${ROOT}/run_mesh_visual_eval.sh"
fi

if [ -d "${ROOT}/scripts" ]; then
  chmod +x "${ROOT}/scripts/"*.py 2>/dev/null || true
fi

echo "[setup] installing apt packages"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git wget curl unzip zip rsync tmux htop build-essential cmake pkg-config \
  libgl1 libglib2.0-0 libosmesa6 libosmesa6-dev libglfw3 libglfw3-dev \
  libfcl-dev libccd-dev

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

echo "[setup] python: $(${PYTHON_BIN} --version)"
"${PYTHON_BIN}" -m pip install --upgrade pip wheel
"${PYTHON_BIN}" -m pip install "setuptools<81"
if [ -f "${REPO}/requirements.txt" ]; then
  echo "[setup] installing InstructScene requirements.txt"
  "${PYTHON_BIN}" -m pip install -r "${REPO}/requirements.txt"
else
  echo "[warn] InstructScene requirements.txt not found under ${REPO}"
fi
if [ -f "${REQ}" ]; then
  "${PYTHON_BIN}" -m pip install -r "${REQ}"
else
  echo "[warn] requirements not found: ${REQ}"
fi

cat > "${ROOT}/activate_relation_scene.sh" <<'EOF'
#!/usr/bin/env bash
export RELATION_ROOT="${RELATION_ROOT:-/root/RelationAwareInstructScene}"
export PYTHONPATH="${RELATION_ROOT}/repos/InstructScene:${RELATION_ROOT}/repos/InstructScene/src:${PYTHONPATH:-}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYOPENGL_PLATFORM="${PYOPENGL_PLATFORM:-egl}"
cd "${RELATION_ROOT}/repos/InstructScene"
EOF
chmod +x "${ROOT}/activate_relation_scene.sh"

echo "[setup] basic Python import check"
"${PYTHON_BIN}" - <<'PY'
import importlib
mods = ["torch", "numpy", "PIL", "trimesh", "pyrender", "cv2", "skimage"]
for name in mods:
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", "ok")
        print(f"[ok] {name}: {version}")
    except Exception as exc:
        print(f"[missing] {name}: {exc}")
try:
    import fcl
    print("[ok] fcl: ok")
except Exception as exc:
    print(f"[missing] fcl: {exc}")
PY

echo "[setup] finished. Next run:"
echo "  bash ${ROOT}/server_setup/check_relation_scene_server.sh"
