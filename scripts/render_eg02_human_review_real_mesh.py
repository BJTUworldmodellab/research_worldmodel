#!/usr/bin/env python3
"""Render EG-02 human-review samples as real 3D-FUTURE mesh PNGs.

This script is intended to run on the AutoDL machine that has the 3D-FUTURE
asset directory and the experiment JSONs. It creates one multi-view PNG per
annotation row and writes an updated CSV with image paths.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pyrender
import trimesh


VIEW_W = 960
VIEW_H = 720
PANEL_GAP = 18
HEADER_H = 150


def exact_count(target: list, pred: list) -> int:
    pred_items = list(map(tuple, pred))
    total = 0
    for rel in map(tuple, target):
        if rel in pred_items:
            total += 1
            pred_items.remove(rel)
    return total


@lru_cache(maxsize=8)
def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_scene(data: dict, scene_id: str) -> dict:
    for scene in data.get("per_scene", []):
        if scene.get("scene_uid") == scene_id:
            return scene
    raise KeyError(f"scene not found: {scene_id}")


def raw_size_from_asset(asset_dir: Path) -> np.ndarray:
    bbox = np.load(asset_dir / "bbox_vertices.npy", mmap_mode="r")
    return np.array(
        [
            np.sqrt(np.sum((bbox[4] - bbox[0]) ** 2)) / 2,
            np.sqrt(np.sum((bbox[2] - bbox[0]) ** 2)) / 2,
            np.sqrt(np.sum((bbox[1] - bbox[0]) ** 2)) / 2,
        ],
        dtype=np.float64,
    )


def resolve_asset(asset_root: Path, asset_jid: str) -> Path:
    asset_dir = asset_root / asset_jid
    if (asset_dir / "raw_model.obj").exists():
        return asset_dir
    matches = [path for path in asset_root.iterdir() if path.name.startswith(asset_jid)]
    for path in matches:
        if (path / "raw_model.obj").exists():
            return path
    raise FileNotFoundError(f"missing raw_model.obj for {asset_jid}")


def load_mesh(asset_root: Path, asset_jid: str, box: dict) -> trimesh.Trimesh:
    asset_dir = resolve_asset(asset_root, asset_jid)
    mesh = trimesh.load(asset_dir / "raw_model.obj", force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(tuple(mesh.dump()))

    raw_size = raw_size_from_asset(asset_dir)
    target_size = np.array(box["size"], dtype=np.float64)
    mesh.vertices *= target_size / np.maximum(raw_size, 1e-6)
    mesh.vertices -= (mesh.bounds[0] + mesh.bounds[1]) / 2.0

    theta = float(box.get("angle", 0.0))
    rot = np.array(
        [
            [math.cos(theta), 0.0, -math.sin(theta)],
            [0.0, 1.0, 0.0],
            [math.sin(theta), 0.0, math.cos(theta)],
        ],
        dtype=np.float64,
    )
    mesh.vertices = mesh.vertices.dot(rot) + np.array(box["translation"], dtype=np.float64)
    return mesh


def boxes_for_mode(scene: dict, mode: str) -> tuple[list[dict], list[str | None]]:
    if mode == "before":
        return scene["layout_boxes"], scene.get("object_model_jids", [])
    boxes = json.loads(json.dumps(scene["repair_boxes"]))
    for repaired, original in zip(boxes, scene["layout_boxes"]):
        repaired["translation"][1] = original["translation"][1]
    return boxes, scene.get("repair_object_model_jids", scene.get("object_model_jids", []))


def bounds_for_meshes(meshes: list[trimesh.Trimesh]) -> tuple[np.ndarray, np.ndarray]:
    mins = np.vstack([mesh.bounds[0] for mesh in meshes])
    maxs = np.vstack([mesh.bounds[1] for mesh in meshes])
    return mins.min(axis=0), maxs.max(axis=0)


def look_at(eye: np.ndarray, target: np.ndarray) -> np.ndarray:
    forward = target - eye
    forward /= np.linalg.norm(forward)
    up = np.array([0.0, 1.0, 0.0])
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose


def material_for_box(box: dict, subject_index: str, object_index: str) -> pyrender.MetallicRoughnessMaterial:
    index = str(box.get("index", ""))
    if index == subject_index:
        color = [0.08, 0.32, 1.0, 1.0]
    elif index == object_index:
        color = [1.0, 0.50, 0.05, 1.0]
    else:
        color = [0.72, 0.76, 0.74, 1.0]
    return pyrender.MetallicRoughnessMaterial(
        baseColorFactor=color,
        metallicFactor=0.0,
        roughnessFactor=0.55,
    )


def make_arrow(start: list[float], end: list[float]) -> trimesh.Trimesh | None:
    s = np.array([start[0], start[1] + 0.18, start[2]], dtype=np.float64)
    e = np.array([end[0], end[1] + 0.18, end[2]], dtype=np.float64)
    if np.linalg.norm(e - s) < 0.08:
        return None
    return trimesh.creation.cylinder(radius=0.03, segment=np.vstack([s, e]), sections=20)


def build_scene(
    asset_root: Path,
    scene: dict,
    mode: str,
    subject_index: str,
    object_index: str,
) -> tuple[pyrender.Scene, list[trimesh.Trimesh], list[str]]:
    boxes, ids = boxes_for_mode(scene, mode)
    render_scene = pyrender.Scene(bg_color=[248, 250, 252, 255], ambient_light=[0.45, 0.47, 0.50])
    meshes: list[trimesh.Trimesh] = []
    skipped: list[str] = []

    for box, jid in zip(boxes, ids):
        if not jid:
            continue
        try:
            mesh = load_mesh(asset_root, jid, box)
            meshes.append(mesh)
            render_scene.add(pyrender.Mesh.from_trimesh(mesh, material=material_for_box(box, subject_index, object_index), smooth=False))
        except Exception as exc:
            skipped.append(f"{box.get('index')}:{box.get('class_name')}:{exc}")

    if not meshes:
        raise RuntimeError("no renderable meshes")

    bmin, bmax = bounds_for_meshes(meshes)
    center = (bmin + bmax) / 2.0
    span = np.maximum(bmax - bmin, 1.0)
    floor_size = max(float(span[0]), float(span[2])) * 1.45
    floor = trimesh.creation.box(extents=[floor_size, 0.025, floor_size])
    floor.apply_translation([center[0], -0.035, center[2]])
    floor.visual = trimesh.visual.ColorVisuals(floor, vertex_colors=[226, 232, 240, 255])
    render_scene.add(pyrender.Mesh.from_trimesh(floor, smooth=False))

    boxes_by_index = {str(box.get("index")): box for box in boxes}
    subject_box = boxes_by_index.get(subject_index)
    object_box = boxes_by_index.get(object_index)
    if subject_box and object_box:
        arrow = make_arrow(object_box["translation"], subject_box["translation"])
        if arrow is not None:
            mat = pyrender.MetallicRoughnessMaterial(
                baseColorFactor=[0.04, 0.12, 0.22, 1.0],
                metallicFactor=0.0,
                roughnessFactor=0.3,
            )
            render_scene.add(pyrender.Mesh.from_trimesh(arrow, material=mat, smooth=False))

    radius = max(float(span[0]), float(span[2]), 3.0)
    lights = [
        center + np.array([-radius * 0.5, radius * 1.9, radius * 0.8]),
        center + np.array([radius * 0.9, radius * 1.2, -radius * 0.7]),
    ]
    for light_eye in lights:
        render_scene.add(
            pyrender.DirectionalLight(color=np.ones(3), intensity=3.5),
            pose=look_at(light_eye, center),
        )
    return render_scene, meshes, skipped


def add_camera(render_scene: pyrender.Scene, meshes: list[trimesh.Trimesh], view: str) -> None:
    bmin, bmax = bounds_for_meshes(meshes)
    center = (bmin + bmax) / 2.0
    span = np.maximum(bmax - bmin, 1.0)
    radius = max(float(span[0]), float(span[2]), 3.0)
    if view == "top":
        eye = center + np.array([0.001, radius * 1.85, 0.001])
        target = center
        camera = pyrender.OrthographicCamera(xmag=radius * 0.75, ymag=radius * 0.75)
    elif view == "front":
        eye = center + np.array([0.0, radius * 0.52, -radius * 1.25])
        target = center + np.array([0.0, 0.22, 0.0])
        camera = pyrender.PerspectiveCamera(yfov=np.deg2rad(38.0), aspectRatio=VIEW_W / VIEW_H)
    else:
        eye = center + np.array([radius * 0.82, radius * 0.70, radius * 0.92])
        target = center + np.array([0.0, 0.20, 0.0])
        camera = pyrender.PerspectiveCamera(yfov=np.deg2rad(38.0), aspectRatio=VIEW_W / VIEW_H)
    render_scene.add(camera, pose=look_at(eye, target))


def render_view(asset_root: Path, scene: dict, row: dict, mode: str, view: str) -> tuple[Image.Image, list[str]]:
    render_scene, meshes, skipped = build_scene(
        asset_root,
        scene,
        mode,
        str(row.get("subject_index", "")),
        str(row.get("object_index", "")),
    )
    add_camera(render_scene, meshes, view)
    renderer = pyrender.OffscreenRenderer(viewport_width=VIEW_W, viewport_height=VIEW_H)
    color, _depth = renderer.render(render_scene, flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL)
    renderer.delete()
    return Image.fromarray(color).convert("RGB"), skipped


def safe_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def render_annotation(asset_root: Path, data_root: Path, row: dict, output: Path, mode: str) -> dict:
    data = load_json(str(data_root / row["source_json"]))
    scene = find_scene(data, row["scene_id"])
    views = ["iso", "top", "front"]
    images = []
    skipped_all: list[str] = []
    for view in views:
        image, skipped = render_view(asset_root, scene, row, mode, view)
        images.append((view, image))
        skipped_all.extend(skipped)

    canvas = Image.new("RGB", (VIEW_W * 3 + PANEL_GAP * 2, VIEW_H + HEADER_H), (248, 250, 252))
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        sub_font = ImageFont.truetype("DejaVuSans.ttf", 22)
        tag_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
    except Exception:
        title_font = sub_font = tag_font = None

    title = f'{row["annotation_id"]} | {row["subject_class"]} {row["predicate"]} {row["object_class"]}'
    draw.text((24, 16), title, fill=(15, 23, 42), font=title_font)
    draw.text((24, 64), safe_text(row.get("source_text", ""), 180), fill=(51, 65, 85), font=sub_font)
    draw.text((24, 104), "Blue = subject, orange = object, dark arrow = object -> subject. Views: isometric / top / front.", fill=(71, 85, 105), font=sub_font)

    for i, (view, image) in enumerate(images):
        x = i * (VIEW_W + PANEL_GAP)
        canvas.paste(image, (x, HEADER_H))
        draw.text((x + 22, HEADER_H + 20), view.upper(), fill=(15, 23, 42), font=tag_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    return {
        "annotation_id": row["annotation_id"],
        "output": str(output),
        "skipped_meshes": len(skipped_all),
        "skipped_mesh_notes": skipped_all[:10],
        "before_score": exact_count(scene["selected_relations"], scene["layout_relations"]),
        "after_score": exact_count(scene["selected_relations"], scene["repair_relations"]),
        "n_relations": len(scene["selected_relations"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--updated-csv", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--mode", choices=["after", "before"], default="after")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    sample = Path(args.sample)
    data_root = Path(args.data_root)
    asset_root = Path(args.asset_root)
    output_dir = Path(args.output_dir)
    with sample.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if args.limit:
        rows = rows[: args.limit]

    manifest = []
    for index, row in enumerate(rows, start=1):
        rel_image = f"images/{row['annotation_id']}.png"
        print(f"[{index}/{len(rows)}] render {row['annotation_id']}")
        item = render_annotation(asset_root, data_root, row, output_dir / rel_image, args.mode)
        row["image_or_view_path"] = rel_image
        manifest.append(item)

    output_dir.mkdir(parents=True, exist_ok=True)
    with Path(args.updated_csv).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"rendered={len(rows)}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
