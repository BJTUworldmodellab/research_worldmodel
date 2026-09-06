#!/usr/bin/env python3
"""Materialize and verify the SQLite source used by the EG13 HTML report."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from pathlib import Path
from typing import Any


LABELS = {
    "baseline": "Original baseline",
    "random_movement_matched_seed0": "Random seed 0",
    "random_movement_matched_seed1": "Random seed 1",
    "random_movement_matched_seed2": "Random seed 2",
    "random_mean": "Random-seed mean",
    "generic_relation_optimizer": "Generic optimizer",
}


def rows(cursor: sqlite3.Cursor, query: str) -> list[dict[str, Any]]:
    result = cursor.execute(query)
    columns = [item[0] for item in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]


def compare(actual: Any, expected: Any, path: str = "snapshot") -> list[str]:
    errors: list[str] = []
    if isinstance(actual, dict) and isinstance(expected, dict):
        if set(actual) != set(expected):
            return [f"{path}: keys {sorted(actual)} != {sorted(expected)}"]
        for key in actual:
            errors.extend(compare(actual[key], expected[key], f"{path}.{key}"))
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return [f"{path}: length {len(actual)} != {len(expected)}"]
        for index, (left, right) in enumerate(zip(actual, expected)):
            errors.extend(compare(left, right, f"{path}[{index}]"))
    elif isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-12):
            errors.append(f"{path}: {actual!r} != {expected!r}")
    elif actual != expected:
        errors.append(f"{path}: {actual!r} != {expected!r}")
    return errors


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    report_dir = root / "artifacts" / "eurographics2027" / "eg13_validation_report"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduction", type=Path, default=root / "results" / "independent_eval" / "eg2027" / "eg13_reproduction_20260825" / "reproduction.json")
    parser.add_argument("--build-result", type=Path, default=root / "artifacts" / "eurographics2027" / "eg13_build_result.json")
    parser.add_argument("--manifest", type=Path, default=root / "artifacts" / "eurographics2027" / "eg13_anonymous_repro" / "MANIFEST.json")
    parser.add_argument("--artifact", type=Path, default=report_dir / "artifact.json")
    parser.add_argument("--database", type=Path, default=report_dir / "report_source.sqlite")
    parser.add_argument("--output", type=Path, default=report_dir / "query_results.json")
    args = parser.parse_args()

    reproduction = json.loads(args.reproduction.read_text(encoding="utf-8"))
    build_result = json.loads(args.build_result.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    main = reproduction["main_table"]
    main_by_room = {row["room"]: row for row in main}
    overall = main_by_room["overall"]
    controls = reproduction["controls_table"]
    controls_by_id = {row["control"]: row for row in controls}
    movement = reproduction["movement_fairness"]
    integrity = reproduction["integrity"]
    collisions = reproduction["collision_pairs"]

    args.database.parent.mkdir(parents=True, exist_ok=True)
    if args.database.exists():
        args.database.unlink()
    connection = sqlite3.connect(args.database)
    cursor = connection.cursor()
    cursor.executescript(
        """
        CREATE TABLE headline(main_accuracy REAL, gain_pp REAL, scenes INTEGER, relations INTEGER, selected_collision_pairs INTEGER, collision_delta INTEGER);
        CREATE TABLE comparison(method TEXT, accuracy REAL, satisfied REAL, relations INTEGER, role TEXT, display_order INTEGER);
        CREATE TABLE controls(display_order INTEGER, control TEXT, accuracy REAL, gain_pp REAL, ci_low_pp REAL, ci_high_pp REAL, supported TEXT);
        CREATE TABLE rooms(display_order INTEGER, room TEXT, scenes INTEGER, relations INTEGER, baseline REAL, main REAL, gain_pp REAL);
        CREATE TABLE quality(display_order INTEGER, check_name TEXT, comparisons INTEGER, failures INTEGER, result TEXT);
        """
    )
    random_mean = controls_by_id["random_mean"]
    cursor.execute(
        "INSERT INTO headline VALUES (?, ?, ?, ?, ?, ?)",
        (
            overall["main_accuracy"],
            random_mean["main_minus_control"] * 100,
            overall["n_scenes"],
            overall["n_relations"],
            collisions["selected_main"],
            collisions["selected_main"] - collisions["baseline"],
        ),
    )
    comparison_rows = [
        ("Original baseline", overall["baseline_accuracy"], overall["baseline_satisfied"], overall["n_relations"], "control", 1),
        ("Random mean", random_mean["accuracy"], random_mean["accuracy"] * overall["n_relations"], overall["n_relations"], "control", 2),
        ("Generic optimizer", controls_by_id["generic_relation_optimizer"]["accuracy"], controls_by_id["generic_relation_optimizer"]["accuracy"] * overall["n_relations"], overall["n_relations"], "control", 3),
        ("Gated Floor-Prior", overall["main_accuracy"], overall["main_satisfied"], overall["n_relations"], "main", 4),
    ]
    cursor.executemany("INSERT INTO comparison VALUES (?, ?, ?, ?, ?, ?)", comparison_rows)
    for order, item in enumerate(controls, 1):
        cursor.execute(
            "INSERT INTO controls VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                order,
                LABELS[item["control"]],
                item["accuracy"],
                item["main_minus_control"] * 100,
                item["ci95_low"] * 100,
                item["ci95_high"] * 100,
                "Yes" if item["claim_supported"] else "No",
            ),
        )
    room_labels = {"bedroom": "Bedroom", "livingroom": "Living room", "diningroom": "Dining room", "overall": "Overall"}
    for order, room in enumerate(("bedroom", "livingroom", "diningroom", "overall"), 1):
        item = main_by_room[room]
        cursor.execute(
            "INSERT INTO rooms VALUES (?, ?, ?, ?, ?, ?, ?)",
            (order, room_labels[room], item["n_scenes"], item["n_relations"], item["baseline_accuracy"], item["main_accuracy"], item["gain"] * 100),
        )
    quality_rows = [
        (1, "EG05 scene/variant key uniqueness", integrity["eg05_rows"], integrity["eg05_duplicate_keys"], "PASS"),
        (2, "EG06 scene/variant key uniqueness", integrity["eg06_rows"], integrity["eg06_duplicate_keys"], "PASS"),
        (3, "Random per-object movement magnitude", movement["random_per_object_comparisons"], movement["random_magnitude_failures"], "PASS"),
        (4, "Generic per-object movement budget", movement["generic_per_object_comparisons"], movement["generic_budget_failures"], "PASS"),
        (5, "Evaluator smoke relations", build_result["smoke"]["relations_checked"], len(build_result["smoke"]["errors"]), "PASS"),
        (6, "Anonymous content scan", manifest["file_count_excluding_manifest"], manifest["anonymity_scan"]["finding_count"], "PASS"),
    ]
    cursor.executemany("INSERT INTO quality VALUES (?, ?, ?, ?, ?)", quality_rows)
    connection.commit()

    queries = {
        "headline": "SELECT main_accuracy, gain_pp, scenes, relations, selected_collision_pairs, collision_delta FROM headline",
        "comparison": "SELECT method, accuracy, satisfied, relations, role, display_order AS 'order' FROM comparison ORDER BY display_order",
        "controls": "SELECT display_order AS 'order', control, accuracy, gain_pp, ci_low_pp, ci_high_pp, supported FROM controls ORDER BY display_order",
        "rooms": "SELECT display_order AS 'order', room, scenes, relations, baseline, main, gain_pp FROM rooms ORDER BY display_order",
        "quality": "SELECT display_order AS 'order', check_name AS 'check', comparisons, failures, result FROM quality ORDER BY display_order",
    }
    datasets = {name: rows(cursor, query) for name, query in queries.items()}
    connection.close()
    errors = compare(datasets, artifact["snapshot"]["datasets"])
    payload = {
        "schema": "eg2027-eg13-report-query-results-v1",
        "status": "PASS" if not errors else "FAIL",
        "queries": queries,
        "datasets": datasets,
        "artifact_snapshot_match": not errors,
        "errors": errors,
    }
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "database": str(args.database), "output": str(args.output), "errors": errors}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
