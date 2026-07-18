#!/usr/bin/env python
import argparse
import os
import zipfile
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO = "chenguolin/InstructScene_dataset"
ROOT = Path(os.environ.get("RELATION_ROOT", "/root/RelationAwareInstructScene"))
TMP = Path(os.environ.get("RELATION_TMP_ROOT", "/root/autodl-tmp/RelationAwareInstructScene"))
CACHE = TMP / "hf_cache"

CHECKPOINTS = {
    "threedfront_objfeat_vqvae_epoch_01999.pth": ROOT / "repos/InstructScene/out/threedfront_objfeat_vqvae/checkpoints/epoch_01999.pth",
    "objfeat_bounds.pkl": ROOT / "repos/InstructScene/out/threedfront_objfeat_vqvae/objfeat_bounds.pkl",
    "bedroom_sg2scdiffusion_objfeat_epoch_01999.pth": TMP / "instructscene_out/bedroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth",
    "bedroom_sgdiffusion_vq_objfeat_epoch_01999.pth": TMP / "instructscene_out/bedroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01999.pth",
    "livingroom_sg2scdiffusion_objfeat_epoch_01999.pth": TMP / "instructscene_out/livingroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth",
    "livingroom_sgdiffusion_vq_objfeat_epoch_01459.pth": TMP / "instructscene_out/livingroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01459.pth",
    "diningroom_sg2scdiffusion_objfeat_epoch_01999.pth": TMP / "instructscene_out/diningroom_sg2scdiffusion_objfeat/checkpoints/epoch_01999.pth",
    "diningroom_sgdiffusion_vq_objfeat_epoch_01239.pth": TMP / "instructscene_out/diningroom_sgdiffusion_vq_objfeat/checkpoints/epoch_01239.pth",
}

DATASETS = {
    "InstructScene.zip": TMP / "datasets",
    "3D-FRONT.zip": ROOT / "raw_data",
}


def download(filename: str) -> Path:
    print(f"[download] {filename}", flush=True)
    return Path(
        hf_hub_download(
            repo_id=REPO,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(CACHE),
            resume_download=True,
        )
    )


def link_or_copy(src: Path, dst: Path, overwrite: bool = False):
    src = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        if not overwrite:
            print(f"[skip] exists {dst}")
            return
        dst.unlink()
    try:
        os.link(src, dst)
        print(f"[link] {src} -> {dst}")
    except OSError:
        import shutil

        shutil.copy2(src, dst)
        print(f"[copy] {src} -> {dst}")


def unzip(src: Path, dst_dir: Path):
    src = src.resolve()
    dst_dir.mkdir(parents=True, exist_ok=True)
    marker = dst_dir / f".{src.name}.unzipped"
    if marker.exists():
        print(f"[skip] already unzipped {src.name} into {dst_dir}")
        return
    print(f"[unzip] {src} -> {dst_dir}", flush=True)
    with zipfile.ZipFile(src) as zf:
        zf.extractall(dst_dir)
    marker.write_text("ok\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoints", action="store_true")
    parser.add_argument("--dataset", choices=["none", "instructscene", "front", "all"], default="none")
    parser.add_argument("--no-unzip", action="store_true")
    parser.add_argument("--repair-links", action="store_true")
    args = parser.parse_args()

    if args.checkpoints or args.repair_links:
        for filename, dst in CHECKPOINTS.items():
            src = download(filename)
            link_or_copy(src, dst, overwrite=args.repair_links)

    dataset_names = []
    if args.dataset in ("instructscene", "all"):
        dataset_names.append("InstructScene.zip")
    if args.dataset in ("front", "all"):
        dataset_names.append("3D-FRONT.zip")
    for filename in dataset_names:
        src = download(filename)
        target_dir = DATASETS[filename]
        if args.no_unzip:
            link_or_copy(src, target_dir / filename)
        else:
            unzip(src, target_dir)


if __name__ == "__main__":
    main()
