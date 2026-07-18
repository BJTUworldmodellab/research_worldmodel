#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/RelationAwareInstructScene
REPO=$ROOT/repos/respace
STAMP=$(date +%Y%m%d_%H%M%S)
LOG=$ROOT/logs/respace_env_setup_${STAMP}.log
mkdir -p $ROOT/logs
exec > >(tee "$LOG") 2>&1
source /root/miniconda3/etc/profile.d/conda.sh
cd "$REPO"
cat > .env.baseline <<'EOF'
PTH_3DFRONT_SCENES=/root/autodl-tmp/RelationAwareInstructScene/raw_data/3D-FRONT/3D-FRONT
PTH_3DFUTURE_ASSETS=/root/autodl-tmp/RelationAwareInstructScene/raw_data/3D-FRONT/3D-FUTURE-model
PTH_INVALID_ROOMS=./data/metadata/invalid_threed_front_rooms.txt
PTH_ASSETS_METADATA=./data/metadata/model_info_3dfuture_assets.json
PTH_ASSETS_METADATA_SCALED=./data/metadata/model_info_3dfuture_assets_scaled.json
PTH_ASSETS_METADATA_SIMPLE_DESCS=./data/metadata/model_info_3dfuture_assets_simple_descs.json
PTH_ASSETS_METADATA_PROMPTS=./data/metadata/model_info_3dfuture_assets_prompts.json
PTH_ASSETS_EMBED=./data/metadata/model_info_3dfuture_assets_embeds.pickle
PTH_EVAL_VIZ_CACHE=./eval/viz
PTH_DATASET_CACHE=./data/cache
PTH_STAGE_3=./dataset-ssr3dfront/splits
EOF
conda env list
if ! conda env list | awk '{print $1}' | grep -qx respace; then
  conda create -n respace python=3.9 -y
fi
conda activate respace
python --version
python -m pip install --upgrade pip
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple || true
python -m pip config set global.extra-index-url https://download.pytorch.org/whl/cu121 || true
python -m pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121
python - <<'PY'
mods=['torch','transformers','datasets','vllm','trimesh','dotenv','shapely']
for m in mods:
    try:
        mod=__import__(m)
        print('IMPORT_OK', m, getattr(mod,'__version__',''))
    except Exception as e:
        print('IMPORT_FAIL', m, type(e).__name__, str(e)[:500])
PY
echo "[respace_env_setup] PASS log=$LOG"
