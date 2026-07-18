#!/usr/bin/env bash
set -euo pipefail

ROOT=/root/RelationAwareInstructScene
source "$ROOT/activate_relation_scene.sh"
LOGDIR="$ROOT/logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/smoke_light_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee "$LOG") 2>&1

echo "[smoke] start $(date)"
echo "[smoke] root=$ROOT"
echo "[smoke] pwd=$(pwd)"
echo "[smoke] python=$(which python)"
echo "[smoke] disk"
df -h / /root/autodl-tmp || true

echo "[smoke] gpu"
nvidia-smi || true
python - <<'PY'
import importlib, os, sys
mods = [
    'torch','numpy','diffusers','transformers','accelerate','huggingface_hub',
    'trimesh','pyrender','cv2','skimage','fcl','clip','nltk','einops'
]
for m in mods:
    mod = importlib.import_module(m)
    print(f"[import] {m}: {getattr(mod, '__version__', 'ok')}")
import torch
print('[torch] cuda_available=', torch.cuda.is_available())
print('[torch] device_count=', torch.cuda.device_count())
PY

echo "[smoke] CLI help"
python src/relation_aware_generate_sg.py --help >/tmp/relation_help.txt
head -n 20 /tmp/relation_help.txt

echo "[smoke] dataset dirs"
python - <<'PY'
from pathlib import Path
base = Path('/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene')
required = ['threed_front_bedroom','threed_front_livingroom','threed_front_diningroom','3D-FUTURE-chatgpt']
for name in required:
    p = base / name
    if not p.exists():
        raise SystemExit(f'missing dataset dir: {p}')
    print(f'[dataset] {name}: {sum(1 for _ in p.iterdir())} items')
PY

echo "[smoke] checkpoint presence and archive integrity"
python - <<'PY'
from pathlib import Path
import zipfile, pickle
paths = [
('/root/RelationAwareInstructScene/repos/InstructScene/out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth', 300_000_000),
('/root/RelationAwareInstructScene/repos/InstructScene/out/threedfront_objfeat_vqvae/objfeat_bounds.pkl', 1),
('/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/bedroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth', 300_000_000),
('/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/bedroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01999.pth', 700_000_000),
('/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/livingroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth', 300_000_000),
('/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/livingroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01459.pth', 700_000_000),
('/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/diningroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth', 300_000_000),
('/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/diningroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01239.pth', 700_000_000),
]
for raw, min_size in paths:
    p = Path(raw)
    if not p.exists():
        raise SystemExit(f'missing checkpoint: {p}')
    size = p.stat().st_size
    if size < min_size:
        raise SystemExit(f'checkpoint too small: {p} size={size}')
    if p.suffix == '.pkl':
        with p.open('rb') as f:
            obj = pickle.load(f)
        print(f'[checkpoint] {p.name}: pickle ok, type={type(obj).__name__}, size={size}')
    else:
        if not zipfile.is_zipfile(p):
            raise SystemExit(f'not a torch zip archive: {p}')
        with zipfile.ZipFile(p) as zf:
            bad = zf.testzip()
            if bad:
                raise SystemExit(f'bad zip member in {p}: {bad}')
            print(f'[checkpoint] {p}: zip crc ok, members={len(zf.infolist())}, size={size}')
PY

echo "[smoke] PASS light smoke completed. Full generation still requires visible GPU and raw 3D-FRONT/3D-FUTURE assets."
echo "[smoke] log=$LOG"
