#!/usr/bin/env python3
"""Run an OBB-only CW-GCP pilot on archived InstructScene layouts.

The runner compares four methods on identical exported scenes:

* original generator layout;
* collision-gated Floor-Prior from the archived result;
* movement-matched random displacement;
* CW-GCP/FA-PSP under a declared movement/edit budget policy.

An optional generic projection control disables confidence and slack.  The
local machine has no FCL/assets, so this runner never labels its output
mesh-safe.  Full method promotion remains blocked until a remote FCL rerun and
human-audited independent evaluation are complete.
"""

import argparse
import copy
import csv
import glob
import hashlib
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cwgcp import CWGCPConfig, repair_layout_cwgcp
from src.cwgcp.adapters import (
    apply_centers_to_exported_boxes,
    objects_from_exported_boxes,
    proposals_from_exported_relations,
)
from src.independent_eval.cwgcp_layout_evaluator import (
    EVALUATOR_CLOSE_DISTANCE,
    EVALUATOR_VERSION,
    evaluate_layout,
)


CANONICAL_PATTERN = (
    "results/floor_prior_remote/"
    "*_relation_aware_parsed_floor_prior_max1.8_mesh_p2_"
    "close0.75_far1.6_eval_cfg1.0_1.0.json"
)

REPRODUCIBILITY_PATHS = (
    "scripts/run_cwgcp_pilot.py",
    "src/relation_schema.py",
    "src/cwgcp",
    "src/independent_eval",
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def _fraction(value: str) -> float:
    parsed = float(value)
    if not 0.0 < parsed < 1.0:
        raise argparse.ArgumentTypeError("value must be strictly between 0 and 1")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not np.isfinite(parsed) or parsed <= 0.0:
        raise argparse.ArgumentTypeError("value must be finite and positive")
    return parsed


def _non_negative_float(value: str) -> float:
    parsed = float(value)
    if not np.isfinite(parsed) or parsed < 0.0:
        raise argparse.ArgumentTypeError(
            "value must be finite and non-negative"
        )
    return parsed


def _split_for_scene(
    scene_uid: str, salt: str, development_fraction: float
) -> str:
    digest = hashlib.sha256(f"{salt}:{scene_uid}".encode("utf-8")).digest()
    fraction = int.from_bytes(digest[:4], "big") / float(0xFFFFFFFF)
    return "dev" if fraction < development_fraction else "validation"


def _validate_scene_record(scene: dict, input_path: str) -> None:
    required = {
        "scene_uid",
        "layout_boxes",
        "repair_boxes",
        "repair_target_relations",
    }
    missing = sorted(required - set(scene))
    if missing:
        raise ValueError(f"{input_path}: scene is missing keys {missing}")
    for name in ("layout_boxes", "repair_boxes"):
        if not isinstance(scene[name], list) or not scene[name]:
            raise ValueError(f"{input_path}: {name} must be a non-empty list")
        for box in scene[name]:
            box_missing = {
                "index",
                "class_id",
                "translation",
                "size",
            } - set(box)
            if box_missing:
                raise ValueError(
                    f"{input_path}: {name} box missing {sorted(box_missing)}"
                )
            if len(box["translation"]) != 3 or len(box["size"]) != 3:
                raise ValueError(
                    f"{input_path}: translations and sizes must have length 3"
                )
            values = list(box["translation"]) + list(box["size"])
            if not all(np.isfinite(float(value)) for value in values):
                raise ValueError(f"{input_path}: box geometry must be finite")
            if any(float(value) <= 0 for value in box["size"]):
                raise ValueError(f"{input_path}: box sizes must be positive")
    if not isinstance(scene["repair_target_relations"], list):
        raise ValueError(
            f"{input_path}: repair_target_relations must be a list"
        )


def _file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return result.stdout.strip()


def _source_tree_provenance() -> dict:
    files = []
    for entry in REPRODUCIBILITY_PATHS:
        path = Path(entry)
        if path.is_dir():
            files.extend(
                candidate
                for candidate in sorted(path.rglob("*.py"))
                if "__pycache__" not in candidate.parts
            )
        elif path.is_file():
            files.append(path)
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    try:
        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--",
                *REPRODUCIBILITY_PATHS,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        relevant_tree_clean = not result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        relevant_tree_clean = False
    return {
        "sha256": digest.hexdigest(),
        "files": [path.as_posix() for path in files],
        "relevant_tree_clean": relevant_tree_clean,
    }


def _room_from_path(path: str) -> str:
    return Path(path).name.split("_", 1)[0]


def _movement(original: Sequence[dict], candidate: Sequence[dict]) -> Dict[str, object]:
    original_by_index = {
        int(box["index"]): np.asarray(box["translation"], dtype=np.float64)
        for box in original
    }
    values = []
    for box in candidate:
        before = original_by_index[int(box["index"])]
        after = np.asarray(box["translation"], dtype=np.float64)
        values.append(float(np.linalg.norm(after[[0, 2]] - before[[0, 2]])))
    return {
        "per_object": values,
        "total": float(sum(values)),
        "maximum": float(max(values)) if values else 0.0,
        "edited": int(sum(value > 1e-3 for value in values)),
    }


def _method_budget(
    floor_movement: Mapping[str, object],
    policy: str,
    total_movement_cap: float,
    edit_cap: int,
    anchor_residual_cap: float,
) -> Tuple[float, int]:
    """Return an input-determined budget that always contains the anchor."""

    floor_total = float(floor_movement["total"])
    floor_edited = int(floor_movement["edited"])
    if policy == "floor_realized":
        return floor_total, floor_edited
    if floor_total > total_movement_cap + 1e-9 or floor_edited > edit_cap:
        raise ValueError("method cap does not contain the Floor-Prior anchor")
    if policy == "fixed_cap":
        return total_movement_cap, edit_cap
    if policy == "anchor_plus_residual":
        return (
            min(total_movement_cap, floor_total + anchor_residual_cap),
            edit_cap,
        )
    raise ValueError(f"unsupported budget policy {policy!r}")


def _collision_gated_floor_prior(scene: dict) -> Tuple[List[dict], dict]:
    baseline_mesh = scene.get("layout_mesh_collision")
    repair_mesh = scene.get("repair_mesh_collision")
    mesh_available = bool(
        baseline_mesh
        and repair_mesh
        and baseline_mesh.get("available")
        and repair_mesh.get("available")
    )
    if mesh_available:
        accepted = int(repair_mesh["collision_pairs"]) <= int(
            baseline_mesh["collision_pairs"]
        )
    else:
        # Preserve the historical Floor-Prior output, but make the absence of
        # mesh gating explicit in the record.
        accepted = True
    boxes = scene["repair_boxes"] if accepted else scene["layout_boxes"]
    return copy.deepcopy(boxes), {
        "mesh_gate_available": mesh_available,
        "repair_accepted": bool(accepted),
        "baseline_mesh_collision_pairs": (
            int(baseline_mesh["collision_pairs"]) if mesh_available else None
        ),
        "repair_mesh_collision_pairs": (
            int(repair_mesh["collision_pairs"]) if mesh_available else None
        ),
    }


def _stable_seed(scene_uid: str, seed: int) -> int:
    digest = hashlib.sha256(f"{scene_uid}:{seed}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _movement_matched_random(
    boxes: Sequence[dict],
    total_budget: float,
    edit_budget: int,
    per_object_budget: float,
    scene_uid: str,
    seed: int,
    max_attempts: int = 64,
) -> Tuple[List[dict], dict]:
    """Safety-constrained rejection sampling at the realized movement budget."""

    if total_budget <= 1e-9 or edit_budget <= 0:
        return copy.deepcopy(list(boxes)), {
            "available": True,
            "accepted": False,
            "rollback_reason": "zero_budget",
            "attempts": 0,
            "movement_ratio": 1.0,
        }

    rng = np.random.RandomState(_stable_seed(scene_uid, seed))
    baseline_geometry = evaluate_layout(boxes, [])
    count = min(edit_budget, len(boxes))
    for attempt in range(1, max_attempts + 1):
        chosen = rng.choice(len(boxes), size=count, replace=False)
        weights = rng.uniform(0.5, 1.5, size=count)
        weights /= weights.sum()
        distances = np.minimum(weights * total_budget, per_object_budget)
        leftover = total_budget - float(distances.sum())
        for _ in range(count * 2):
            if leftover <= 1e-9:
                break
            capacity = per_object_budget - distances
            available_indices = np.where(capacity > 1e-9)[0]
            if len(available_indices) == 0:
                break
            share = leftover / len(available_indices)
            added = np.minimum(capacity[available_indices], share)
            distances[available_indices] += added
            leftover -= float(added.sum())

        realized = float(distances.sum())
        movement_ratio = realized / total_budget
        if not 0.95 <= movement_ratio <= 1.05:
            continue
        angles = rng.uniform(0, 2 * np.pi, size=count)
        candidate = copy.deepcopy(list(boxes))
        for box_index, distance, angle in zip(chosen, distances, angles):
            candidate[box_index]["translation"][0] += float(
                distance * np.cos(angle)
            )
            candidate[box_index]["translation"][2] += float(
                distance * np.sin(angle)
            )

        candidate_geometry = evaluate_layout(candidate, [])
        worsened = (
            candidate_geometry["obb_collision_pairs"]
            > baseline_geometry["obb_collision_pairs"]
            or candidate_geometry["obb_overlap_area"]
            > baseline_geometry["obb_overlap_area"] + 1e-7
        )
        if not worsened:
            return candidate, {
                "available": True,
                "accepted": True,
                "rollback_reason": None,
                "attempts": attempt,
                "movement_ratio": movement_ratio,
            }
    return copy.deepcopy(list(boxes)), {
        "available": False,
        "accepted": False,
        "rollback_reason": "no_safe_movement_matched_candidate",
        "attempts": max_attempts,
        "movement_ratio": 0.0,
    }


def _evaluate_variant(
    boxes: Sequence[dict], relations: Sequence[Sequence[int]]
) -> Dict[str, object]:
    return evaluate_layout(
        boxes, relations, close_distance=EVALUATOR_CLOSE_DISTANCE
    )


def _bootstrap_delta(
    rows: Sequence[dict],
    lhs: str,
    rhs: str,
    samples: int,
    seed: int,
) -> Dict[str, float]:
    eligible = [
        row for row in rows
        if row.get(f"{lhs}_available", True)
        and row.get(f"{rhs}_available", True)
    ]
    if not eligible:
        return {
            "mean": 0.0,
            "low": 0.0,
            "high": 0.0,
            "scene_count": 0,
            "cluster_count": 0,
        }
    rows = eligible
    grouped: Dict[str, List[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row["scene_uid"]), []).append(row)
    clusters = list(grouped.values())
    rng = np.random.RandomState(seed)

    def accuracy(cluster_indices: np.ndarray, prefix: str) -> float:
        sampled_rows = [
            row
            for cluster_index in cluster_indices
            for row in clusters[int(cluster_index)]
        ]
        satisfied = sum(
            int(row[f"{prefix}_satisfied"]) for row in sampled_rows
        )
        total = sum(int(row[f"{prefix}_total"]) for row in sampled_rows)
        return float(satisfied / total) if total else 0.0

    all_indices = np.arange(len(clusters))
    observed = accuracy(all_indices, lhs) - accuracy(all_indices, rhs)
    values = np.empty(samples, dtype=np.float64)
    for sample in range(samples):
        indices = rng.randint(0, len(clusters), size=len(clusters))
        values[sample] = accuracy(indices, lhs) - accuracy(indices, rhs)
    low, high = np.quantile(values, [0.025, 0.975])
    return {
        "mean": float(observed),
        "low": float(low),
        "high": float(high),
        "scene_count": len(rows),
        "cluster_count": len(clusters),
    }


def _aggregate(rows: Sequence[dict], prefix: str) -> Dict[str, float]:
    rows = [
        row for row in rows
        if row.get(f"{prefix}_available", True)
    ]
    total = sum(int(row[f"{prefix}_total"]) for row in rows)
    satisfied = sum(int(row[f"{prefix}_satisfied"]) for row in rows)
    result = {
        "scene_count": len(rows),
        "satisfied": int(satisfied),
        "total": int(total),
        "accuracy": float(satisfied / total) if total else 0.0,
        "mean_obb_collision_pairs": float(
            np.mean([row[f"{prefix}_obb_collision_pairs"] for row in rows])
        )
        if rows
        else 0.0,
        "mean_obb_overlap_area": float(
            np.mean([row[f"{prefix}_obb_overlap_area"] for row in rows])
        )
        if rows
        else 0.0,
        "mean_total_movement": float(
            np.mean([row[f"{prefix}_total_movement"] for row in rows])
        )
        if rows
        else 0.0,
    }
    mesh_key = f"{prefix}_mesh_collision_pairs"
    if rows and mesh_key in rows[0]:
        values = [
            float(row[mesh_key])
            for row in rows
            if row[mesh_key] is not None
            and np.isfinite(float(row[mesh_key]))
        ]
    else:
        values = []
    if values:
        result["mean_mesh_collision_pairs"] = float(np.mean(values))
    else:
        result["mean_mesh_collision_pairs"] = None
    return result


def _flatten_eval(row: dict, prefix: str, evaluation: dict, movement: dict) -> None:
    row[f"{prefix}_satisfied"] = int(evaluation["satisfied_relations"])
    row[f"{prefix}_total"] = int(evaluation["total_relations"])
    row[f"{prefix}_accuracy"] = float(evaluation["relation_accuracy"])
    row[f"{prefix}_obb_collision_pairs"] = int(
        evaluation["obb_collision_pairs"]
    )
    row[f"{prefix}_obb_overlap_area"] = float(evaluation["obb_overlap_area"])
    row[f"{prefix}_total_movement"] = float(movement["total"])
    row[f"{prefix}_max_movement"] = float(movement["maximum"])
    row[f"{prefix}_edited_objects"] = int(movement["edited"])


def _write_outputs(
    output_dir: Path,
    rows: Sequence[dict],
    certificates: Sequence[dict],
    summary: dict,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if rows:
        with (output_dir / "paired_scene_metrics.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    with (output_dir / "certificates.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for record in certificates:
            handle.write(
                json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n"
            )
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            summary, handle, ensure_ascii=False, indent=2, allow_nan=False
        )

    lines = [
        f"# CW-GCP Pilot ({summary['safety_mode']})",
        "",
        f"- Scenes: {summary['scene_count']}",
        f"- Random-control eligible scenes: "
        f"{summary['random_available_scenes']}",
        f"- Relations: {summary['methods']['baseline']['total']}",
        f"- CW-GCP accepted scenes: {summary['accepted_scenes']}",
        f"- Selected sources: `{summary['selected_source_counts']}`",
        f"- New-candidate FCL recomputation available: "
        f"**{summary['new_candidate_fcl_recomputation_available']}**",
        f"- Cached FCL available for every selected layout: "
        f"**{summary['selected_layout_cached_fcl_available']}**",
        f"- CPU solver signal: **{summary['cpu_solver_signal']}**",
        f"- Paper-method upgrade GO: **{summary['method_upgrade_go']}**",
        "",
        "## Aggregate comparison",
        "",
        "| Method | Relation accuracy | Mean mesh pairs | Mean OBB pairs | Mean overlap area | Mean movement |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, metrics in summary["methods"].items():
        lines.append(
            f"| {name} | {metrics['accuracy']:.4f} | "
            f"{metrics['mean_mesh_collision_pairs'] if metrics['mean_mesh_collision_pairs'] is not None else 'NA'} | "
            f"{metrics['mean_obb_collision_pairs']:.4f} | "
            f"{metrics['mean_obb_overlap_area']:.4f} | "
            f"{metrics['mean_total_movement']:.4f} |"
        )
    lines += [
        "",
        "## Paired scene-bootstrap deltas",
        "",
        "| Comparison | Mean | 95% CI |",
        "|---|---:|---:|",
    ]
    for name, interval in summary["paired_deltas"].items():
        lines.append(
            f"| {name} | {interval['mean']:+.4f} | "
            f"[{interval['low']:+.4f}, {interval['high']:+.4f}] |"
        )
    lines += [
        "",
        "## Mandatory limitations",
        "",
        "- This run uses a separately implemented evaluator, but it has not yet "
        "been validated on a human-audited subset.",
        "- Archived triples are class-level, so instance-assignment accuracy "
        "cannot be claimed without new annotations.",
        "- Cached FCL is available for original/Floor-Prior warm starts. "
        "It is only enforced in `cached_fcl` selector mode. Local FCL "
        "recomputation for new solver candidates and true "
        "room-boundary containment are unavailable and fail closed.",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit-per-room", type=_non_negative_int, default=0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--restarts", type=_positive_int, default=2)
    parser.add_argument("--outer-iterations", type=_positive_int, default=2)
    parser.add_argument(
        "--solver-max-iterations", type=_positive_int, default=80
    )
    parser.add_argument(
        "--bootstrap-samples", type=_positive_int, default=5000
    )
    parser.add_argument(
        "--safety-mode",
        choices=("obb_only", "cached_fcl"),
        default="obb_only",
        help=(
            "obb_only evaluates new candidates with exact OBB gates; "
            "cached_fcl is a guarded selector that only recognizes archived "
            "baseline/Floor-Prior layouts"
        ),
    )
    parser.add_argument(
        "--split",
        choices=("all", "dev", "validation"),
        default="all",
        help="source-scene hash split to evaluate",
    )
    parser.add_argument(
        "--split-salt",
        default="cwgcp-v03-main-method-20260729",
    )
    parser.add_argument(
        "--development-fraction",
        type=_fraction,
        default=0.4,
    )
    parser.add_argument(
        "--method-profile",
        choices=("cwgcp_v021", "fapsp_v03", "agrp_v04"),
        default="cwgcp_v021",
    )
    parser.add_argument(
        "--budget-policy",
        choices=("floor_realized", "fixed_cap", "anchor_plus_residual"),
        default="floor_realized",
    )
    parser.add_argument(
        "--total-movement-cap",
        type=_positive_float,
        default=3.6,
    )
    parser.add_argument("--edit-cap", type=_positive_int, default=3)
    parser.add_argument(
        "--anchor-residual-cap",
        type=_non_negative_float,
        default=0.25,
        help=(
            "maximum movement beyond the collision-gated Floor-Prior anchor "
            "when --budget-policy=anchor_plus_residual"
        ),
    )
    parser.add_argument(
        "--semantic-margin",
        type=_non_negative_float,
        default=0.02,
    )
    parser.add_argument(
        "--random-match",
        choices=("auto", "floor", "candidate"),
        default="auto",
    )
    parser.add_argument("--include-generic", action="store_true")
    args = parser.parse_args()

    inputs = args.input or sorted(glob.glob(CANONICAL_PATTERN))
    if not inputs:
        raise SystemExit("No canonical Floor-Prior JSON inputs found")

    profile_config = {}
    if args.method_profile == "fapsp_v03":
        profile_config = {
            "relation_margin": args.semantic_margin,
            "min_confidence": 1.0,
            "max_slack": 0.0,
            "refine_warm_starts": True,
            "coverage_first_selection": True,
            "require_coverage_gain": True,
            "enable_proposal_nudge": True,
        }
    elif args.method_profile == "agrp_v04":
        profile_config = {
            "relation_margin": args.semantic_margin,
            "min_confidence": 1.0,
            "max_slack": 0.0,
            "refine_warm_starts": True,
            "coverage_first_selection": False,
            "require_coverage_gain": False,
            "enable_proposal_nudge": False,
        }
    base_config = CWGCPConfig(
        restarts=args.restarts,
        outer_iterations=args.outer_iterations,
        solver_max_iterations=args.solver_max_iterations,
        seed=args.seed,
        **profile_config,
    )
    rows: List[dict] = []
    certificates: List[dict] = []
    seen_evaluation_uids = set()
    input_hashes = {path: _file_sha256(path) for path in inputs}
    code_commit = _git_commit()
    source_tree = _source_tree_provenance()
    started = time.perf_counter()

    for input_path in inputs:
        room = _room_from_path(input_path)
        with open(input_path, encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict) or not isinstance(
            payload.get("per_scene"), list
        ):
            raise ValueError(f"{input_path}: per_scene must be a list")
        scenes = payload["per_scene"]
        if args.split != "all":
            scenes = [
                scene
                for scene in scenes
                if _split_for_scene(
                    str(scene.get("scene_uid", "")),
                    args.split_salt,
                    args.development_fraction,
                )
                == args.split
            ]
        seen_source_uids_in_input = set()
        if args.limit_per_room > 0:
            scenes = scenes[: args.limit_per_room]
        print(f"{room}: {len(scenes)} scenes from {Path(input_path).name}")

        for scene_index, scene in enumerate(scenes):
            _validate_scene_record(scene, input_path)
            scene_uid = str(scene["scene_uid"])
            if scene_uid in seen_source_uids_in_input:
                raise ValueError(
                    f"{input_path}: duplicate scene_uid within input "
                    f"{scene_uid!r}"
                )
            seen_source_uids_in_input.add(scene_uid)
            evaluation_uid = f"{Path(input_path).name}::{scene_uid}"
            if evaluation_uid in seen_evaluation_uids:
                raise ValueError(
                    f"duplicate evaluation_uid {evaluation_uid!r}"
                )
            seen_evaluation_uids.add(evaluation_uid)
            original_boxes = copy.deepcopy(scene["layout_boxes"])
            floor_boxes, floor_gate = _collision_gated_floor_prior(scene)
            relations = scene["repair_target_relations"]
            objects = objects_from_exported_boxes(original_boxes)
            proposals = proposals_from_exported_relations(relations)
            floor_movement = _movement(original_boxes, floor_boxes)
            try:
                total_movement_budget, max_edited_objects = _method_budget(
                    floor_movement,
                    args.budget_policy,
                    args.total_movement_cap,
                    args.edit_cap,
                    args.anchor_residual_cap,
                )
            except ValueError as error:
                raise ValueError(f"{evaluation_uid}: {error}") from error
            scene_config = replace(
                base_config,
                total_movement_budget=total_movement_budget,
                max_edited_objects=max_edited_objects,
            )
            original_centers = np.asarray(
                [
                    [box["translation"][0], box["translation"][2]]
                    for box in original_boxes
                ],
                dtype=np.float64,
            )
            floor_centers = np.asarray(
                [
                    [box["translation"][0], box["translation"][2]]
                    for box in floor_boxes
                ],
                dtype=np.float64,
            )

            mesh_safety_callback = None
            if (
                args.safety_mode == "cached_fcl"
                and floor_gate["mesh_gate_available"]
            ):
                baseline_mesh_pairs = float(
                    floor_gate["baseline_mesh_collision_pairs"]
                )
                selected_floor_pairs = (
                    float(floor_gate["repair_mesh_collision_pairs"])
                    if floor_gate["repair_accepted"]
                    else baseline_mesh_pairs
                )

                def _cached_mesh_safety(
                    centers,
                    original=original_centers,
                    floor=floor_centers,
                    baseline_pairs=baseline_mesh_pairs,
                    floor_pairs=selected_floor_pairs,
                ):
                    if np.allclose(centers, original, atol=1e-10, rtol=0.0):
                        return {"mesh_collision_pairs": baseline_pairs}
                    if np.allclose(centers, floor, atol=1e-10, rtol=0.0):
                        return {"mesh_collision_pairs": floor_pairs}
                    # No local FCL/assets: unknown candidates fail closed.
                    return {"mesh_collision_pairs": 1e12}

                mesh_safety_callback = _cached_mesh_safety

            cwgcp_result = repair_layout_cwgcp(
                objects,
                proposals,
                room_bounds=None,
                config=scene_config,
                external_safety_fn=mesh_safety_callback,
                warm_start_centers=[floor_centers],
                anchor_centers=(
                    floor_centers
                    if args.method_profile in {"fapsp_v03", "agrp_v04"}
                    else None
                ),
                external_safety_metadata={
                    "mode": args.safety_mode,
                    "archived_baseline_mesh_collision_pairs": (
                        floor_gate["baseline_mesh_collision_pairs"]
                    ),
                    "archived_repair_mesh_collision_pairs": (
                        floor_gate["repair_mesh_collision_pairs"]
                    ),
                    "evaluator_version": EVALUATOR_VERSION,
                },
                provenance={
                    "input_file": str(Path(input_path)),
                    "input_file_sha256": input_hashes[input_path],
                    "scene_uid": scene_uid,
                    "code_commit": code_commit,
                    "source_tree": source_tree,
                },
            )
            cwgcp_boxes = apply_centers_to_exported_boxes(
                original_boxes, cwgcp_result.centers_xz
            )
            cwgcp_movement = _movement(original_boxes, cwgcp_boxes)
            random_match = args.random_match
            if random_match == "auto":
                random_match = (
                    "candidate"
                    if args.method_profile in {"fapsp_v03", "agrp_v04"}
                    else "floor"
                )
            random_target = (
                cwgcp_movement if random_match == "candidate" else floor_movement
            )
            random_boxes, random_log = _movement_matched_random(
                original_boxes,
                total_budget=float(random_target["total"]),
                edit_budget=int(random_target["edited"]),
                per_object_budget=scene_config.per_object_budget,
                scene_uid=scene_uid,
                seed=args.seed,
            )

            variants = {
                "baseline": original_boxes,
                "floor_prior": floor_boxes,
                "random": random_boxes,
                "cwgcp": cwgcp_boxes,
            }
            generic_certificate = None
            if args.include_generic:
                generic_config = replace(
                    scene_config,
                    min_confidence=1.0,
                    max_slack=0.0,
                    coverage_first_selection=False,
                    require_coverage_gain=False,
                    enable_proposal_nudge=False,
                )
                generic_result = repair_layout_cwgcp(
                    objects,
                    [
                        replace(proposal, confidence=1.0)
                        for proposal in proposals
                    ],
                    room_bounds=None,
                    config=generic_config,
                    external_safety_fn=mesh_safety_callback,
                    warm_start_centers=[floor_centers],
                    anchor_centers=(
                        floor_centers
                        if args.method_profile in {"fapsp_v03", "agrp_v04"}
                        else None
                    ),
                    external_safety_metadata={
                        "mode": "obb_only_generic_control",
                        "evaluator_version": EVALUATOR_VERSION,
                    },
                    provenance={
                        "input_file": str(Path(input_path)),
                        "input_file_sha256": input_hashes[input_path],
                        "scene_uid": scene_uid,
                        "code_commit": code_commit,
                        "source_tree": source_tree,
                    },
                )
                variants["generic"] = apply_centers_to_exported_boxes(
                    original_boxes, generic_result.centers_xz
                )
                generic_certificate = generic_result.certificate

            selected_external = cwgcp_result.certificate["solver"][
                "selected_metrics"
            ].get("external_safety")
            baseline_mesh_value = (
                float(floor_gate["baseline_mesh_collision_pairs"])
                if floor_gate["mesh_gate_available"]
                else None
            )
            floor_mesh_value = (
                (
                    float(floor_gate["repair_mesh_collision_pairs"])
                    if floor_gate["repair_accepted"]
                    else baseline_mesh_value
                )
                if floor_gate["mesh_gate_available"]
                else None
            )
            cwgcp_mesh_value = (
                float(selected_external["mesh_collision_pairs"])
                if selected_external is not None
                else None
            )
            row = {
                "room": room,
                "scene_index": scene_index,
                "scene_uid": scene_uid,
                "evaluation_uid": evaluation_uid,
                "target_relation_count": len(relations),
                "method_total_movement_budget": total_movement_budget,
                "method_max_edited_objects": max_edited_objects,
                "random_match_target": random_match,
                "floor_mesh_gate_available": floor_gate["mesh_gate_available"],
                "floor_repair_accepted": floor_gate["repair_accepted"],
                "random_accepted": random_log["accepted"],
                "random_available": random_log["available"],
                "cwgcp_accepted": cwgcp_result.accepted,
                "cwgcp_runtime_seconds": cwgcp_result.certificate[
                    "runtime_seconds"
                ],
                "cwgcp_unresolved_relations": len(
                    cwgcp_result.certificate["unresolved_relations"]
                ),
                "cwgcp_selected_source": (
                    cwgcp_result.certificate["solver"]["selected_metrics"].get(
                        "candidate_source",
                        (
                            "anchor_rollback"
                            if args.method_profile in {"fapsp_v03", "agrp_v04"}
                            else "baseline_rollback"
                        ),
                    )
                ),
                "baseline_mesh_collision_pairs": baseline_mesh_value,
                "floor_prior_mesh_collision_pairs": floor_mesh_value,
                "cwgcp_mesh_collision_pairs": cwgcp_mesh_value,
            }
            for name, boxes in variants.items():
                evaluation = _evaluate_variant(boxes, relations)
                movement = _movement(original_boxes, boxes)
                _flatten_eval(row, name, evaluation, movement)
            rows.append(row)
            certificates.append(
                {
                    "room": room,
                    "scene_uid": scene_uid,
                    "floor_gate": floor_gate,
                    "random": random_log,
                    "cwgcp": cwgcp_result.certificate,
                    "cwgcp_boxes": cwgcp_boxes,
                    "generic": generic_certificate,
                }
            )
            if (scene_index + 1) % 25 == 0:
                print(f"  completed {scene_index + 1}/{len(scenes)}")

    methods = ["baseline", "floor_prior", "random", "cwgcp"]
    if args.include_generic:
        methods.append("generic")
    aggregate = {method: _aggregate(rows, method) for method in methods}
    comparisons = {
        "cwgcp_minus_baseline": _bootstrap_delta(
            rows, "cwgcp", "baseline", args.bootstrap_samples, args.seed + 11
        ),
        "cwgcp_minus_floor_prior": _bootstrap_delta(
            rows, "cwgcp", "floor_prior", args.bootstrap_samples, args.seed + 12
        ),
        "cwgcp_minus_random": _bootstrap_delta(
            rows, "cwgcp", "random", args.bootstrap_samples, args.seed + 13
        ),
    }
    if args.include_generic:
        comparisons["cwgcp_minus_generic"] = _bootstrap_delta(
            rows, "cwgcp", "generic", args.bootstrap_samples, args.seed + 14
        )

    room_deltas_vs_floor_prior = {
        room: _bootstrap_delta(
            [row for row in rows if row["room"] == room],
            "cwgcp",
            "floor_prior",
            args.bootstrap_samples,
            args.seed + 100 + room_index,
        )
        for room_index, room in enumerate(
            sorted(set(row["room"] for row in rows))
        )
    }
    runtimes = [float(row["cwgcp_runtime_seconds"]) for row in rows]
    movement_ratio = (
        aggregate["cwgcp"]["mean_total_movement"]
        / aggregate["floor_prior"]["mean_total_movement"]
        if aggregate["floor_prior"]["mean_total_movement"] > 0
        else 1.0
    )
    selected_source_counts = {
        source: int(
            sum(row["cwgcp_selected_source"] == source for row in rows)
        )
        for source in sorted(
            set(row["cwgcp_selected_source"] for row in rows)
        )
    }
    selected_method_candidate_count = sum(
        count
        for source, count in selected_source_counts.items()
        if source not in {"anchor_rollback", "baseline_rollback"}
    )
    generic_signal = (
        not args.include_generic
        or comparisons["cwgcp_minus_generic"]["low"] > 0
    )
    cpu_method_signal = bool(
        comparisons["cwgcp_minus_baseline"]["low"] > 0
        and comparisons["cwgcp_minus_random"]["low"] > 0
        and comparisons["cwgcp_minus_floor_prior"]["low"] > 0
        and generic_signal
        and all(
            interval["mean"] > 0
            for interval in room_deltas_vs_floor_prior.values()
        )
        and 0.95 <= movement_ratio <= 1.05
        and selected_method_candidate_count > 0
        and aggregate["cwgcp"]["mean_obb_collision_pairs"]
        <= aggregate["floor_prior"]["mean_obb_collision_pairs"] + 1e-9
        and aggregate["cwgcp"]["mean_obb_overlap_area"]
        <= aggregate["floor_prior"]["mean_obb_overlap_area"] + 1e-9
    )
    summary = {
        "algorithm": (
            {
                "fapsp_v03": "FA-PSP 0.3 exploratory pilot",
                "agrp_v04": "AGRP 0.4 exploratory pilot",
            }.get(args.method_profile, "CW-GCP 0.2.1 CPU pilot")
        ),
        "code_commit": code_commit,
        "source_tree": source_tree,
        "evaluator": {
            "version": EVALUATOR_VERSION,
            "close_distance": EVALUATOR_CLOSE_DISTANCE,
        },
        "scene_count": len(rows),
        "unique_evaluation_uid_count": len(seen_evaluation_uids),
        "unique_source_scene_uid_count": len(
            set(row["scene_uid"] for row in rows)
        ),
        "rooms": sorted(set(row["room"] for row in rows)),
        "safety_mode": args.safety_mode,
        "method_profile": args.method_profile,
        "budget_policy": {
            "name": args.budget_policy,
            "total_movement_cap": args.total_movement_cap,
            "edit_cap": args.edit_cap,
            "anchor_residual_cap": args.anchor_residual_cap,
            "random_match": args.random_match,
        },
        "split": {
            "name": args.split,
            "salt": args.split_salt,
            "development_fraction": args.development_fraction,
        },
        "config": asdict(base_config),
        "generic_control": (
            {
                "same_anchor_budget_warm_starts_and_safety": True,
                "confidence_weighting": False,
                "slack": False,
                "coverage_first_selection": False,
                "strict_coverage_gain_gate": False,
                "proposal_nudge_candidates": False,
            }
            if args.include_generic
            else None
        ),
        "methods": aggregate,
        "paired_deltas": comparisons,
        "room_deltas_vs_floor_prior": room_deltas_vs_floor_prior,
        "accepted_scenes": int(sum(row["cwgcp_accepted"] for row in rows)),
        "random_available_scenes": int(
            sum(row["random_available"] for row in rows)
        ),
        "selected_source_counts": selected_source_counts,
        "selected_method_candidate_count": selected_method_candidate_count,
        "movement_ratio_vs_floor_prior": float(movement_ratio),
        "runtime_median_seconds": float(statistics.median(runtimes))
        if runtimes
        else 0.0,
        "runtime_p95_seconds": float(np.quantile(runtimes, 0.95))
        if runtimes
        else 0.0,
        "external_fcl_available": False,
        "archived_warm_start_fcl_scenes": int(
            sum(row["floor_mesh_gate_available"] for row in rows)
        ),
        "selected_layout_cached_fcl_available": bool(
            args.safety_mode == "cached_fcl"
            and all(row["floor_mesh_gate_available"] for row in rows)
        ),
        "new_candidate_fcl_recomputation_available": False,
        "human_audit_available": False,
        "true_room_boundary_available": False,
        "cpu_method_signal": cpu_method_signal,
        "cpu_solver_signal": cpu_method_signal,
        "cpu_pilot_go": cpu_method_signal,
        # Deliberately fail closed: local OBB evidence cannot promote the paper
        # method without the predeclared mesh and human-audit gates.
        "method_upgrade_go": False,
        "duration_seconds": float(time.perf_counter() - started),
        "inputs": inputs,
    }
    _write_outputs(Path(args.output_dir), rows, certificates, summary)
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
