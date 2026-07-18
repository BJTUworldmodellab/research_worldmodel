#!/usr/bin/env bash
set -u

ROOT="${RELATION_ROOT:-/root/RelationAwareInstructScene}"
TMP_ROOT="${RELATION_TMP_ROOT:-/root/autodl-tmp/RelationAwareInstructScene}"
REPO="${ROOT}/repos/InstructScene"
FAIL=0

check_path() {
  local kind="$1"
  local path="$2"
  if [ "$kind" = "file" ] && [ -f "$path" ]; then
    echo "[ok] file $path"
  elif [ "$kind" = "dir" ] && [ -d "$path" ]; then
    echo "[ok] dir  $path"
  elif [ "$kind" = "link" ] && [ -L "$path" ]; then
    echo "[ok] link $path -> $(readlink "$path")"
  else
    echo "[miss] $kind $path"
    FAIL=1
  fi
}

echo "[check] GPU"
nvidia-smi || FAIL=1

echo "[check] disk"
df -h /root /root/autodl-tmp 2>/dev/null || df -h
free_kb="$(df -Pk /root/autodl-tmp 2>/dev/null | awk 'NR==2 {print $4}')"
if [ -n "${free_kb}" ] && [ "${free_kb}" -lt 52428800 ]; then
  echo "[warn] /root/autodl-tmp has less than 50GB free; full data/checkpoint setup may fail"
fi

echo "[check] project paths"
check_path dir "${ROOT}"
check_path dir "${REPO}"
check_path file "${REPO}/src/relation_aware_generate_sg.py"
check_path link "${REPO}/dataset/InstructScene"
check_path link "${REPO}/dataset/3D-FRONT"
check_path link "${REPO}/out"
check_path dir "${TMP_ROOT}/datasets/InstructScene"
check_path dir "${ROOT}/raw_data/3D-FRONT"
check_path dir "${ROOT}/raw_data/3D-FRONT/3D-FUTURE-model"

if [ -d "${ROOT}/raw_data/3D-FRONT/3D-FUTURE-model" ]; then
  model_count="$(find "${ROOT}/raw_data/3D-FRONT/3D-FUTURE-model" -name raw_model.obj 2>/dev/null | wc -l | tr -d ' ')"
  echo "[check] 3D-FUTURE raw_model.obj count: ${model_count}"
  if [ "${model_count}" -lt 4000 ]; then
    echo "[warn] expected roughly 4232+ available model assets for the recorded bedroom/living/dining setup"
  fi
fi

echo "[check] checkpoint output roots"
for tag in \
  bedroom_sg2scdiffusion_objfeat \
  bedroom_sgdiffusion_vq_objfeat \
  livingroom_sg2scdiffusion_objfeat \
  livingroom_sgdiffusion_vq_objfeat \
  diningroom_sg2scdiffusion_objfeat \
  diningroom_sgdiffusion_vq_objfeat
do
  if find "${TMP_ROOT}/instructscene_out" "${REPO}/out" -path "*${tag}*" -print -quit 2>/dev/null | grep -q .; then
    echo "[ok] checkpoint/output tag visible: ${tag}"
  else
    echo "[warn] checkpoint/output tag not found yet: ${tag}"
  fi
done

echo "[check] Python imports"
python - <<'PY' || FAIL=1
import importlib
mods = ["torch", "numpy", "trimesh", "pyrender", "cv2", "skimage", "diffusers", "transformers", "accelerate", "huggingface_hub"]
for name in mods:
    mod = importlib.import_module(name)
    print(f"[ok] {name}: {getattr(mod, '__version__', 'ok')}")
try:
    import fcl
    print("[ok] fcl")
except Exception as exc:
    raise SystemExit(f"[fail] fcl: {exc}")
PY

if [ "$FAIL" -eq 0 ]; then
  echo "[check] PASS: base environment looks ready"
else
  echo "[check] NOT READY: fix missing items above"
fi
exit "$FAIL"
