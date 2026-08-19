#!/usr/bin/env python3
"""Check EG-06 fixture fairness and claim-readiness boundaries."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "results" / "independent_eval" / "eg2027" / "eg06_movement_baseline_fixture"
EPS = 1e-6


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"FAIL: {error}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()

    errors: list[str] = []
    required = [
        "audit.json",
        "eg06_augmented_layouts.json",
        "movement_audit.csv",
        "per_relation.csv",
        "per_scene.csv",
        "summary.csv",
    ]
    for name in required:
        if not (args.run_dir / name).exists():
            errors.append(f"missing output file: {name}")

    if errors:
        fail(errors)

    audit = json.loads((args.run_dir / "audit.json").read_text(encoding="utf-8"))
    if audit.get("note") != "Fixture run only; full 531-scene EG-06 requires EG-07 normalized layout export.":
        errors.append("audit must clearly mark fixture-only status")
    if audit.get("protocol") != "eg2027-eg05-v1":
        errors.append("audit protocol must be eg2027-eg05-v1")
    if audit.get("seeds") != [0, 1, 2]:
        errors.append("random baseline seeds must be [0, 1, 2]")

    movement = read_csv(args.run_dir / "movement_audit.csv")
    by_scene_variant = {(row["scene_id"], row["layout_variant"]): row for row in movement}
    scenes = sorted({row["scene_id"] for row in movement})

    for scene in scenes:
        main = by_scene_variant.get((scene, "collision_gated_floor_prior"))
        if main is None:
            errors.append(f"{scene} missing main movement audit row")
            continue
        main_total = float(main["total_xz_movement"])
        main_max = float(main["max_xz_movement"])
        for seed in [0, 1, 2]:
            row = by_scene_variant.get((scene, f"random_movement_matched_seed{seed}"))
            if row is None:
                errors.append(f"{scene} missing random seed {seed}")
                continue
            if abs(float(row["total_xz_movement"]) - main_total) > EPS:
                errors.append(f"{scene} seed {seed} total movement is not exact-matched")
            if abs(float(row["max_xz_movement"]) - main_max) > EPS:
                errors.append(f"{scene} seed {seed} max movement is not exact-matched")

        generic = by_scene_variant.get((scene, "generic_relation_optimizer"))
        if generic is None:
            errors.append(f"{scene} missing generic optimizer")
        elif float(generic["total_xz_movement"]) - float(generic["budget_total"]) > EPS:
            errors.append(f"{scene} generic optimizer exceeds total budget")

    summary = read_csv(args.run_dir / "summary.csv")
    variants = {row["layout_variant"] for row in summary}
    expected_variants = {
        "baseline",
        "collision_gated_floor_prior",
        "generic_relation_optimizer",
        "random_movement_matched_seed0",
        "random_movement_matched_seed1",
        "random_movement_matched_seed2",
    }
    missing_variants = expected_variants - variants
    if missing_variants:
        errors.append(f"summary missing variants: {sorted(missing_variants)}")

    if errors:
        fail(errors)

    print("EG-06 fixture fairness check passed.")
    print("random_baselines=exact per-object XZ movement matched")
    print("generic_optimizer=budget matched, may use less movement")
    print("claim_readiness=fixture only; full EG-07 export still required")


if __name__ == "__main__":
    main()
