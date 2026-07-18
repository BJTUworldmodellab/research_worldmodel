#!/usr/bin/env bash
set -u
ROOT="${RELATION_ROOT:-/root/RelationAwareInstructScene}"
cd "$ROOT"
source "$ROOT/activate_accel.sh" >/dev/null 2>&1 || true
source "$ROOT/activate_relation_scene.sh"
mkdir -p "$ROOT/logs"

echo "[smoke] time $(date '+%F %T')"
echo "[smoke] cwd $(pwd)"
echo "[smoke] gpu"
nvidia-smi || true

echo "[smoke] python imports"
python - <<'PY'
import importlib
mods = ['torch','numpy','diffusers','transformers','accelerate','huggingface_hub','trimesh','pyrender','cv2','skimage','fcl','clip','nltk','einops']
for name in mods:
    mod = importlib.import_module(name)
    print(f'[ok] {name}: {getattr(mod, "__version__", "ok")}')
import torch
print('[info] torch cuda available', torch.cuda.is_available())
print('[info] torch cuda device_count', torch.cuda.device_count())
PY

echo "[smoke] relation_aware_generate_sg help"
python src/relation_aware_generate_sg.py --help >/tmp/relation_help.txt
head -40 /tmp/relation_help.txt

echo "[smoke] dataset directories"
python - <<'PY'
from pathlib import Path
root=Path('/root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene')
print('[exists]', root, root.exists())
for name in ['threed_front_bedroom','threed_front_livingroom','threed_front_diningroom','3D-FUTURE-chatgpt']:
    p=root/name
    print('[dataset]', name, 'exists=', p.exists(), 'items=', len(list(p.iterdir())) if p.exists() else 'NA')
PY

echo "[smoke] checkpoint CPU load"
python - <<'PY'
from pathlib import Path
import torch
paths = [
'/root/RelationAwareInstructScene/repos/InstructScene/out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth',
'/root/RelationAwareInstructScene/repos/InstructScene/out/threedfront_objfeat_vqvae/objfeat_bounds.pkl',
'/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/bedroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth',
'/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/bedroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01999.pth',
'/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/livingroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth',
'/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/livingroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01459.pth',
'/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/diningroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth',
'/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/diningroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01239.pth',
]
for item in paths:
    p=Path(item)
    print('[file]', p, 'exists=', p.exists(), 'size=', p.stat().st_size if p.exists() else 'NA')
    if p.suffix == '.pth':
        obj=torch.load(p, map_location='cpu')
        if isinstance(obj, dict):
            print('[load]', p.name, 'keys=', list(obj.keys())[:8], 'nkeys=', len(obj))
        else:
            print('[load]', p.name, 'type=', type(obj).__name__)
PY

echo "[smoke] disk"
df -h / /root/autodl-tmp

echo "[smoke] PASS cpu/data/checkpoint smoke; GPU/raw 3D assets still required for full generation/mesh tests"
