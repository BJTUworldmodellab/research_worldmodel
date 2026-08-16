#!/usr/bin/env python3
"""Check EG-06 full-run movement fairness and paired bootstrap CIs."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_DIR = ROOT / "eg07_final_delivery_20260814" / "eg06"
MAIN = "collision_gated_floor_prior"
RANDOM_VARIANTS = [
    "random_movement_matched_seed0",
    "random_movement_matched_seed1",
    "random_movement_matched_seed2",
]
COMPARISONS = [
    "baseline",
    *RANDOM_VARIANTS,
    "random_mean",
    "generic_relation_optimizer",
]
EPS = 1e-6


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    idx = (len(ordered) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(ordered) - 1)
    frac = idx - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac


def check_movement(run_dir: Path) -> dict[str, object]:
    rows = read_csv(run_dir / "movement_audit.csv")
    scenes = sorted({row["scene_id"] for row in rows})
    by_scene_variant = {(row["scene_id"], row["layout_variant"]): row for row in rows}
    errors: list[str] = []

    for scene in scenes:
        main = by_scene_variant.get((scene, MAIN))
        if main is None:
            errors.append(f"{scene}: missing main movement row")
            continue
        main_total = float(main["total_xz_movement"])
        main_max = float(main["max_xz_movement"])
        for variant in RANDOM_VARIANTS:
            row = by_scene_variant.get((scene, variant))
            if row is None:
                errors.append(f"{scene}: missing {variant}")
                continue
            if abs(float(row["total_xz_movement"]) - main_total) > EPS:
                errors.append(f"{scene}: {variant} total movement mismatch")
            if abs(float(row["max_xz_movement"]) - main_max) > EPS:
                errors.append(f"{scene}: {variant} max movement mismatch")

        generic = by_scene_variant.get((scene, "generic_relation_optimizer"))
        if generic is None:
            errors.append(f"{scene}: missing generic optimizer")
        elif (
            float(generic["total_xz_movement"]) - float(generic["budget_total"]) > EPS
            or float(generic["max_xz_movement"]) - float(generic["budget_max"]) > EPS
        ):
            errors.append(f"{scene}: generic optimizer exceeds movement budget")

    return {
        "rows": len(rows),
        "scenes": len(scenes),
        "expected_rows": len(scenes) * 5,
        "errors": errors,
    }


def bootstrap_ci(run_dir: Path, rounds: int, seed: int) -> dict[str, object]:
    rows = read_csv(run_dir / "per_scene.csv")
    by_scene: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        by_scene.setdefault(row["scene_id"], {})[row["layout_variant"]] = row
    scenes = sorted(by_scene)

    rng = random.Random(seed)
    output: dict[str, object] = {}
    for variant in COMPARISONS:
        unweighted_diffs: list[float] = []
        weighted_terms: list[tuple[float, float]] = []
        for scene in scenes:
            scene_rows = by_scene[scene]
            main = scene_rows[MAIN]
            if variant == "random_mean":
                comparison_accuracy = sum(
                    float(scene_rows[random_variant]["relation_accuracy"])
                    for random_variant in RANDOM_VARIANTS
                ) / len(RANDOM_VARIANTS)
                comparison_satisfied = sum(
                    float(scene_rows[random_variant]["n_satisfied"])
                    for random_variant in RANDOM_VARIANTS
                ) / len(RANDOM_VARIANTS)
                comparison_relations = float(scene_rows[RANDOM_VARIANTS[0]]["n_relations"])
            else:
                comparison = scene_rows[variant]
                comparison_accuracy = float(comparison["relation_accuracy"])
                comparison_satisfied = float(comparison["n_satisfied"])
                comparison_relations = float(comparison["n_relations"])

            unweighted_diffs.append(float(main["relation_accuracy"]) - comparison_accuracy)
            weighted_terms.append(
                (float(main["n_satisfied"]) - comparison_satisfied, comparison_relations)
            )

        boot_unweighted: list[float] = []
        boot_weighted: list[float] = []
        n_scenes = len(scenes)
        for _ in range(rounds):
            sample = [rng.randrange(n_scenes) for _ in range(n_scenes)]
            boot_unweighted.append(sum(unweighted_diffs[idx] for idx in sample) / n_scenes)
            denominator = sum(weighted_terms[idx][1] for idx in sample)
            boot_weighted.append(
                sum(weighted_terms[idx][0] for idx in sample) / denominator
                if denominator
                else 0.0
            )

        output[variant] = {
            "scene_unweighted_mean_diff": sum(unweighted_diffs) / n_scenes,
            "scene_unweighted_ci95": [
                percentile(boot_unweighted, 0.025),
                percentile(boot_unweighted, 0.975),
            ],
            "relation_weighted_diff": sum(term[0] for term in weighted_terms)
            / sum(term[1] for term in weighted_terms),
            "relation_weighted_ci95": [
                percentile(boot_weighted, 0.025),
                percentile(boot_weighted, 0.975),
            ],
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--rounds", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260816)
    args = parser.parse_args()

    movement = check_movement(args.run_dir)
    if movement["rows"] != movement["expected_rows"] or movement["errors"]:
        print(json.dumps({"movement": movement}, indent=2))
        sys.exit(1)

    ci = bootstrap_ci(args.run_dir, args.rounds, args.seed)
    random_comparisons = [*RANDOM_VARIANTS, "random_mean"]
    random_pass = all(
        ci[variant]["scene_unweighted_ci95"][0] > 0
        and ci[variant]["relation_weighted_ci95"][0] > 0
        for variant in random_comparisons
    )
    generic_pass = (
        ci["generic_relation_optimizer"]["scene_unweighted_ci95"][0] > 0
        and ci["generic_relation_optimizer"]["relation_weighted_ci95"][0] > 0
    )
    result = {
        "movement": movement,
        "bootstrap_seed": args.seed,
        "bootstrap_resamples": args.rounds,
        "paired_ci": ci,
        "acceptance": {
            "all_random_ci_lower_gt_0": random_pass,
            "generic_optimizer_ci_lower_gt_0": generic_pass,
            "eg06_claim_status": (
                "complete_for_random_movement_baseline_generic_not_beaten"
                if random_pass and not generic_pass
                else "review_required"
            ),
        },
    }
    print(json.dumps(result, indent=2))

    if not random_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
