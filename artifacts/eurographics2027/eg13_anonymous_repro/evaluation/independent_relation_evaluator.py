#!/usr/bin/env python3
"""Independent relation evaluator for the Eurographics 2027 workflow.

The evaluator follows `evaluation/independent_protocol.md` and deliberately
does not import repair, verifier, or candidate-scoring code from the optimizer.
It evaluates final layouts only.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any


DIRECTION_MARGIN = 0.05
CLOSE_DISTANCE = 0.75
FAR_DISTANCE = 1.60
VERTICAL_MARGIN = 0.05

SUPPORTED_PREDICATES = {
    "left": "left",
    "left of": "left",
    "right": "right",
    "right of": "right",
    "in front of": "in_front_of",
    "front": "in_front_of",
    "behind": "behind",
    "close to": "close_to",
    "near": "close_to",
    "close by": "close_to",
    "far from": "far_from",
    "above": "above",
    "below": "below",
}

OPPOSITES = {
    frozenset(["left", "right"]),
    frozenset(["in_front_of", "behind"]),
    frozenset(["above", "below"]),
    frozenset(["close_to", "far_from"]),
}

ALIASES = {
    "night stand": "nightstand",
    "bedside table": "nightstand",
    "bedside cabinet": "nightstand",
    "closet": "wardrobe",
    "cabinet wardrobe": "wardrobe",
    "lounge chair": "armchair",
    "single sofa": "armchair",
    "couch": "sofa",
    "tea table": "coffee table",
    "dinner table": "dining table",
    "television stand": "tv stand",
    "tv cabinet": "tv stand",
}

PER_RELATION_FIELDS = [
    "scene_id",
    "room_type",
    "layout_variant",
    "source_config_id",
    "relation_id",
    "subject_class",
    "object_class",
    "predicate",
    "subject_index",
    "object_index",
    "status",
    "is_satisfied",
    "failure_reason",
    "dx",
    "dy",
    "dz",
    "d_xz",
]

PER_SCENE_FIELDS = [
    "scene_id",
    "room_type",
    "layout_variant",
    "source_config_id",
    "n_relations",
    "n_evaluated",
    "n_satisfied",
    "n_missing",
    "n_unsupported",
    "relation_accuracy",
    "conditional_accuracy",
    "has_conflicting_targets",
]

SUMMARY_FIELDS = [
    "layout_variant",
    "source_config_id",
    "room_type",
    "n_scenes",
    "n_relations",
    "relation_accuracy",
    "conditional_accuracy",
    "missing_rate",
    "unsupported_rate",
]


@dataclass(frozen=True)
class Obj:
    index: int
    category: str
    center: tuple[float, float, float]
    size: tuple[float, float, float] | None = None
    yaw: float | None = None


@dataclass(frozen=True)
class Relation:
    relation_id: str
    subject_class: str
    predicate: str
    object_class: str


def normalize_label(label: str) -> str:
    normalized = " ".join(label.lower().replace("_", " ").replace("-", " ").split())
    return ALIASES.get(normalized, normalized)


def normalize_predicate(predicate: str) -> str | None:
    normalized = " ".join(predicate.lower().replace("_", " ").replace("-", " ").split())
    return SUPPORTED_PREDICATES.get(normalized)


def as_obj(raw: dict[str, Any]) -> Obj:
    center = raw.get("center", raw.get("translation"))
    if center is None:
        raise ValueError(f"object {raw!r} is missing center/translation")
    size = raw.get("size")
    return Obj(
        index=int(raw.get("index", raw.get("id"))),
        category=str(raw.get("category", raw.get("label", raw.get("class", "")))),
        center=(float(center[0]), float(center[1]), float(center[2])),
        size=tuple(float(v) for v in size) if size is not None else None,
        yaw=float(raw["yaw"]) if "yaw" in raw and raw["yaw"] is not None else None,
    )


def as_relation(raw: dict[str, Any], fallback_id: int) -> Relation:
    return Relation(
        relation_id=str(raw.get("relation_id", raw.get("id", fallback_id))),
        subject_class=str(raw.get("subject_class", raw.get("subject", ""))),
        predicate=str(raw.get("predicate", raw.get("relation", ""))),
        object_class=str(raw.get("object_class", raw.get("object", ""))),
    )


def load_input(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if "layouts" in data:
        return list(data["layouts"])
    if "scenes" in data:
        return list(data["scenes"])
    raise ValueError("input JSON must be a list or contain `layouts`/`scenes`")


def choose_pair_from_baseline(objects: list[Obj], relation: Relation) -> tuple[int | None, int | None, str]:
    subject_class = normalize_label(relation.subject_class)
    object_class = normalize_label(relation.object_class)
    subjects = [obj for obj in objects if normalize_label(obj.category) == subject_class]
    objects_ = [obj for obj in objects if normalize_label(obj.category) == object_class]

    if not subjects and not objects_:
        return None, None, "missing_both"
    if not subjects:
        return None, None, "missing_subject"
    if not objects_:
        return None, None, "missing_object"

    def key(pair: tuple[Obj, Obj]) -> tuple[float, int, int]:
        s, o = pair
        dx = s.center[0] - o.center[0]
        dz = s.center[2] - o.center[2]
        return (dx * dx + dz * dz, s.index, o.index)

    subject, object_ = min(((s, o) for s in subjects for o in objects_), key=key)
    return subject.index, object_.index, "evaluated"


def relation_satisfied(predicate: str, subject: Obj, object_: Obj) -> tuple[bool, dict[str, float]]:
    dx = subject.center[0] - object_.center[0]
    dy = subject.center[1] - object_.center[1]
    dz = subject.center[2] - object_.center[2]
    d_xz = math.sqrt(dx * dx + dz * dz)
    values = {"dx": dx, "dy": dy, "dz": dz, "d_xz": d_xz}

    if predicate == "left":
        return dx < -DIRECTION_MARGIN, values
    if predicate == "right":
        return dx > DIRECTION_MARGIN, values
    if predicate == "in_front_of":
        return dz > DIRECTION_MARGIN, values
    if predicate == "behind":
        return dz < -DIRECTION_MARGIN, values
    if predicate == "close_to":
        return d_xz <= CLOSE_DISTANCE, values
    if predicate == "far_from":
        return d_xz >= FAR_DISTANCE, values
    if predicate == "above":
        return dy > VERTICAL_MARGIN, values
    if predicate == "below":
        return dy < -VERTICAL_MARGIN, values
    raise ValueError(f"unsupported normalized predicate: {predicate}")


def detect_conflicts(relations: list[Relation], frozen_pairs: dict[str, tuple[int | None, int | None, str]]) -> bool:
    by_pair: dict[tuple[int | None, int | None], set[str]] = {}
    for relation in relations:
        subject_idx, object_idx, status = frozen_pairs[relation.relation_id]
        if status != "evaluated":
            continue
        predicate = normalize_predicate(relation.predicate)
        if predicate is None:
            continue
        key = (subject_idx, object_idx)
        by_pair.setdefault(key, set()).add(predicate)

    for predicates in by_pair.values():
        for opposite in OPPOSITES:
            if opposite.issubset(predicates):
                return True
    return False


def evaluate_layout(
    layout: dict[str, Any],
    relations: list[Relation],
    frozen_pairs: dict[str, tuple[int | None, int | None, str]],
    has_conflicting_targets: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    objects = [as_obj(raw) for raw in layout["objects"]]
    by_index = {obj.index: obj for obj in objects}
    scene_id = str(layout["scene_id"])
    room_type = str(layout["room_type"])
    layout_variant = str(layout["layout_variant"])
    source_config_id = str(layout.get("source_config_id", "unknown"))

    rows = []
    for relation in relations:
        predicate = normalize_predicate(relation.predicate)
        subject_idx, object_idx, match_status = frozen_pairs[relation.relation_id]

        status = match_status
        satisfied = False
        failure_reason = ""
        values = {"dx": "", "dy": "", "dz": "", "d_xz": ""}

        if predicate is None:
            status = "unsupported_predicate"
            failure_reason = "unsupported_predicate"
        elif match_status != "evaluated":
            failure_reason = match_status
        elif subject_idx not in by_index or object_idx not in by_index:
            status = "missing_matched_instance"
            failure_reason = "matched_instance_absent_in_variant"
        else:
            satisfied, values = relation_satisfied(predicate, by_index[subject_idx], by_index[object_idx])
            failure_reason = "" if satisfied else "predicate_failed"

        rows.append({
            "scene_id": scene_id,
            "room_type": room_type,
            "layout_variant": layout_variant,
            "source_config_id": source_config_id,
            "relation_id": relation.relation_id,
            "subject_class": normalize_label(relation.subject_class),
            "object_class": normalize_label(relation.object_class),
            "predicate": relation.predicate,
            "subject_index": "" if subject_idx is None else subject_idx,
            "object_index": "" if object_idx is None else object_idx,
            "status": status,
            "is_satisfied": int(satisfied),
            "failure_reason": failure_reason,
            "dx": values["dx"],
            "dy": values["dy"],
            "dz": values["dz"],
            "d_xz": values["d_xz"],
        })

    n_relations = len(rows)
    n_evaluated = sum(1 for row in rows if row["status"] == "evaluated")
    n_satisfied = sum(int(row["is_satisfied"]) for row in rows)
    n_missing = sum(1 for row in rows if str(row["status"]).startswith("missing"))
    n_unsupported = sum(1 for row in rows if row["status"] == "unsupported_predicate")
    scene_row = {
        "scene_id": scene_id,
        "room_type": room_type,
        "layout_variant": layout_variant,
        "source_config_id": source_config_id,
        "n_relations": n_relations,
        "n_evaluated": n_evaluated,
        "n_satisfied": n_satisfied,
        "n_missing": n_missing,
        "n_unsupported": n_unsupported,
        "relation_accuracy": n_satisfied / n_relations if n_relations else 0.0,
        "conditional_accuracy": n_satisfied / n_evaluated if n_evaluated else 0.0,
        "has_conflicting_targets": int(has_conflicting_targets),
    }
    return rows, scene_row


def evaluate(layouts: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for layout in layouts:
        grouped.setdefault(str(layout["scene_id"]), []).append(layout)

    per_relation: list[dict[str, Any]] = []
    per_scene: list[dict[str, Any]] = []
    missing_baseline_scenes: list[str] = []

    for scene_id, scene_layouts in sorted(grouped.items()):
        baseline = next((layout for layout in scene_layouts if layout.get("layout_variant") == "baseline"), None)
        if baseline is None:
            missing_baseline_scenes.append(scene_id)
            baseline = scene_layouts[0]

        relations = [
            as_relation(raw, idx)
            for idx, raw in enumerate(baseline.get("target_relations", []))
        ]
        baseline_objects = [as_obj(raw) for raw in baseline["objects"]]
        frozen_pairs = {
            relation.relation_id: choose_pair_from_baseline(baseline_objects, relation)
            for relation in relations
        }
        has_conflicting_targets = detect_conflicts(relations, frozen_pairs)

        for layout in sorted(scene_layouts, key=lambda item: str(item.get("layout_variant", ""))):
            rows, scene_row = evaluate_layout(layout, relations, frozen_pairs, has_conflicting_targets)
            per_relation.extend(rows)
            per_scene.append(scene_row)

    summary = summarize(per_scene)
    audit = {
        "protocol": "eg2027-eg05-v1",
        "evaluator": "evaluation/independent_relation_evaluator.py",
        "independence_rule": {
            "imports_repair_or_optimizer_modules": False,
            "forbidden_imports": [
                "scripts/compute_gated_floorprior.py",
                "scripts/summarize_floorprior_results.py",
                "scripts/sync_parallel_floorprior_results.py",
                "results/relation_aware_generate_sg.py",
                "src/ablation/repairers.py",
            ],
        },
        "thresholds": {
            "direction_margin": DIRECTION_MARGIN,
            "close_distance": CLOSE_DISTANCE,
            "far_distance": FAR_DISTANCE,
            "vertical_margin": VERTICAL_MARGIN,
        },
        "missing_baseline_scenes": missing_baseline_scenes,
    }
    return per_relation, per_scene, summary, audit


def summarize(per_scene: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in per_scene:
        key = (row["layout_variant"], row["source_config_id"], row["room_type"])
        groups.setdefault(key, []).append(row)

    summary_rows = []
    for (layout_variant, source_config_id, room_type), rows in sorted(groups.items()):
        n_scenes = len(rows)
        n_relations = sum(int(row["n_relations"]) for row in rows)
        n_evaluated = sum(int(row["n_evaluated"]) for row in rows)
        n_satisfied = sum(int(row["n_satisfied"]) for row in rows)
        n_missing = sum(int(row["n_missing"]) for row in rows)
        n_unsupported = sum(int(row["n_unsupported"]) for row in rows)
        summary_rows.append({
            "layout_variant": layout_variant,
            "source_config_id": source_config_id,
            "room_type": room_type,
            "n_scenes": n_scenes,
            "n_relations": n_relations,
            "relation_accuracy": n_satisfied / n_relations if n_relations else 0.0,
            "conditional_accuracy": n_satisfied / n_evaluated if n_evaluated else 0.0,
            "missing_rate": n_missing / n_relations if n_relations else 0.0,
            "unsupported_rate": n_unsupported / n_relations if n_relations else 0.0,
        })
    return summary_rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input layout JSON.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Output directory.")
    parser.add_argument("--run-id", default=None, help="Optional run id for audit metadata.")
    args = parser.parse_args()

    layouts = load_input(args.input)
    per_relation, per_scene, summary, audit = evaluate(layouts)
    audit.update({
        "run_id": args.run_id or args.output_dir.name,
        "input_path": str(args.input),
        "input_sha256": file_sha256(args.input),
        "n_layouts": len(layouts),
        "n_per_relation_rows": len(per_relation),
        "n_per_scene_rows": len(per_scene),
    })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "per_relation.csv", PER_RELATION_FIELDS, per_relation)
    write_csv(args.output_dir / "per_scene.csv", PER_SCENE_FIELDS, per_scene)
    write_csv(args.output_dir / "summary.csv", SUMMARY_FIELDS, summary)
    (args.output_dir / "audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {args.output_dir}")


if __name__ == "__main__":
    main()
