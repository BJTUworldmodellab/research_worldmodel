import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "floor_prior_remote"
OUT = ROOT / "results" / "tables" / "floor_prior_gated_results.csv"
MESH_OUT = ROOT / "results" / "tables" / "floor_prior_mesh_results.csv"


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    count = 0
    for rel in map(tuple, target):
        if rel in pred:
            count += 1
            pred.remove(rel)
    return count


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


def summarize(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    room, variant = parse_meta(path)
    rel_total = 0
    base_correct = 0
    repair_correct = 0
    gated_correct = 0
    base_pairs = 0
    repair_pairs = 0
    gated_pairs = 0
    base_total_pairs = 0
    repair_total_pairs = 0
    gated_total_pairs = 0
    fallback_scenes = 0
    mesh_unavailable_scenes = 0
    evaluated = 0
    for scene in data["per_scene"]:
        selected = scene["selected_relations"]
        rel_total += len(selected)
        base_rel = scene["layout_relations"]
        repair_rel = scene["repair_relations"]
        base_correct += exact_count(selected, base_rel)
        repair_correct += exact_count(selected, repair_rel)
        layout_mesh = scene.get("layout_mesh_collision") or {}
        repair_mesh = scene.get("repair_mesh_collision") or {}
        if not (layout_mesh.get("available") and repair_mesh.get("available")):
            # Collision-gated means fail closed: an unverified repair cannot
            # replace the original layout when either mesh result is missing.
            gated_rel = base_rel
            gated_mesh = layout_mesh
            fallback_scenes += 1
            mesh_unavailable_scenes += 1
        elif repair_mesh["collision_pairs"] <= layout_mesh["collision_pairs"]:
            gated_rel = repair_rel
            gated_mesh = repair_mesh
            evaluated += 1
        else:
            gated_rel = base_rel
            gated_mesh = layout_mesh
            fallback_scenes += 1
            evaluated += 1
        gated_correct += exact_count(selected, gated_rel)
        base_pairs += layout_mesh.get("collision_pairs", 0)
        repair_pairs += repair_mesh.get("collision_pairs", 0)
        gated_pairs += gated_mesh.get("collision_pairs", 0)
        base_total_pairs += layout_mesh.get("total_pairs", 0)
        repair_total_pairs += repair_mesh.get("total_pairs", 0)
        gated_total_pairs += gated_mesh.get("total_pairs", 0)
    return {
        "room": room,
        "variant": variant,
        "rel_total": rel_total,
        "baseline_acc": base_correct / max(rel_total, 1),
        "repair_acc": repair_correct / max(rel_total, 1),
        "gated_acc": gated_correct / max(rel_total, 1),
        "repair_gain": repair_correct / max(rel_total, 1) - base_correct / max(rel_total, 1),
        "gated_gain": gated_correct / max(rel_total, 1) - base_correct / max(rel_total, 1),
        "baseline_mesh_pair_rate": base_pairs / max(base_total_pairs, 1),
        "repair_mesh_pair_rate": repair_pairs / max(repair_total_pairs, 1),
        "gated_mesh_pair_rate": gated_pairs / max(gated_total_pairs, 1),
        "fallback_scenes": fallback_scenes,
        "mesh_unavailable_scenes": mesh_unavailable_scenes,
        "mesh_scenes_evaluated": evaluated,
        "source": str(path),
    }


def main():
    paths = sorted(IN_DIR.glob("*relation_aware_parsed_*mesh*_eval_cfg1.0_1.0.json"))
    rows = [summarize(path) for path in paths]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with OUT.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        mesh_rows = []
        for row in rows:
            mesh_rows.append({
                "room": row["room"],
                "variant": row["variant"],
                "baseline_mesh_pair_rate": row["baseline_mesh_pair_rate"],
                "repair_mesh_pair_rate": row["repair_mesh_pair_rate"],
                "gated_mesh_pair_rate": row["gated_mesh_pair_rate"],
                "repair_mesh_delta": row["repair_mesh_pair_rate"] - row["baseline_mesh_pair_rate"],
                "gated_mesh_delta": row["gated_mesh_pair_rate"] - row["baseline_mesh_pair_rate"],
                "repair_gain": row["repair_gain"],
                "gated_gain": row["gated_gain"],
                "fallback_scenes": row["fallback_scenes"],
                "mesh_unavailable_scenes": row["mesh_unavailable_scenes"],
                "mesh_scenes_evaluated": row["mesh_scenes_evaluated"],
            })
        with MESH_OUT.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(mesh_rows[0].keys()))
            writer.writeheader()
            writer.writerows(mesh_rows)
    print(OUT)
    print(MESH_OUT)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
