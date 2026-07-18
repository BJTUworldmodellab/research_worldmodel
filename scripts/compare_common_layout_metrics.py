#!/usr/bin/env python3
import argparse
import csv
import json
import math
from pathlib import Path


def yaw_from_quat(q):
    if not q or len(q) != 4:
        return 0.0
    x, y, z, w = [float(v) for v in q]
    return math.atan2(2.0 * (w * y + x * z), 1.0 - 2.0 * (y * y + z * z))


def rect_corners(cx, cz, sx, sz, angle):
    hx, hz = abs(float(sx)) / 2.0, abs(float(sz)) / 2.0
    ca, sa = math.cos(float(angle)), math.sin(float(angle))
    pts = [(-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)]
    return [(cx + x * ca - z * sa, cz + x * sa + z * ca) for x, z in pts]


def polygon_area(poly):
    if len(poly) < 3:
        return 0.0
    total = 0.0
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[(i + 1) % len(poly)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def inside(p, edge_start, edge_end):
    x, y = p
    x1, y1 = edge_start
    x2, y2 = edge_end
    return (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) >= -1e-9


def line_intersection(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-12:
        return p2
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return px, py


def polygon_clip(subject, clip):
    output = list(subject)
    for i in range(len(clip)):
        input_list = output
        output = []
        if not input_list:
            break
        a = clip[i]
        b = clip[(i + 1) % len(clip)]
        s = input_list[-1]
        for e in input_list:
            if inside(e, a, b):
                if not inside(s, a, b):
                    output.append(line_intersection(s, e, a, b))
                output.append(e)
            elif inside(s, a, b):
                output.append(line_intersection(s, e, a, b))
            s = e
    return output


def box_polygon(box):
    return rect_corners(
        box["translation"][0],
        box["translation"][2],
        box["size"][0],
        box["size"][2],
        box.get("angle", 0.0),
    )


def summarize_boxes(boxes, bounds=None, source_quality=None):
    boxes = [b for b in boxes if b.get("size") and b.get("translation")]
    n = len(boxes)
    polys = [box_polygon(b) for b in boxes]
    areas = [polygon_area(p) for p in polys]
    total_area = sum(areas)
    overlap_area = 0.0
    overlap_pairs = 0
    relation_counts = {"left_right": 0, "front_behind": 0}
    pairs = n * (n - 1) // 2

    for i in range(n):
        xi, zi = boxes[i]["translation"][0], boxes[i]["translation"][2]
        for j in range(i + 1, n):
            inter = polygon_clip(polys[i], polys[j])
            area = polygon_area(inter)
            if area > 1e-6:
                overlap_pairs += 1
                overlap_area += area
            xj, zj = boxes[j]["translation"][0], boxes[j]["translation"][2]
            if abs(xi - xj) >= abs(zi - zj):
                relation_counts["left_right"] += 1
            else:
                relation_counts["front_behind"] += 1

    oob = None
    if bounds:
        xs = [float(p[0]) for p in bounds]
        zs = [float(p[2]) for p in bounds]
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)
        oob_count = 0
        for b in boxes:
            x, z = b["translation"][0], b["translation"][2]
            oob_count += int(x < min_x or x > max_x or z < min_z or z > max_z)
        oob = oob_count / max(n, 1)
    elif source_quality and source_quality.get("object_count"):
        oob = source_quality.get("out_of_bounds_centers", 0) / max(source_quality.get("object_count", 1), 1)

    return {
        "object_count": n,
        "nonempty": int(n > 0),
        "footprint_area": total_area,
        "overlap_pairs": overlap_pairs,
        "overlap_area": overlap_area,
        "overlap_ratio": overlap_area / max(total_area, 1e-9),
        "overlap_pairs_per_scene": overlap_pairs,
        "out_of_bounds_center_rate": oob,
        "relation_pair_count": pairs,
        "relation_pair_density": pairs / max(n * (n - 1) / 2, 1) if n >= 2 else 0.0,
        "left_right_pairs": relation_counts["left_right"],
        "front_behind_pairs": relation_counts["front_behind"],
    }


def aggregate(name, rows):
    numeric_keys = [
        "object_count",
        "nonempty",
        "overlap_pairs_per_scene",
        "overlap_ratio",
        "out_of_bounds_center_rate",
        "relation_pair_count",
        "relation_pair_density",
        "left_right_pairs",
        "front_behind_pairs",
    ]
    out = {"method": name, "scene_count": len(rows)}
    for key in numeric_keys:
        vals = [r[key] for r in rows if r.get(key) is not None]
        out[key] = sum(vals) / len(vals) if vals else None
    out["nonempty_rate"] = out.pop("nonempty")
    return out


def load_original(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    baseline = []
    repaired = []
    for scene in data.get("per_scene", []):
        baseline.append(summarize_boxes(scene.get("layout_boxes", []), source_quality=scene.get("layout_quality")))
        repaired.append(summarize_boxes(scene.get("repair_boxes", []), source_quality=scene.get("repair_quality")))
    return baseline, repaired


def load_respace_dir(path):
    rows = []
    for p in sorted(Path(path).rglob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        boxes = []
        for idx, obj in enumerate(data.get("objects", [])):
            pos = obj.get("pos") or [0.0, 0.0, 0.0]
            size = obj.get("size") or obj.get("sampled_asset_size") or [0.0, 0.0, 0.0]
            boxes.append({
                "index": idx,
                "class_name": obj.get("prompt") or obj.get("desc") or "object",
                "translation": [float(pos[0]), float(pos[1]), float(pos[2])],
                "size": [float(size[0]), float(size[1]), float(size[2])],
                "angle": yaw_from_quat(obj.get("rot")),
            })
        rows.append(summarize_boxes(boxes, bounds=data.get("bounds_bottom")))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-json", required=True)
    parser.add_argument("--qwen-full-dir", required=True)
    parser.add_argument("--qwen-add-dir", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args()

    original_baseline, original_repaired = load_original(args.original_json)
    qwen_full = load_respace_dir(args.qwen_full_dir)
    qwen_add = load_respace_dir(args.qwen_add_dir)

    summaries = [
        aggregate("original_baseline_layout", original_baseline),
        aggregate("original_repaired_floor_prior", original_repaired),
        aggregate("qwen_respace_full_scene", qwen_full),
        aggregate("qwen_respace_add_only", qwen_add),
    ]

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"summaries": summaries}, indent=2), encoding="utf-8")

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)

    print(json.dumps({"summaries": summaries, "out_csv": str(out_csv), "out_json": str(out_json)}, indent=2))


if __name__ == "__main__":
    main()
