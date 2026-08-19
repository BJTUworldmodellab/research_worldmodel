#!/usr/bin/env python3
"""Compute EG-08 paired scene-cluster bootstrap confidence intervals.

The primary estimand is the difference in relation accuracy, where relation
accuracy is a ratio of summed satisfied relations to summed target relations.
Scenes are the resampling clusters. Overall resampling is stratified by room so
the frozen bedroom/livingroom/diningroom split sizes remain fixed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


MAIN = "collision_gated_floor_prior"
BASELINE = "baseline"
GENERIC = "generic_relation_optimizer"
RANDOMS = tuple(f"random_movement_matched_seed{seed}" for seed in range(3))
ROOMS = ("bedroom", "livingroom", "diningroom")
EXPECTED_ROOM_COUNTS = {"bedroom": 162, "livingroom": 192, "diningroom": 177}
EXPECTED_VARIANTS = (BASELINE, MAIN, GENERIC, *RANDOMS)
COMPARISONS = (
    ("main_vs_baseline", BASELINE),
    ("main_vs_random_seed0", RANDOMS[0]),
    ("main_vs_random_seed1", RANDOMS[1]),
    ("main_vs_random_seed2", RANDOMS[2]),
    ("main_vs_random_mean", "random_seed_mean"),
    ("main_vs_generic_optimizer", GENERIC),
)
PRIMARY_COMPARISON = "main_vs_random_mean"
SCHEMA = "eg2027-eg08-paired-scene-bootstrap-v1"
CANONICAL_CHECKER = Path(__file__).with_name("check_eg06_full_completion.py")


@dataclass(frozen=True)
class SceneRecord:
    scene_id: str
    room_type: str
    n_relations: int
    satisfied: dict[str, int]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_per_scene(path: Path) -> dict[str, dict[str, dict[str, object]]]:
    by_scene: dict[str, dict[str, dict[str, object]]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "scene_id",
            "room_type",
            "layout_variant",
            "n_relations",
            "n_evaluated",
            "n_satisfied",
            "n_missing",
            "n_unsupported",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        for line_number, row in enumerate(reader, start=2):
            scene_id = row["scene_id"]
            variant = row["layout_variant"]
            if not scene_id or not variant:
                raise ValueError(f"{path}:{line_number}: blank scene_id or layout_variant")
            scene = by_scene.setdefault(scene_id, {})
            if variant in scene:
                raise ValueError(f"{path}:{line_number}: duplicate {scene_id}/{variant}")
            parsed: dict[str, object] = dict(row)
            for key in (
                "n_relations",
                "n_evaluated",
                "n_satisfied",
                "n_missing",
                "n_unsupported",
            ):
                parsed[key] = int(row[key])
            scene[variant] = parsed
    if not by_scene:
        raise ValueError(f"{path}: no data rows")
    return by_scene


def build_scene_records(
    eg05: dict[str, dict[str, dict[str, object]]],
    eg06: dict[str, dict[str, dict[str, object]]],
) -> tuple[list[SceneRecord], dict[str, object]]:
    if set(eg05) != set(eg06):
        missing_from_eg05 = sorted(set(eg06) - set(eg05))
        missing_from_eg06 = sorted(set(eg05) - set(eg06))
        raise ValueError(
            "EG05/EG06 scene mismatch: "
            f"missing_from_eg05={missing_from_eg05[:3]} "
            f"missing_from_eg06={missing_from_eg06[:3]}"
        )

    records: list[SceneRecord] = []
    room_counts = {room: 0 for room in ROOMS}
    missing_targets = 0
    unsupported_targets = 0
    for scene_id in sorted(eg06):
        variants = eg06[scene_id]
        if set(variants) != set(EXPECTED_VARIANTS):
            raise ValueError(
                f"{scene_id}: expected variants {sorted(EXPECTED_VARIANTS)}, "
                f"found {sorted(variants)}"
            )
        if set(eg05[scene_id]) != {BASELINE, MAIN}:
            raise ValueError(f"{scene_id}: EG05 must contain exactly baseline and main")

        reference = variants[BASELINE]
        room_type = str(reference["room_type"])
        if room_type not in room_counts:
            raise ValueError(f"{scene_id}: unexpected room_type={room_type}")
        n_relations = int(reference["n_relations"])
        if n_relations <= 0:
            raise ValueError(f"{scene_id}: n_relations must be positive")

        satisfied: dict[str, int] = {}
        for variant in EXPECTED_VARIANTS:
            row = variants[variant]
            for key in ("room_type", "n_relations", "n_missing", "n_unsupported"):
                if row[key] != reference[key]:
                    raise ValueError(f"{scene_id}/{variant}: inconsistent {key}")
            n_satisfied = int(row["n_satisfied"])
            if not 0 <= n_satisfied <= n_relations:
                raise ValueError(f"{scene_id}/{variant}: invalid n_satisfied")
            satisfied[variant] = n_satisfied

        for variant in (BASELINE, MAIN):
            for key in (
                "room_type",
                "n_relations",
                "n_evaluated",
                "n_satisfied",
                "n_missing",
                "n_unsupported",
            ):
                if eg05[scene_id][variant][key] != variants[variant][key]:
                    raise ValueError(f"{scene_id}/{variant}: EG05/EG06 mismatch in {key}")

        records.append(SceneRecord(scene_id, room_type, n_relations, satisfied))
        room_counts[room_type] += 1
        missing_targets += int(reference["n_missing"])
        unsupported_targets += int(reference["n_unsupported"])

    if room_counts != EXPECTED_ROOM_COUNTS:
        raise ValueError(f"room counts mismatch: {room_counts} != {EXPECTED_ROOM_COUNTS}")

    n_relations = sum(record.n_relations for record in records)
    if n_relations != 808:
        raise ValueError(f"target relation count mismatch: {n_relations} != 808")

    return records, {
        "scene_count": len(records),
        "room_counts": room_counts,
        "target_relations": n_relations,
        "missing_targets": missing_targets,
        "unsupported_targets": unsupported_targets,
        "variant_count": len(EXPECTED_VARIANTS),
        "eg05_rows": sum(len(rows) for rows in eg05.values()),
        "eg06_rows": sum(len(rows) for rows in eg06.values()),
    }


def control_satisfied(record: SceneRecord, control: str) -> float:
    if control == "random_seed_mean":
        return sum(record.satisfied[variant] for variant in RANDOMS) / len(RANDOMS)
    return float(record.satisfied[control])


def point_estimate(records: Iterable[SceneRecord], control: str) -> tuple[float, float, float, int]:
    selected = list(records)
    denominator = sum(record.n_relations for record in selected)
    if denominator <= 0:
        raise ValueError("comparison has no target relations")
    main_accuracy = sum(record.satisfied[MAIN] for record in selected) / denominator
    control_accuracy = sum(control_satisfied(record, control) for record in selected) / denominator
    return main_accuracy, control_accuracy, main_accuracy - control_accuracy, denominator


def _bootstrap_scope(
    records: list[SceneRecord],
    rounds: int,
    seed: int,
    stratified: bool,
    chunk_size: int,
) -> dict[str, np.ndarray]:
    if rounds <= 0 or chunk_size <= 0:
        raise ValueError("rounds and chunk_size must be positive")

    grouped = (
        [[record for record in records if record.room_type == room] for room in ROOMS]
        if stratified
        else [records]
    )
    if any(not group for group in grouped):
        raise ValueError("bootstrap scope contains an empty stratum")

    comparison_arrays = {name: np.empty(rounds, dtype=np.float64) for name, _ in COMPARISONS}
    rng = np.random.default_rng(seed)
    offset = 0
    while offset < rounds:
        current = min(chunk_size, rounds - offset)
        total_denominator = np.zeros(current, dtype=np.float64)
        total_main = np.zeros(current, dtype=np.float64)
        total_controls = {
            name: np.zeros(current, dtype=np.float64) for name, _ in COMPARISONS
        }

        for group in grouped:
            denominator = np.asarray([record.n_relations for record in group], dtype=np.float64)
            main = np.asarray([record.satisfied[MAIN] for record in group], dtype=np.float64)
            controls = {
                name: np.asarray([control_satisfied(record, control) for record in group])
                for name, control in COMPARISONS
            }
            sampled = rng.integers(0, len(group), size=(current, len(group)))
            total_denominator += denominator[sampled].sum(axis=1)
            total_main += main[sampled].sum(axis=1)
            for name, _ in COMPARISONS:
                total_controls[name] += controls[name][sampled].sum(axis=1)

        main_accuracy = total_main / total_denominator
        for name, _ in COMPARISONS:
            comparison_arrays[name][offset : offset + current] = (
                main_accuracy - total_controls[name] / total_denominator
            )
        offset += current

    return comparison_arrays


def classify_interval(low: float, high: float) -> str:
    if low > 0:
        return "MAIN_HIGHER"
    if high < 0:
        return "MAIN_LOWER"
    return "INCONCLUSIVE"


def compute_statistics(
    records: list[SceneRecord],
    rounds: int,
    seed: int,
    chunk_size: int,
) -> list[dict[str, object]]:
    scopes: list[tuple[str, list[SceneRecord], bool]] = [
        ("overall", records, True),
        *[(room, [record for record in records if record.room_type == room], False) for room in ROOMS],
    ]
    rows: list[dict[str, object]] = []
    for scope_index, (scope, selected, stratified) in enumerate(scopes):
        scope_seed = seed + scope_index
        bootstrap = _bootstrap_scope(selected, rounds, scope_seed, stratified, chunk_size)
        for name, control in COMPARISONS:
            main_accuracy, control_accuracy, gain, denominator = point_estimate(selected, control)
            low, high = np.quantile(bootstrap[name], [0.025, 0.975], method="linear")
            rows.append(
                {
                    "scope": scope,
                    "comparison": name,
                    "control_variant": control,
                    "n_scenes": len(selected),
                    "n_relations": denominator,
                    "main_accuracy": main_accuracy,
                    "control_accuracy": control_accuracy,
                    "gain": gain,
                    "gain_pp": gain * 100,
                    "ci95_low": float(low),
                    "ci95_high": float(high),
                    "ci95_low_pp": float(low) * 100,
                    "ci95_high_pp": float(high) * 100,
                    "bootstrap_standard_error": float(np.std(bootstrap[name], ddof=1)),
                    "bootstrap_fraction_gain_gt_zero": float(np.mean(bootstrap[name] > 0)),
                    "bootstrap_rounds": rounds,
                    "bootstrap_seed": scope_seed,
                    "resampling": "stratified_by_room_scene_clusters" if stratified else "scene_clusters",
                    "interval_classification": classify_interval(float(low), float(high)),
                    "gate_role": "PRIMARY" if scope == "overall" and name == PRIMARY_COMPARISON else "REPORTED",
                }
            )
    return rows


def load_canonical_eg06_ci(run_dir: Path, rounds: int, seed: int) -> dict[str, object]:
    """Run the already accepted EG06 CI implementation without duplicating it."""
    spec = importlib.util.spec_from_file_location("eg06_full_completion_for_eg08", CANONICAL_CHECKER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical checker: {CANONICAL_CHECKER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.bootstrap_ci(run_dir, rounds, seed)


def validate_final_metrics(path: Path, integrity: dict[str, object]) -> dict[str, object]:
    metrics = json.loads(path.read_text(encoding="utf-8"))
    structural = metrics["structural"]
    if structural["scenes"] != integrity["scene_count"]:
        raise ValueError("final metrics scene count does not match per-scene CSV")
    if structural["target_relations"] != integrity["target_relations"]:
        raise ValueError("final metrics relation count does not match per-scene CSV")
    if structural["scene_count_by_room"] != integrity["room_counts"]:
        raise ValueError("final metrics room counts do not match per-scene CSV")
    if metrics["eg05"]["missing"]["overall"] != integrity["missing_targets"]:
        raise ValueError("final metrics missing-target count does not match per-scene CSV")
    if metrics["eg05"]["unsupported"] != integrity["unsupported_targets"]:
        raise ValueError("final metrics unsupported-target count does not match per-scene CSV")
    fairness = metrics["eg06"]["fairness"]
    if fairness != {
        "generic_within_budget": True,
        "random_exact_movement_matched": True,
    }:
        raise ValueError(f"EG06 fairness gate failed: {fairness}")
    baseline_collisions = int(structural["baseline_collision_pairs_total"])
    chosen_collisions = int(structural["chosen_main_collision_pairs_total"])
    return {
        "baseline_collision_pairs_total": baseline_collisions,
        "chosen_main_collision_pairs_total": chosen_collisions,
        "collision_non_worsening": chosen_collisions <= baseline_collisions,
        "random_exact_movement_matched": fairness["random_exact_movement_matched"],
        "generic_within_budget": fairness["generic_within_budget"],
        "layouts_sha256": metrics["input"]["layouts_sha256"],
        "frozen_config_sha256": metrics["provenance"]["source_config_sha256"],
        "generation_code_commit": metrics["provenance"]["code_commit"],
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def format_report(payload: dict[str, object]) -> str:
    rows = payload["statistics"]
    overall = [row for row in rows if row["scope"] == "overall"]
    primary = payload["primary_gate"]
    lines = [
        "# EG-08 Paired Scene-Level Statistics",
        "",
        "Date: 2026-08-16",
        "Branch: `agent/eg01-eg02-eurographics2027`",
        f"Schema: `{SCHEMA}`",
        "",
        "## Verdict",
        "",
        f"**{payload['verdict']}**",
        "",
        "The frozen primary gate compares Collision-gated Floor-Prior with the mean of the three "
        "movement-matched random seeds. The gate is GO only when the overall 95% paired "
        "scene-cluster bootstrap CI lower bound is above zero.",
        "",
        f"Canonical primary gain: **{primary['gain_pp']:.3f} pp**, relation-weighted 95% CI "
        f"**[{primary['ci95_low_pp']:.3f}, {primary['ci95_high_pp']:.3f}] pp**.",
        "",
        "## 50,000-round stratified sensitivity comparisons",
        "",
        "| Comparison | Main | Control | Gain (pp) | 95% CI (pp) | Classification | Gate |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in overall:
        lines.append(
            f"| {row['comparison']} | {row['main_accuracy']:.6f} | "
            f"{row['control_accuracy']:.6f} | {row['gain_pp']:+.3f} | "
            f"[{row['ci95_low_pp']:+.3f}, {row['ci95_high_pp']:+.3f}] | "
            f"{row['interval_classification']} | {row['gate_role']} |"
        )
    lines.extend(
        [
            "",
            "## Room-level stratified sensitivity for the primary comparison",
            "",
            "| Room | Scenes | Relations | Gain (pp) | 95% CI (pp) | Classification |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        if row["scope"] != "overall" and row["comparison"] == PRIMARY_COMPARISON:
            lines.append(
                f"| {row['scope']} | {row['n_scenes']} | {row['n_relations']} | "
                f"{row['gain_pp']:+.3f} | [{row['ci95_low_pp']:+.3f}, "
                f"{row['ci95_high_pp']:+.3f}] | {row['interval_classification']} |"
            )
    method = payload["methodology"]["sensitivity"]
    canonical = payload["methodology"]["canonical"]
    safety = payload["safety_gate"]
    lines.extend(
        [
            "",
            "## Methodology",
            "",
            f"- Canonical EG06 integration: both scene-unweighted and relation-weighted intervals, "
            f"{canonical['rounds']:,} unstratified scene resamples, seed {canonical['seed']}.",
            f"- Estimand: `{method['estimand']}`.",
            f"- Resampling unit: `{method['resampling_unit']}`.",
            f"- Overall stratification: `{method['overall_stratification']}`.",
            f"- Interval: percentile 95% CI, {method['rounds']:,} rounds, base seed {method['seed']}.",
            "- Missing targets remain in the denominator; unsupported predicates are explicitly counted.",
            "- Bootstrap fraction above zero is a stability diagnostic, not a p-value.",
            "",
            "## Safety and claim boundary",
            "",
            f"- Mesh collision pairs: chosen main {safety['chosen_main_collision_pairs_total']} vs "
            f"baseline {safety['baseline_collision_pairs_total']} — "
            f"{'GO' if safety['collision_non_worsening'] else 'NO-GO'}.",
            "- Only the overall main-vs-random-mean interval is the frozen superiority gate.",
            "- Baseline, individual random seeds, generic optimizer, and room-level intervals are reported, "
            "not silently promoted to additional gates.",
            "- A CI that includes zero does not establish superiority; it must be described as inconclusive.",
            "",
            "## Inputs",
            "",
        ]
    )
    for name, item in payload["inputs"].items():
        lines.append(f"- `{name}`: `{item['path']}` — SHA-256 `{item['sha256']}`")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path("eg07_final_delivery_20260814")
    parser.add_argument("--eg05-per-scene", type=Path, default=root / "eg05" / "per_scene.csv")
    parser.add_argument("--eg06-per-scene", type=Path, default=root / "eg06" / "per_scene.csv")
    parser.add_argument(
        "--final-metrics",
        type=Path,
        default=root / "final" / "eg07_final_metrics_20260814.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/independent_eval/eg2027/eg08_paired_statistics_20260816"),
    )
    parser.add_argument("--rounds", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--chunk-size", type=int, default=1_000)
    parser.add_argument("--canonical-rounds", type=int, default=10_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    inputs = {
        "eg05_per_scene": args.eg05_per_scene,
        "eg06_per_scene": args.eg06_per_scene,
        "eg07_final_metrics": args.final_metrics,
    }
    for path in inputs.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    eg05 = read_per_scene(args.eg05_per_scene)
    eg06 = read_per_scene(args.eg06_per_scene)
    records, integrity = build_scene_records(eg05, eg06)
    safety_gate = validate_final_metrics(args.final_metrics, integrity)
    canonical_ci = load_canonical_eg06_ci(
        args.eg06_per_scene.parent, args.canonical_rounds, args.seed
    )
    statistics = compute_statistics(records, args.rounds, args.seed, args.chunk_size)
    canonical_random_controls = [*RANDOMS, "random_mean"]
    canonical_random_go = all(
        float(canonical_ci[variant]["scene_unweighted_ci95"][0]) > 0
        and float(canonical_ci[variant]["relation_weighted_ci95"][0]) > 0
        for variant in canonical_random_controls
    )
    canonical_primary = canonical_ci["random_mean"]
    primary_low, primary_high = canonical_primary["relation_weighted_ci95"]
    primary_go = float(primary_low) > 0
    verdict = (
        "EG08_GO"
        if primary_go and canonical_random_go and safety_gate["collision_non_worsening"]
        else "EG08_NO_GO"
    )

    payload: dict[str, object] = {
        "schema": SCHEMA,
        "created_at": "2026-08-16",
        "verdict": verdict,
        "primary_gate": {
            "comparison": PRIMARY_COMPARISON,
            "rule": "accepted EG06 protocol: all random controls pass both paired estimators; random-mean relation-weighted ci95_low > 0",
            "gain": canonical_primary["relation_weighted_diff"],
            "gain_pp": canonical_primary["relation_weighted_diff"] * 100,
            "ci95_low": primary_low,
            "ci95_high": primary_high,
            "ci95_low_pp": primary_low * 100,
            "ci95_high_pp": primary_high * 100,
            "all_random_controls_both_estimators_go": canonical_random_go,
            "decision": "GO" if primary_go else "NO_GO",
        },
        "methodology": {
            "canonical": {
                "source": CANONICAL_CHECKER.as_posix(),
                "estimators": ["scene_unweighted", "relation_weighted"],
                "resampling_unit": "paired scene",
                "overall_stratification": "none",
                "interval": "percentile",
                "confidence_level": 0.95,
                "rounds": args.canonical_rounds,
                "seed": args.seed,
                "rng": "python random.Random",
            },
            "sensitivity": {
                "estimand": "difference of relation-accuracy ratios (sum satisfied / sum target relations)",
                "resampling_unit": "paired scene cluster",
                "overall_stratification": "fixed bedroom/livingroom/diningroom scene counts",
                "interval": "percentile",
                "confidence_level": 0.95,
                "rounds": args.rounds,
                "seed": args.seed,
                "rng": "numpy.random.default_rng (PCG64)",
            },
        },
        "integrity": integrity,
        "safety_gate": safety_gate,
        "inputs": {
            name: {"path": path.as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for name, path in inputs.items()
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "canonical_eg06_ci": canonical_ci,
        "statistics": statistics,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "paired_ci.csv", statistics)
    (args.output_dir / "canonical_eg06_ci.json").write_text(
        json.dumps(canonical_ci, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "paired_statistics.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "eg08_report.md").write_text(format_report(payload), encoding="utf-8")
    (args.output_dir / verdict).write_text(
        f"{verdict}\nprimary_ci95_low={primary_low:.12f}\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"verdict": verdict, "primary": payload["primary_gate"], "output_dir": str(args.output_dir)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
