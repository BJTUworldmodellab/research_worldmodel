#!/usr/bin/env python3
"""Rebuild the EG2027 paper tables from the frozen anonymous evidence package.

The script uses only the Python standard library.  It verifies table values,
dataset grain, variant coverage, denominators, per-object movement matching,
and the generic optimizer's per-object movement budget.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOMS = ("bedroom", "livingroom", "diningroom")
MAIN = "collision_gated_floor_prior"
RANDOMS = tuple(f"random_movement_matched_seed{seed}" for seed in range(3))
CONTROLS = ("baseline", *RANDOMS, "generic_relation_optimizer")
EPS = 1e-12
MOVE_EPS = 1e-6


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["room_type"], row["layout_variant"])].append(row)
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for key, members in grouped.items():
        relations = sum(int(row["n_relations"]) for row in members)
        satisfied = sum(int(row["n_satisfied"]) for row in members)
        output[key] = {
            "n_scenes": len(members),
            "n_relations": relations,
            "n_satisfied": satisfied,
            "n_missing": sum(int(row["n_missing"]) for row in members),
            "n_unsupported": sum(int(row["n_unsupported"]) for row in members),
            "accuracy": satisfied / relations if relations else 0.0,
        }
    return output


def duplicate_keys(rows: list[dict[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    duplicates = []
    for row in rows:
        key = (row["scene_id"], row["layout_variant"])
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def check_variant_coverage(
    rows: list[dict[str, str]], expected: set[str]
) -> list[str]:
    by_scene: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_scene[row["scene_id"]].add(row["layout_variant"])
    return [
        f"{scene}: variants={sorted(variants)}"
        for scene, variants in sorted(by_scene.items())
        if variants != expected
    ]


def overall(
    aggregates: dict[tuple[str, str], dict[str, Any]], variant: str
) -> dict[str, Any]:
    members = [aggregates[(room, variant)] for room in ROOMS]
    relations = sum(row["n_relations"] for row in members)
    satisfied = sum(row["n_satisfied"] for row in members)
    return {
        "n_scenes": sum(row["n_scenes"] for row in members),
        "n_relations": relations,
        "n_satisfied": satisfied,
        "n_missing": sum(row["n_missing"] for row in members),
        "n_unsupported": sum(row["n_unsupported"] for row in members),
        "accuracy": satisfied / relations,
    }


def verify_movement(layout_path: Path) -> dict[str, Any]:
    layouts = json.loads(layout_path.read_text(encoding="utf-8"))["layouts"]
    by_scene: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for layout in layouts:
        by_scene[layout["scene_id"]][layout["layout_variant"]] = layout

    random_comparisons = 0
    random_failures = 0
    random_max_abs_diff = 0.0
    generic_comparisons = 0
    generic_failures = 0
    generic_max_excess = 0.0
    coverage_errors: list[str] = []

    for scene_id, variants in sorted(by_scene.items()):
        required = {"baseline", MAIN, *RANDOMS, "generic_relation_optimizer"}
        if set(variants) != required:
            coverage_errors.append(f"{scene_id}: {sorted(variants)}")
            continue
        objects = {
            variant: {int(obj["index"]): obj for obj in layout["objects"]}
            for variant, layout in variants.items()
        }
        baseline_indices = set(objects["baseline"])
        if any(set(by_index) != baseline_indices for by_index in objects.values()):
            coverage_errors.append(f"{scene_id}: object-index coverage mismatch")
            continue
        for index in sorted(baseline_indices):
            origin = objects["baseline"][index]["center"]

            def distance(variant: str) -> float:
                center = objects[variant][index]["center"]
                return math.hypot(
                    float(center[0]) - float(origin[0]),
                    float(center[2]) - float(origin[2]),
                )

            main_distance = distance(MAIN)
            for variant in RANDOMS:
                delta = abs(distance(variant) - main_distance)
                random_max_abs_diff = max(random_max_abs_diff, delta)
                random_failures += delta > MOVE_EPS
                random_comparisons += 1
            excess = distance("generic_relation_optimizer") - main_distance
            generic_max_excess = max(generic_max_excess, excess)
            generic_failures += excess > MOVE_EPS
            generic_comparisons += 1

    return {
        "scenes": len(by_scene),
        "layouts": len(layouts),
        "coverage_errors": coverage_errors,
        "random_per_object_comparisons": random_comparisons,
        "random_magnitude_failures": random_failures,
        "random_max_abs_difference_m": random_max_abs_diff,
        "generic_per_object_comparisons": generic_comparisons,
        "generic_budget_failures": generic_failures,
        "generic_max_excess_m": generic_max_excess,
    }


def assert_close(errors: list[str], label: str, actual: float, expected: float) -> None:
    if abs(actual - expected) > EPS:
        errors.append(f"{label}: actual={actual!r}, expected={expected!r}")


def default_data_root(script: Path) -> Path:
    root = script.resolve().parents[1]
    packaged = root / "data"
    return packaged if packaged.exists() else root / "eg07_final_delivery_20260814"


def parse_args() -> argparse.Namespace:
    script = Path(__file__)
    root = script.resolve().parents[1]
    data_root = default_data_root(script)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=data_root)
    parser.add_argument(
        "--statistics",
        type=Path,
        default=(
            data_root / "stats" / "paired_statistics.json"
            if (data_root / "stats").exists()
            else root
            / "results"
            / "independent_eval"
            / "eg2027"
            / "eg08_paired_statistics_20260816"
            / "paired_statistics.json"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "output" / "reproduction",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = args.data_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    packaged_final = data_root / "final" / "final_metrics.json"
    repository_final = data_root / "final" / "eg07_final_metrics_20260814.json"
    paths = {
        "eg05_per_scene": data_root / "eg05" / "per_scene.csv",
        "eg06_per_scene": data_root / "eg06" / "per_scene.csv",
        "augmented_layouts": data_root / "eg06" / "eg06_augmented_layouts.json",
        "final_metrics": packaged_final if packaged_final.exists() else repository_final,
        "paired_statistics": args.statistics.resolve(),
    }
    for label, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"missing {label}: {path}")

    eg05_rows = read_csv(paths["eg05_per_scene"])
    eg06_rows = read_csv(paths["eg06_per_scene"])
    frozen = json.loads(paths["final_metrics"].read_text(encoding="utf-8"))
    stats = json.loads(paths["paired_statistics"].read_text(encoding="utf-8"))
    eg05 = aggregate(eg05_rows)
    eg06 = aggregate(eg06_rows)
    errors: list[str] = []

    eg05_duplicates = duplicate_keys(eg05_rows)
    eg06_duplicates = duplicate_keys(eg06_rows)
    if eg05_duplicates:
        errors.append(f"EG05 duplicate scene/variant keys: {len(eg05_duplicates)}")
    if eg06_duplicates:
        errors.append(f"EG06 duplicate scene/variant keys: {len(eg06_duplicates)}")
    eg05_coverage = check_variant_coverage(eg05_rows, {"baseline", MAIN})
    eg06_coverage = check_variant_coverage(eg06_rows, {MAIN, *CONTROLS})
    if eg05_coverage:
        errors.append(f"EG05 variant coverage errors: {len(eg05_coverage)}")
    if eg06_coverage:
        errors.append(f"EG06 variant coverage errors: {len(eg06_coverage)}")

    main_rows: list[dict[str, Any]] = []
    for room in ROOMS:
        baseline = eg05[(room, "baseline")]
        main = eg05[(room, MAIN)]
        main_rows.append(
            {
                "room": room,
                "n_scenes": baseline["n_scenes"],
                "n_relations": baseline["n_relations"],
                "baseline_satisfied": baseline["n_satisfied"],
                "main_satisfied": main["n_satisfied"],
                "baseline_accuracy": baseline["accuracy"],
                "main_accuracy": main["accuracy"],
                "gain": main["accuracy"] - baseline["accuracy"],
                "missing": baseline["n_missing"],
                "unsupported": baseline["n_unsupported"],
            }
        )
    baseline_overall = overall(eg05, "baseline")
    main_overall = overall(eg05, MAIN)
    main_rows.append(
        {
            "room": "overall",
            "n_scenes": baseline_overall["n_scenes"],
            "n_relations": baseline_overall["n_relations"],
            "baseline_satisfied": baseline_overall["n_satisfied"],
            "main_satisfied": main_overall["n_satisfied"],
            "baseline_accuracy": baseline_overall["accuracy"],
            "main_accuracy": main_overall["accuracy"],
            "gain": main_overall["accuracy"] - baseline_overall["accuracy"],
            "missing": baseline_overall["n_missing"],
            "unsupported": baseline_overall["n_unsupported"],
        }
    )

    assert_close(errors, "baseline overall", baseline_overall["accuracy"], frozen["eg05"]["relation_accuracy"]["baseline_overall"])
    assert_close(errors, "main overall", main_overall["accuracy"], frozen["eg05"]["relation_accuracy"]["main_overall"])
    for room in ROOMS:
        assert_close(errors, f"{room} baseline", eg05[(room, "baseline")]["accuracy"], frozen["eg05"]["relation_accuracy"]["baseline"][room])
        assert_close(errors, f"{room} main", eg05[(room, MAIN)]["accuracy"], frozen["eg05"]["relation_accuracy"]["main"][room])

    control_accuracy = {variant: overall(eg06, variant)["accuracy"] for variant in CONTROLS}
    random_mean = sum(control_accuracy[variant] for variant in RANDOMS) / len(RANDOMS)
    canonical = stats["canonical_eg06_ci"]
    control_rows: list[dict[str, Any]] = []
    for variant in ("baseline", *RANDOMS, "random_mean", "generic_relation_optimizer"):
        accuracy = random_mean if variant == "random_mean" else control_accuracy[variant]
        ci = canonical[variant]["relation_weighted_ci95"]
        gain = main_overall["accuracy"] - accuracy
        control_rows.append(
            {
                "control": variant,
                "accuracy": accuracy,
                "main_minus_control": gain,
                "ci95_low": ci[0],
                "ci95_high": ci[1],
                "claim_supported": ci[0] > 0,
            }
        )
        assert_close(errors, f"{variant} canonical gain", gain, canonical[variant]["relation_weighted_diff"])

    structural = frozen["structural"]
    gate_rows = [
        {
            "room": room,
            "repair_selected": structural["gate_decision_by_room"][room]["repair"],
            "baseline_fallback": structural["gate_decision_by_room"][room]["fallback_baseline"],
            "total": structural["scene_count_by_room"][room],
        }
        for room in ROOMS
    ]
    gate_rows.append(
        {
            "room": "overall",
            "repair_selected": structural["gate_decision"]["repair"],
            "baseline_fallback": structural["gate_decision"]["fallback_baseline"],
            "total": structural["scenes"],
        }
    )
    for row in gate_rows:
        if row["repair_selected"] + row["baseline_fallback"] != row["total"]:
            errors.append(f"gate accounting mismatch: {row}")

    movement = verify_movement(paths["augmented_layouts"])
    if movement["coverage_errors"]:
        errors.append(f"layout/object coverage errors: {len(movement['coverage_errors'])}")
    if movement["random_magnitude_failures"]:
        errors.append(f"random per-object movement failures: {movement['random_magnitude_failures']}")
    if movement["generic_budget_failures"]:
        errors.append(f"generic per-object movement-budget failures: {movement['generic_budget_failures']}")

    integrity = {
        "eg05_rows": len(eg05_rows),
        "eg06_rows": len(eg06_rows),
        "eg05_duplicate_keys": len(eg05_duplicates),
        "eg06_duplicate_keys": len(eg06_duplicates),
        "eg05_variant_coverage_errors": len(eg05_coverage),
        "eg06_variant_coverage_errors": len(eg06_coverage),
        "scene_count": baseline_overall["n_scenes"],
        "target_relations": baseline_overall["n_relations"],
        "missing_targets": baseline_overall["n_missing"],
        "unsupported_targets": baseline_overall["n_unsupported"],
    }
    payload = {
        "schema": "eg2027-eg13-reproduction-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "inputs": {label: {"path": path.relative_to(data_root).as_posix() if path.is_relative_to(data_root) else path.name, "sha256": sha256(path), "bytes": path.stat().st_size} for label, path in paths.items()},
        "integrity": integrity,
        "movement_fairness": movement,
        "main_table": main_rows,
        "controls_table": control_rows,
        "gate_table": gate_rows,
        "collision_pairs": {
            "baseline": structural["baseline_collision_pairs_total"],
            "selected_main": structural["chosen_main_collision_pairs_total"],
            "non_worsening": structural["chosen_main_collision_pairs_total"] <= structural["baseline_collision_pairs_total"],
        },
    }
    (output_dir / "reproduction.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(output_dir / "main_table.csv", main_rows)
    write_csv(output_dir / "controls_table.csv", control_rows)
    write_csv(output_dir / "gate_table.csv", gate_rows)
    markdown = [
        "# EG13 frozen-result reproduction",
        "",
        f"Status: **{payload['status']}**",
        "",
        f"Verified {integrity['scene_count']} scenes and {integrity['target_relations']} target relations.",
        f"Main relation accuracy: {main_overall['accuracy']:.6f}; movement-matched random mean: {random_mean:.6f}.",
        f"Primary gain: {(main_overall['accuracy'] - random_mean) * 100:.4f} percentage points; canonical 95% CI: [{canonical['random_mean']['relation_weighted_ci95'][0] * 100:.4f}, {canonical['random_mean']['relation_weighted_ci95'][1] * 100:.4f}] points.",
        f"Per-object random movement checks: {movement['random_per_object_comparisons']} comparisons, {movement['random_magnitude_failures']} failures.",
        f"Generic per-object budget checks: {movement['generic_per_object_comparisons']} comparisons, {movement['generic_budget_failures']} failures.",
        "",
        "The original-baseline and generic-optimizer confidence intervals include zero; no superiority claim is supported for those comparisons.",
    ]
    if errors:
        markdown.extend(["", "## Errors", "", *[f"- {error}" for error in errors]])
    (output_dir / "reproduction.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "output_dir": str(output_dir), "errors": errors}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
