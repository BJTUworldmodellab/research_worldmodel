import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "floor_prior_remote"
TABLE_DIR = ROOT / "results" / "tables"


def parse_meta(path):
    name = path.name
    if name.startswith("bedroom_"):
        room = "bedroom"
    elif name.startswith("livingroom_"):
        room = "livingroom"
    elif name.startswith("diningroom_"):
        room = "diningroom"
    else:
        room = "unknown"
    variant = name.split("_relation_aware_parsed_", 1)[1].rsplit("_eval_cfg", 1)[0]
    return room, variant


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    count = 0
    for rel in map(tuple, target):
        if rel in pred:
            count += 1
            pred.remove(rel)
    return count


def per_relation_rows(paths):
    rows = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        room, variant = parse_meta(path)
        totals = Counter()
        base = Counter()
        repair = Counter()
        predicate_types = data.get("predicate_types") or []
        for scene in data["per_scene"]:
            for rel in scene["selected_relations"]:
                pred_id = int(rel[1])
                key = predicate_types[pred_id] if pred_id < len(predicate_types) else str(pred_id)
                totals[key] += 1
                if tuple(rel) in map(tuple, scene["layout_relations"]):
                    base[key] += 1
                if tuple(rel) in map(tuple, scene["repair_relations"]):
                    repair[key] += 1
        for key in sorted(totals):
            rows.append({
                "room": room,
                "variant": variant,
                "relation": key,
                "n": totals[key],
                "baseline_acc": base[key] / max(totals[key], 1),
                "repair_acc": repair[key] / max(totals[key], 1),
                "gain": repair[key] / max(totals[key], 1) - base[key] / max(totals[key], 1),
            })
    return rows


def support_rows(paths):
    rows = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        room, variant = parse_meta(path)
        objects = 0
        changed_y = 0
        max_abs_y_delta = 0.0
        moved = []
        for scene in data["per_scene"]:
            for before, after in zip(scene["layout_boxes"], scene["repair_boxes"]):
                objects += 1
                dy = abs(float(after["translation"][1]) - float(before["translation"][1]))
                max_abs_y_delta = max(max_abs_y_delta, dy)
                if dy > 1e-6:
                    changed_y += 1
                dx = float(after["translation"][0]) - float(before["translation"][0])
                dz = float(after["translation"][2]) - float(before["translation"][2])
                moved.append((dx * dx + dz * dz) ** 0.5)
        moved_sorted = sorted(moved)
        q95 = moved_sorted[int(0.95 * (len(moved_sorted) - 1))] if moved_sorted else 0.0
        rows.append({
            "room": room,
            "variant": variant,
            "objects": objects,
            "y_changed": changed_y,
            "y_changed_rate": changed_y / max(objects, 1),
            "max_abs_y_delta": max_abs_y_delta,
            "mean_xz_displacement": sum(moved) / max(len(moved), 1),
            "p95_xz_displacement": q95,
        })
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(IN_DIR.glob("*_relation_aware_parsed_*mesh*_eval_cfg1.0_1.0.json"))
    write_csv(TABLE_DIR / "floor_prior_per_relation_breakdown.csv", per_relation_rows(paths))
    write_csv(TABLE_DIR / "floor_prior_support_movement_diagnostics.csv", support_rows(paths))
    print(TABLE_DIR / "floor_prior_per_relation_breakdown.csv")
    print(TABLE_DIR / "floor_prior_support_movement_diagnostics.csv")


if __name__ == "__main__":
    main()
