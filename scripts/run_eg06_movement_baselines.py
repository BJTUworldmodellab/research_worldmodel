#!/usr/bin/env python3
"""Generate EG-06 movement-matched baselines and evaluate them.

This script expects an evaluator-layout JSON with a `baseline` layout and the
frozen `collision_gated_floor_prior` layout for each scene. It derives per-object
XZ movement budgets from the frozen main method, then creates:

- `random_movement_matched_seed{N}` baselines;
- `generic_relation_optimizer` baseline.

All generated layouts are evaluated by the EG-05 independent evaluator.
"""

from __future__ import annotations

import argparse
import copy
import csv
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "evaluation" / "independent_relation_evaluator.py"
DEFAULT_INPUT = ROOT / "evaluation" / "fixtures" / "eg06_movement_baseline_fixture.json"
DEFAULT_OUT = ROOT / "results" / "independent_eval" / "eg2027" / "eg06_movement_baseline_fixture"
MAIN_VARIANT = "collision_gated_floor_prior"
MAIN_CONFIG = "floor_prior_max1.8_mesh_p2_close0.75_far1.6"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("independent_relation_evaluator", EVALUATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def object_map(layout: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(obj["index"]): obj for obj in layout["objects"]}


def movement_budgets(baseline: dict[str, Any], main: dict[str, Any]) -> dict[int, float]:
    base = object_map(baseline)
    repair = object_map(main)
    budgets = {}
    for idx, base_obj in base.items():
        if idx not in repair:
            budgets[idx] = 0.0
            continue
        b = base_obj["center"]
        r = repair[idx]["center"]
        dx = float(r[0]) - float(b[0])
        dz = float(r[2]) - float(b[2])
        budgets[idx] = math.sqrt(dx * dx + dz * dz)
    return budgets


def clone_with_variant(layout: dict[str, Any], variant: str, config: str) -> dict[str, Any]:
    cloned = copy.deepcopy(layout)
    cloned["layout_variant"] = variant
    cloned["source_config_id"] = config
    return cloned


def apply_random(layout: dict[str, Any], budgets: dict[int, float], seed: int) -> dict[str, Any]:
    rng = random.Random(f"{layout['scene_id']}:{seed}")
    out = clone_with_variant(layout, f"random_movement_matched_seed{seed}", f"eg06_random_seed{seed}")
    for obj in out["objects"]:
        budget = budgets.get(int(obj["index"]), 0.0)
        angle = rng.uniform(0.0, math.tau)
        obj["center"][0] = float(obj["center"][0]) + math.cos(angle) * budget
        obj["center"][2] = float(obj["center"][2]) + math.sin(angle) * budget
    return out


def normalized_pair(evaluator, baseline: dict[str, Any], relation: dict[str, Any]):
    objects = [evaluator.as_obj(raw) for raw in baseline["objects"]]
    rel = evaluator.as_relation(relation, 0)
    return evaluator.choose_pair_from_baseline(objects, rel)


def move_toward_relation(evaluator, layout: dict[str, Any], relation: dict[str, Any], budgets: dict[int, float]) -> None:
    subject_idx, object_idx, status = normalized_pair(evaluator, layout, relation)
    predicate = evaluator.normalize_predicate(relation["predicate"])
    if status != "evaluated" or predicate is None or subject_idx is None or object_idx is None:
        return

    by_idx = object_map(layout)
    subject = by_idx[subject_idx]
    object_ = by_idx[object_idx]
    budget = budgets.get(subject_idx, 0.0)
    if budget <= 0:
        return

    sx, sy, sz = [float(v) for v in subject["center"]]
    ox, oy, oz = [float(v) for v in object_["center"]]
    dx = sx - ox
    dz = sz - oz
    d_xz = math.sqrt(dx * dx + dz * dz)
    margin = evaluator.DIRECTION_MARGIN

    target_dx = dx
    target_dz = dz
    if predicate == "left" and not dx < -margin:
        target_dx = -margin * 1.5
    elif predicate == "right" and not dx > margin:
        target_dx = margin * 1.5
    elif predicate == "behind" and not dz < -margin:
        target_dz = -margin * 1.5
    elif predicate == "in_front_of" and not dz > margin:
        target_dz = margin * 1.5
    elif predicate == "close_to" and d_xz > evaluator.CLOSE_DISTANCE:
        scale = evaluator.CLOSE_DISTANCE / max(d_xz, 1e-9)
        target_dx = dx * scale
        target_dz = dz * scale
    elif predicate == "far_from" and d_xz < evaluator.FAR_DISTANCE:
        if d_xz < 1e-9:
            target_dx = evaluator.FAR_DISTANCE
            target_dz = 0.0
        else:
            scale = evaluator.FAR_DISTANCE / d_xz
            target_dx = dx * scale
            target_dz = dz * scale
    else:
        return

    desired_move = (target_dx - dx, target_dz - dz)
    desired_norm = math.sqrt(desired_move[0] ** 2 + desired_move[1] ** 2)
    if desired_norm > budget and desired_norm > 0:
        desired_move = (desired_move[0] / desired_norm * budget, desired_move[1] / desired_norm * budget)

    subject["center"][0] = sx + desired_move[0]
    subject["center"][1] = sy
    subject["center"][2] = sz + desired_move[1]


def apply_generic_optimizer(evaluator, baseline: dict[str, Any], budgets: dict[int, float]) -> dict[str, Any]:
    out = clone_with_variant(baseline, "generic_relation_optimizer", "eg06_generic_budget_matched")
    for relation in baseline.get("target_relations", []):
        move_toward_relation(evaluator, out, relation, budgets)
    return out


def load_layouts(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["layouts"] if isinstance(data, dict) and "layouts" in data else data


def build_augmented_layouts(evaluator, layouts: list[dict[str, Any]], seeds: list[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_scene: dict[str, list[dict[str, Any]]] = {}
    for layout in layouts:
        by_scene.setdefault(str(layout["scene_id"]), []).append(layout)

    augmented = []
    movement_rows = []
    for scene_id, scene_layouts in sorted(by_scene.items()):
        baseline = next((x for x in scene_layouts if x["layout_variant"] == "baseline"), None)
        main = next((x for x in scene_layouts if x["layout_variant"] == MAIN_VARIANT), None)
        if baseline is None or main is None:
            continue
        budgets = movement_budgets(baseline, main)
        generated = [baseline, main]
        generated.extend(apply_random(baseline, budgets, seed) for seed in seeds)
        generated.append(apply_generic_optimizer(evaluator, baseline, budgets))
        augmented.extend(generated)
        movement_rows.extend(measure_movements(scene_id, baseline, generated, budgets))
    return augmented, movement_rows


def measure_movements(scene_id: str, baseline: dict[str, Any], layouts: list[dict[str, Any]], budgets: dict[int, float]) -> list[dict[str, Any]]:
    base = object_map(baseline)
    rows = []
    for layout in layouts:
        if layout["layout_variant"] == "baseline":
            continue
        total = 0.0
        max_move = 0.0
        changed = 0
        for obj in layout["objects"]:
            idx = int(obj["index"])
            if idx not in base:
                continue
            b = base[idx]["center"]
            c = obj["center"]
            move = math.sqrt((float(c[0]) - float(b[0])) ** 2 + (float(c[2]) - float(b[2])) ** 2)
            total += move
            max_move = max(max_move, move)
            changed += int(move > 1e-9)
        rows.append({
            "scene_id": scene_id,
            "layout_variant": layout["layout_variant"],
            "source_config_id": layout["source_config_id"],
            "n_objects": len(layout["objects"]),
            "changed_objects": changed,
            "total_xz_movement": total,
            "max_xz_movement": max_move,
            "budget_total": sum(budgets.values()),
            "budget_max": max(budgets.values()) if budgets else 0.0,
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seeds", default="0,1,2")
    args = parser.parse_args()

    evaluator = load_evaluator()
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    layouts = load_layouts(args.input)
    augmented, movement_rows = build_augmented_layouts(evaluator, layouts, seeds)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    augmented_path = args.output_dir / "eg06_augmented_layouts.json"
    augmented_path.write_text(json.dumps({"layouts": augmented}, indent=2), encoding="utf-8")
    write_csv(args.output_dir / "movement_audit.csv", movement_rows)

    per_relation, per_scene, summary, audit = evaluator.evaluate(augmented)
    evaluator.write_csv(args.output_dir / "per_relation.csv", evaluator.PER_RELATION_FIELDS, per_relation)
    evaluator.write_csv(args.output_dir / "per_scene.csv", evaluator.PER_SCENE_FIELDS, per_scene)
    evaluator.write_csv(args.output_dir / "summary.csv", evaluator.SUMMARY_FIELDS, summary)
    audit.update({
        "run_id": args.output_dir.name,
        "task": "EG-06 movement-matched baseline fixture",
        "input_path": str(args.input),
        "augmented_layout_path": str(augmented_path),
        "seeds": seeds,
        "baselines": ["random_movement_matched", "generic_relation_optimizer"],
        "note": "Fixture run only; full 531-scene EG-06 requires EG-07 normalized layout export.",
    })
    (args.output_dir / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {args.output_dir}")


if __name__ == "__main__":
    main()
