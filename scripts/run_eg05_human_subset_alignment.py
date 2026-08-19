#!/usr/bin/env python3
"""Run EG-05 independent evaluator on the EG-02 adjudicated human subset.

The final EG-02 annotation CSV contains the repaired subject/object coordinates
used during human review. This script converts those rows into the evaluator's
layout JSON schema, runs the independent evaluator, and compares binary
evaluator labels against the adjudicated human labels.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "evaluation" / "independent_relation_evaluator.py"
DEFAULT_LABELS = ROOT / "results" / "eurographics2027" / "eg02_human_review_v2_final" / "final_labels.csv"
DEFAULT_OUT = ROOT / "results" / "independent_eval" / "eg2027" / "eg05_human_subset_repair"


def load_evaluator():
    spec = importlib.util.spec_from_file_location("independent_relation_evaluator", EVALUATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_center(value: str) -> list[float]:
    return [float(x) for x in json.loads(value)]


def obj(index: int, category: str, center: list[float]) -> dict:
    return {
        "index": index,
        "category": category,
        "center": center,
        "size": [1.0, 1.0, 1.0],
        "yaw": 0.0,
    }


def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict[str, str]]]:
    layouts = []
    for row in rows:
        if not row["subject_index"] or not row["object_index"]:
            continue
        if not row["subject_center_xyz"] or not row["object_center_xyz"]:
            continue
        annotation_id = row["annotation_id"]
        subject_index = int(row["subject_index"])
        object_index = int(row["object_index"])
        layouts.append({
            "scene_id": annotation_id,
            "room_type": row["room_type"],
            "layout_variant": "collision_gated_floor_prior",
            "source_config_id": "floor_prior_max1.8_mesh_p2_close0.75_far1.6",
            "objects": [
                obj(subject_index, row["subject_class"], parse_center(row["subject_center_xyz"])),
                obj(object_index, row["object_class"], parse_center(row["object_center_xyz"])),
            ],
            "target_relations": [
                {
                    "relation_id": annotation_id,
                    "subject_class": row["subject_class"],
                    "predicate": row["predicate"],
                    "object_class": row["object_class"],
                }
            ],
        })
    included_ids = {layout["scene_id"] for layout in layouts}
    included_rows = [row for row in rows if row["annotation_id"] in included_ids]
    return layouts, included_rows


def binary_label(value: str) -> str | None:
    if value == "satisfied":
        return "satisfied"
    if value == "not_satisfied":
        return "not_satisfied"
    return None


def compare(per_relation: list[dict], human_rows: list[dict[str, str]]) -> tuple[list[dict], dict]:
    by_id = {row["annotation_id"]: row for row in human_rows}
    comparison = []
    counts = {
        "n_relations": 0,
        "binary_evaluable": 0,
        "not_judgable": 0,
        "tp": 0,
        "tn": 0,
        "fp": 0,
        "fn": 0,
    }
    by_room: dict[str, dict[str, int]] = {}
    by_predicate: dict[str, dict[str, int]] = {}

    for row in per_relation:
        human = by_id[str(row["relation_id"])]
        human_label = binary_label(human["final_label"])
        evaluator_label = "satisfied" if int(row["is_satisfied"]) else "not_satisfied"
        counts["n_relations"] += 1
        if human_label is None:
            counts["not_judgable"] += 1
            agreement = ""
        else:
            counts["binary_evaluable"] += 1
            agreement = int(human_label == evaluator_label)
            if human_label == "satisfied" and evaluator_label == "satisfied":
                counts["tp"] += 1
            elif human_label == "not_satisfied" and evaluator_label == "not_satisfied":
                counts["tn"] += 1
            elif human_label == "not_satisfied" and evaluator_label == "satisfied":
                counts["fp"] += 1
            elif human_label == "satisfied" and evaluator_label == "not_satisfied":
                counts["fn"] += 1

            for table, key in [(by_room, human["room_type"]), (by_predicate, human["predicate"])]:
                table.setdefault(key, {"n": 0, "agree": 0})
                table[key]["n"] += 1
                table[key]["agree"] += int(agreement)

        comparison.append({
            "annotation_id": row["relation_id"],
            "room_type": human["room_type"],
            "predicate": human["predicate"],
            "subject_class": human["subject_class"],
            "object_class": human["object_class"],
            "human_final_label": human["final_label"],
            "evaluator_label": evaluator_label,
            "agreement": agreement,
            "status": row["status"],
            "dx": row["dx"],
            "dy": row["dy"],
            "dz": row["dz"],
            "d_xz": row["d_xz"],
            "coord_rule_label_from_annotation": human["coord_rule_label"],
            "final_vs_coord": human["final_vs_coord"],
        })

    n = counts["binary_evaluable"]
    tp, tn, fp, fn = counts["tp"], counts["tn"], counts["fp"], counts["fn"]
    summary = {
        **counts,
        "accuracy": (tp + tn) / n if n else 0.0,
        "precision_satisfied": tp / (tp + fp) if tp + fp else 0.0,
        "recall_satisfied": tp / (tp + fn) if tp + fn else 0.0,
        "specificity_not_satisfied": tn / (tn + fp) if tn + fp else 0.0,
        "by_room": {k: {"n": v["n"], "accuracy": v["agree"] / v["n"]} for k, v in sorted(by_room.items())},
        "by_predicate": {k: {"n": v["n"], "accuracy": v["agree"] / v["n"]} for k, v in sorted(by_predicate.items())},
        "coordinate_convention": "eg2027-eg05-v1: behind dz<0; in_front_of dz>0",
    }
    return comparison, summary


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    with args.labels.open(newline="", encoding="utf-8") as handle:
        human_rows = list(csv.DictReader(handle))
    layouts, included_human_rows = convert_rows(human_rows)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    converted = args.output_dir / "human_subset_repair_layouts.json"
    converted.write_text(json.dumps({"layouts": layouts}, indent=2), encoding="utf-8")

    evaluator = load_evaluator()
    per_relation, per_scene, summary, audit = evaluator.evaluate(layouts)
    evaluator.write_csv(args.output_dir / "per_relation.csv", evaluator.PER_RELATION_FIELDS, per_relation)
    evaluator.write_csv(args.output_dir / "per_scene.csv", evaluator.PER_SCENE_FIELDS, per_scene)
    evaluator.write_csv(args.output_dir / "summary.csv", evaluator.SUMMARY_FIELDS, summary)
    audit.update({
        "run_id": "eg05_human_subset_repair",
        "input_path": str(converted),
        "human_label_path": str(args.labels),
        "n_human_rows": len(human_rows),
        "n_converted_rows": len(included_human_rows),
        "n_skipped_missing_pair_or_center": len(human_rows) - len(included_human_rows),
    })
    (args.output_dir / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")

    comparison, alignment_summary = compare(per_relation, included_human_rows)
    alignment_summary["n_source_human_rows"] = len(human_rows)
    alignment_summary["n_converted_rows"] = len(included_human_rows)
    alignment_summary["n_skipped_missing_pair_or_center"] = len(human_rows) - len(included_human_rows)
    write_csv(args.output_dir / "human_alignment.csv", comparison)
    (args.output_dir / "human_alignment_summary.json").write_text(
        json.dumps(alignment_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(alignment_summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
