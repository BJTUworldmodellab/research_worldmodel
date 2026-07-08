import json
import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh
import pyrender


REPO = Path("/root/RelationAwareInstructScene/repos/InstructScene")
ASSET_ROOT = Path("/root/RelationAwareInstructScene/raw_data/3D-FRONT/3D-FUTURE-model")
OUT = Path("/root/RelationAwareInstructScene/outputs/real_mesh_showcase_v3")

PICKS = {
    "bedroom": {
        "idx": 145,
        "json": "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999/relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.json",
    },
    "livingroom": {
        "idx": 16,
        "json": "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/livingroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01459/relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.json",
    },
    "diningroom": {
        "idx": 136,
        "json": "/root/autodl-tmp/RelationAwareInstructScene/instructscene_out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01239/relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.json",
    },
}


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    total = 0
    for rel in map(tuple, target):
        if rel in pred:
            total += 1
            pred.remove(rel)
    return total


def improved_relations(scene):
    selected = [tuple(x) for x in scene["selected_relations"]]
    before = set(map(tuple, scene["layout_relations"]))
    after = set(map(tuple, scene["repair_relations"]))
    improved = [rel for rel in selected if rel not in before and rel in after]
    return improved or selected[:1]


def raw_size_from_asset(asset_dir):
    bbox = np.load(asset_dir / "bbox_vertices.npy", mmap_mode="r")
    return np.array([
        np.sqrt(np.sum((bbox[4] - bbox[0]) ** 2)) / 2,
        np.sqrt(np.sum((bbox[2] - bbox[0]) ** 2)) / 2,
        np.sqrt(np.sum((bbox[1] - bbox[0]) ** 2)) / 2,
    ])


def load_mesh(asset_jid, box):
    asset_dir = ASSET_ROOT / asset_jid
    mesh_path = asset_dir / "raw_model.obj"
    if not mesh_path.exists():
        matches = [p for p in ASSET_ROOT.iterdir() if p.name.startswith(asset_jid)]
        if matches:
            asset_dir = matches[0]
            mesh_path = asset_dir / "raw_model.obj"
    mesh = trimesh.load(mesh_path, force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(tuple(mesh.dump()))
    raw_size = raw_size_from_asset(asset_dir)
    target_size = np.array(box["size"], dtype=np.float64)
    scale = target_size / np.maximum(raw_size, 1e-6)
    mesh.vertices *= scale
    mesh.vertices -= (mesh.bounds[0] + mesh.bounds[1]) / 2.0
    theta = float(box["angle"])
    rot = np.array([
        [math.cos(theta), 0.0, -math.sin(theta)],
        [0.0, 1.0, 0.0],
        [math.sin(theta), 0.0, math.cos(theta)],
    ])
    mesh.vertices = mesh.vertices.dot(rot) + np.array(box["translation"])
    return mesh


def boxes_for_mode(scene_record, mode):
    if mode != "after":
        return scene_record["layout_boxes"]
    boxes = json.loads(json.dumps(scene_record["repair_boxes"]))
    layout_boxes = scene_record["layout_boxes"]
    for repaired, original in zip(boxes, layout_boxes):
        repaired["translation"][1] = original["translation"][1]
    return boxes


def find_pair(boxes, rel):
    subj, _pred, obj = rel
    subj_boxes = [b for b in boxes if int(b["class_id"]) == int(subj)]
    obj_boxes = [b for b in boxes if int(b["class_id"]) == int(obj)]
    best = None
    best_d = 1e12
    for a in subj_boxes:
        for b in obj_boxes:
            dx = a["translation"][0] - b["translation"][0]
            dz = a["translation"][2] - b["translation"][2]
            d = dx * dx + dz * dz
            if d < best_d:
                best_d = d
                best = (a, b)
    return best


def make_arrow_mesh(start, end):
    s = np.array([start[0], 1.25, start[2]], dtype=np.float64)
    e = np.array([end[0], 1.25, end[2]], dtype=np.float64)
    if np.linalg.norm(e - s) < 0.1:
        return None
    shaft = trimesh.creation.cylinder(radius=0.035, segment=np.vstack([s, e]), sections=24)
    return shaft


def look_at(eye, target):
    eye = np.array(eye, dtype=np.float64)
    target = np.array(target, dtype=np.float64)
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


def bounds_for_meshes(meshes):
    mins = np.vstack([m.bounds[0] for m in meshes])
    maxs = np.vstack([m.bounds[1] for m in meshes])
    return mins.min(axis=0), maxs.max(axis=0)


def mesh_collision_pairs(meshes):
    try:
        manager = trimesh.collision.CollisionManager()
        for idx, mesh in enumerate(meshes):
            if mesh is not None and len(mesh.vertices) > 0 and len(mesh.faces) > 0:
                manager.add_object(str(idx), mesh)
        _hit, pairs = manager.in_collision_internal(return_names=True)
        return len(pairs)
    except Exception as exc:
        print(f"mesh collision unavailable: {exc}")
        return None


def render_layout(scene_record, mode, out_path):
    boxes = boxes_for_mode(scene_record, mode)
    ids = scene_record["repair_object_model_jids"] if mode == "after" else scene_record["object_model_jids"]
    meshes = []
    render_scene = pyrender.Scene(bg_color=[8, 10, 14, 255], ambient_light=[0.18, 0.20, 0.24])
    for box, jid in zip(boxes, ids):
        if jid is None:
            continue
        try:
            mesh = load_mesh(jid, box)
        except Exception as exc:
            print(f"skip mesh {jid}: {exc}")
            continue
        meshes.append(mesh)
        try:
            pr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=False)
        except Exception:
            mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=[190, 205, 200, 255])
            pr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=False)
        render_scene.add(pr_mesh)

    if not meshes:
        raise RuntimeError("no renderable meshes")
    collision_pairs = mesh_collision_pairs(meshes)
    bmin, bmax = bounds_for_meshes(meshes)
    center = (bmin + bmax) / 2
    span = np.maximum(bmax - bmin, 1.0)
    floor_size = max(float(span[0]), float(span[2])) * 1.36
    floor = trimesh.creation.box(extents=[floor_size, 0.035, floor_size])
    floor.apply_translation([center[0], -0.035, center[2]])
    floor.visual = trimesh.visual.ColorVisuals(floor, vertex_colors=[42, 50, 54, 255])
    render_scene.add(pyrender.Mesh.from_trimesh(floor, smooth=False))

    for rel in improved_relations(scene_record):
        pair = find_pair(boxes, rel)
        if pair:
            arrow = make_arrow_mesh(pair[1]["translation"], pair[0]["translation"])
            if arrow is not None:
                mat = pyrender.MetallicRoughnessMaterial(
                    baseColorFactor=[0.05, 1.0, 0.78, 1.0],
                    emissiveFactor=[0.0, 0.75, 0.55],
                    metallicFactor=0.0,
                    roughnessFactor=0.25,
                )
                render_scene.add(pyrender.Mesh.from_trimesh(arrow, material=mat, smooth=False))

    radius = max(float(span[0]), float(span[2]), 3.0)
    eye = center + np.array([radius * 0.72, radius * 0.62, radius * 0.88])
    target = center + np.array([0.0, 0.25, 0.0])
    camera = pyrender.PerspectiveCamera(yfov=np.deg2rad(40.0), aspectRatio=16 / 10)
    render_scene.add(camera, pose=look_at(eye, target))

    light_pose = look_at(center + np.array([-radius * 0.5, radius * 1.8, radius * 0.7]), center)
    render_scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=4.8), pose=light_pose)
    render_scene.add(pyrender.SpotLight(color=np.array([0.55, 0.95, 1.0]), intensity=28.0, innerConeAngle=0.2, outerConeAngle=0.9), pose=look_at(center + np.array([radius * 0.55, radius * 1.2, -radius]), center))

    renderer = pyrender.OffscreenRenderer(viewport_width=1600, viewport_height=1000)
    color, _depth = renderer.render(render_scene, flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL)
    renderer.delete()
    img = Image.fromarray(color)
    img.save(out_path)
    return out_path, collision_pairs


def annotate_pair(before_path, after_path, scene_record, room, idx, out_path, before_pairs, after_pairs):
    before = Image.open(before_path).convert("RGB")
    after = Image.open(after_path).convert("RGB")
    w, h = before.size
    canvas = Image.new("RGB", (w * 2, h + 190), (8, 10, 14))
    canvas.paste(before, (0, 150))
    canvas.paste(after, (w, 150))
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        sub_font = ImageFont.truetype("DejaVuSans.ttf", 24)
        tag_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except Exception:
        title_font = sub_font = tag_font = None
    selected = scene_record["selected_relations"]
    bscore = exact_count(selected, scene_record["layout_relations"])
    ascore = exact_count(selected, scene_record["repair_relations"])
    bpairs = before_pairs if before_pairs is not None else scene_record["layout_mesh_collision"]["collision_pairs"]
    apairs = after_pairs if after_pairs is not None else scene_record["repair_mesh_collision"]["collision_pairs"]
    title = f"{room} #{idx} real 3D-FUTURE mesh render"
    draw.text((34, 20), title, fill=(235, 255, 250), font=title_font)
    prompt = scene_record["text"]
    if len(prompt) > 170:
        prompt = prompt[:167] + "..."
    draw.text((36, 82), prompt, fill=(174, 195, 190), font=sub_font)
    draw.text((44, 158), f"BEFORE  relation {bscore}/{len(selected)}  mesh pairs {bpairs}", fill=(255, 184, 112), font=tag_font)
    draw.text((w + 44, 158), f"AFTER  relation {ascore}/{len(selected)}  mesh pairs {apairs}  y-fixed", fill=(80, 255, 205), font=tag_font)
    canvas.save(out_path)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for room, spec in PICKS.items():
        idx = spec["idx"]
        data = json.loads(Path(spec["json"]).read_text(encoding="utf-8"))
        scene_record = data["per_scene"][idx]
        before = OUT / f"{room}_{idx:04d}_before.png"
        after = OUT / f"{room}_{idx:04d}_after.png"
        combined = OUT / f"{room}_{idx:04d}_comparison.png"
        print(f"render {room} {idx} before")
        _before_path, before_pairs = render_layout(scene_record, "before", before)
        print(f"render {room} {idx} after")
        _after_path, after_pairs = render_layout(scene_record, "after", after)
        annotate_pair(before, after, scene_record, room, idx, combined, before_pairs, after_pairs)
        manifest.append({
            "room": room,
            "idx": idx,
            "text": scene_record["text"],
            "before": str(before),
            "after": str(after),
            "combined": str(combined),
            "beforeScore": exact_count(scene_record["selected_relations"], scene_record["layout_relations"]),
            "afterScore": exact_count(scene_record["selected_relations"], scene_record["repair_relations"]),
            "total": len(scene_record["selected_relations"]),
            "beforePairs": before_pairs if before_pairs is not None else scene_record["layout_mesh_collision"]["collision_pairs"],
            "afterPairs": after_pairs if after_pairs is not None else scene_record["repair_mesh_collision"]["collision_pairs"],
            "heightFix": "repair moves x/z only and preserves each object's original y",
        })
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(OUT / "manifest.json")


if __name__ == "__main__":
    main()
