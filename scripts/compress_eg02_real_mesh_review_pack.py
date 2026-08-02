#!/usr/bin/env python3
"""Compress EG-02 real-mesh PNG review images into a smaller JPG pack."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from PIL import Image


def convert_image(src: Path, dst: Path, max_width: int, quality: int) -> None:
    image = Image.open(src).convert("RGB")
    if image.width > max_width:
        new_height = round(image.height * (max_width / image.width))
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    image.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-width", type=int, default=1800)
    parser.add_argument("--quality", type=int, default=82)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    image_dir = output_dir / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    source_csv = input_dir / "eg02_human_review_sample_real_mesh_images.csv"
    rows = []
    with source_csv.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            png_rel = Path(row["image_or_view_path"])
            jpg_name = png_rel.with_suffix(".jpg").name
            convert_image(input_dir / png_rel, image_dir / jpg_name, args.max_width, args.quality)
            row["image_or_view_path"] = f"images/{jpg_name}"
            rows.append(row)

    with (output_dir / "eg02_human_review_sample_real_mesh_images.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest_path = input_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest:
            item["output"] = str(Path("images") / Path(item["output"]).with_suffix(".jpg").name)
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme = """# EG-02 Real Mesh Human Review Pack

Use `eg02_human_review_sample_real_mesh_images.csv` for annotation.

Each `image_or_view_path` points to one JPG in `images/`.
Each image contains three real 3D-FUTURE mesh views: isometric, top, and front.

Blue object = subject. Orange object = object/reference.
Fill only: human_label, missing_object, visibility_quality, annotator_id, notes.
"""
    (output_dir / "README_for_annotator.md").write_text(readme, encoding="utf-8")
    print(f"converted={len(rows)}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
