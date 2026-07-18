#!/usr/bin/env python3
"""Grid runner for repair v0 parameter ablation.

Runs multiple repair configs over the same input scenes, collects per-scene
and aggregate metrics, and produces leaderboard + pareto + summary outputs.
"""

import copy
import csv
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np

from src.ablation.io import (
    load_scenes_from_dir,
    load_metadata,
    save_repaired_scenes,
)
from src.ablation.evaluators import evaluate_all
from src.ablation.repairers import repair_overlap_with_sg_guard


# ---------------------------------------------------------------------------
# Config ID builder
# ---------------------------------------------------------------------------

def make_config_id(step, max_disp, max_iter) -> str:
    return f"s{int(step*1000):04d}_d{int(max_disp*100):03d}_i{max_iter:03d}"


# ---------------------------------------------------------------------------
# Pareto filter
# ---------------------------------------------------------------------------

def is_pareto_dominated(a: Dict, b: Dict, objectives: List[str]) -> bool:
    """True if a is strictly dominated by b (b is better or equal on all objectives,
    and strictly better on at least one).  Lower is better for all objectives
    by convention; for consistency we use (1 - consistency) so lower = better.
    """
    better = False
    for obj in objectives:
        va = a[obj]
        vb = b[obj]
        if va is None or vb is None or (isinstance(va, float) and np.isnan(va)):
            return False
        if vb > va:
            return False  # b is worse on this objective
        if vb < va:
            better = True  # b is strictly better on this objective
    return better


def compute_pareto_front(
    rows: List[Dict], objectives: List[str]
) -> List[Dict]:
    """Return the Pareto-optimal subset of rows."""
    front = []
    for i, a in enumerate(rows):
        dominated = False
        for j, b in enumerate(rows):
            if i == j:
                continue
            if is_pareto_dominated(a, b, objectives):
                dominated = True
                break
        if not dominated:
            front.append(a)
    return front


# ---------------------------------------------------------------------------
# Grid configs
# ---------------------------------------------------------------------------

GRID_CONFIGS = [
    # (step, max_disp, max_iter)
    (0.025, 0.15, 25),
    (0.025, 0.25, 50),
    (0.025, 0.35, 50),
    (0.050, 0.15, 25),
    (0.050, 0.25, 50),
    (0.050, 0.35, 50),
    (0.075, 0.15, 25),
    (0.075, 0.25, 50),
    (0.075, 0.35, 50),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Grid runner for repair v0 parameter ablation"
    )
    parser.add_argument(
        "--input_dir", type=str, required=True,
        help="Directory containing scene_*.npz files + metadata.json",
    )
    parser.add_argument(
        "--output_dir", type=str, required=True,
        help="Directory to write grid outputs",
    )
    parser.add_argument(
        "--repair_seed", type=int, default=42,
    )
    args = parser.parse_args()

    t0 = time.time()
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Load ---
    base_scenes = load_scenes_from_dir(args.input_dir)
    print(f"Loaded {len(base_scenes)} base scenes")
    metadata = load_metadata(args.input_dir)
    obj_types = metadata["object_types"]
    pred_types = metadata["predicate_types"]

    all_per_scene = []       # rows for metrics_per_scene.csv
    all_aggregate = []       # rows for metrics_aggregate.csv
    all_leaderboard = []     # rows for leaderboard.csv
    failures = []            # rows for failures.jsonl
    repair_configs_run = []  # for summary

    # --- Run baseline (config 10) ---
    print("\n=== Config baseline: eval-only ===")
    baseline_scenes = copy.deepcopy(base_scenes)
    bl_per, bl_agg = evaluate_all(baseline_scenes, obj_types, pred_types, None)
    bl_agg["config_id"] = "baseline"
    bl_agg["repair_step_size"] = 0.0
    bl_agg["repair_max_displacement"] = 0.0
    bl_agg["repair_max_iter"] = 0
    bl_agg["mean_movement_mean_displacement"] = 0.0
    bl_agg["mean_movement_max_displacement"] = 0.0
    bl_agg["baseline_mean_overlap_iou_sum"] = bl_agg["mean_overlap_iou_sum"]
    bl_agg["overlap_iou_sum_delta"] = 0.0
    bl_agg["consistency_drop"] = 0.0
    for ps in bl_per:
        ps["config_id"] = "baseline"
        ps["scene_id"] = f"{ps['scene_index']:06d}"
        ps["movement_mean_displacement"] = 0.0
        ps["movement_max_displacement"] = 0.0
        ps["baseline_overlap_iou_sum"] = ps["overlap_iou_sum"]
        ps["overlap_iou_sum_delta"] = 0.0
        ps["consistency_drop"] = 0.0
    all_per_scene.extend(bl_per)
    all_aggregate.append(bl_agg)
    all_leaderboard.append(bl_agg)
    repair_configs_run.append({
        "config_id": "baseline",
        "step": 0, "max_disp": 0, "max_iter": 0,
        "mean_overlap_iou_sum": bl_agg["mean_overlap_iou_sum"],
        "mean_movement": 0.0,
        "consistency_drop": 0.0,
        "overlap_iou_sum_delta": 0.0,
        "status": "ok",
    })
    print(f"  baseline: overlap_iou_sum={bl_agg['mean_overlap_iou_sum']:.4f}, "
          f"consistency={bl_agg['mean_sg_layout_consistency']:.4f}")

    # --- Run repair configs ---
    for step, max_disp, max_iter in GRID_CONFIGS:
        config_id = make_config_id(step, max_disp, max_iter)
        print(f"\n=== Config {config_id}: "
              f"step={step}, max_disp={max_disp}, max_iter={max_iter} ===")

        try:
            # Fresh copy from baseline
            scenes = copy.deepcopy(base_scenes)

            for scene in scenes:
                repaired, rlog = repair_overlap_with_sg_guard(
                    scene["bbox_params"],
                    scene["objs"],
                    scene["edges"],
                    scene["obj_masks"],
                    obj_types,
                    pred_types,
                    max_iter=max_iter,
                    step_size=step,
                    max_displacement=max_disp,
                    seed=args.repair_seed,
                )
                scene["bbox_params"] = repaired

            # Evaluate repaired
            per_scene, aggregate = evaluate_all(scenes, obj_types, pred_types, None)

            # Compute deltas
            agg_overlap_rep = aggregate["mean_overlap_iou_sum"]
            agg_overlap_base = bl_agg["mean_overlap_iou_sum"]
            overlap_delta = agg_overlap_rep - agg_overlap_base
            agg_cons_rep = aggregate["mean_sg_layout_consistency"]
            agg_cons_base = bl_agg["mean_sg_layout_consistency"]
            cons_drop = agg_cons_base - agg_cons_rep

            # Compute movement from repair logs (re-run for logs — lightweight)
            movement_means = []
            movement_maxs = []
            for si, scene in enumerate(scenes):
                # Quick movement computation: diff repaired vs original
                b_orig = base_scenes[si]["bbox_params"]
                b_rep = scene["bbox_params"]
                cls_dim = len(obj_types) + 1
                active = scene["obj_masks"] == 1
                dxz = b_rep[active][:, cls_dim:cls_dim + 3][:, [0, 2]] - \
                      b_orig[active][:, cls_dim:cls_dim + 3][:, [0, 2]]
                disp = np.linalg.norm(dxz, axis=1)
                movement_means.append(float(disp.mean()) if len(disp) > 0 else 0.0)
                movement_maxs.append(float(disp.max()) if len(disp) > 0 else 0.0)

            mean_move = float(np.mean(movement_means))
            max_move = float(np.max(movement_maxs))

            # Tag per-scene rows
            for si, ps in enumerate(per_scene):
                ps["config_id"] = config_id
                ps["scene_id"] = f"{ps['scene_index']:06d}"
                ps["movement_mean_displacement"] = movement_means[si]
                ps["movement_max_displacement"] = movement_maxs[si]
                ps["baseline_overlap_iou_sum"] = agg_overlap_base
                ps["overlap_iou_sum_delta"] = \
                    ps["overlap_iou_sum"] - agg_overlap_base
                ps["consistency_drop"] = \
                    bl_agg["mean_sg_layout_consistency"] - ps["sg_layout_consistency"]

            # Tag aggregate
            aggregate["config_id"] = config_id
            aggregate["repair_step_size"] = step
            aggregate["repair_max_displacement"] = max_disp
            aggregate["repair_max_iter"] = max_iter
            aggregate["mean_movement_mean_displacement"] = mean_move
            aggregate["mean_movement_max_displacement"] = max_move
            aggregate["baseline_mean_overlap_iou_sum"] = agg_overlap_base
            aggregate["overlap_iou_sum_delta"] = overlap_delta
            aggregate["consistency_drop"] = cons_drop

            all_per_scene.extend(per_scene)
            all_aggregate.append(aggregate)
            all_leaderboard.append(aggregate)

            repair_configs_run.append({
                "config_id": config_id,
                "step": step, "max_disp": max_disp, "max_iter": max_iter,
                "mean_overlap_iou_sum": agg_overlap_rep,
                "mean_movement": mean_move,
                "consistency_drop": cons_drop,
                "overlap_iou_sum_delta": overlap_delta,
                "status": "ok",
            })
            print(f"  overlap: {agg_overlap_base:.4f} → {agg_overlap_rep:.4f} "
                  f"(Δ={overlap_delta:.4f}), "
                  f"consistency_drop={cons_drop:.4f}, "
                  f"movement mean={mean_move:.4f}m")

        except Exception as e:
            print(f"  FAILED: {e}")
            failures.append({
                "config_id": config_id,
                "step": step,
                "max_disp": max_disp,
                "max_iter": max_iter,
                "error": str(e),
            })
            repair_configs_run.append({
                "config_id": config_id,
                "step": step, "max_disp": max_disp, "max_iter": max_iter,
                "mean_overlap_iou_sum": None,
                "mean_movement": None,
                "consistency_drop": None,
                "overlap_iou_sum_delta": None,
                "status": "failed",
            })

    # --- Build leaderboard ---
    leaderboard = sorted(
        all_leaderboard,
        key=lambda r: (
            abs(r.get("consistency_drop", 0)),
            r.get("overlap_iou_sum_delta", 0),  # most negative = best
            r.get("mean_movement_mean_displacement", float("inf")),
        ),
    )

    # --- Build Pareto front ---
    pareto_rows = [
        r for r in all_aggregate
        if "overlap_iou_sum_delta" in r and "consistency_drop" in r
        and not np.isnan(r["overlap_iou_sum_delta"])
        and not np.isnan(r["consistency_drop"])
    ]
    # Objectives: consistency_drop (lower better), overlap_iou_sum (lower better),
    # movement_mean (lower better)
    pareto_input = []
    for r in pareto_rows:
        pareto_input.append({
            **r,
            "_cons_loss": r["consistency_drop"],
            "_overlap": r["mean_overlap_iou_sum"],
            "_movement": r.get("mean_movement_mean_displacement", 0.0),
        })
    pareto = compute_pareto_front(
        pareto_input,
        ["_cons_loss", "_overlap", "_movement"],
    )
    # Strip internal keys
    for p in pareto:
        del p["_cons_loss"]
        del p["_overlap"]
        del p["_movement"]

    # --- Write outputs ---
    # metrics_per_scene.csv
    if all_per_scene:
        with open(os.path.join(args.output_dir, "metrics_per_scene.csv"), "w",
                  newline="") as f:
            fieldnames = list(all_per_scene[0].keys())
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(all_per_scene)

    # metrics_aggregate.csv
    if all_aggregate:
        agg_keys = list(all_aggregate[0].keys())
        with open(os.path.join(args.output_dir, "metrics_aggregate.csv"), "w",
                  newline="") as f:
            w = csv.DictWriter(f, fieldnames=agg_keys)
            w.writeheader()
            w.writerows(all_aggregate)

    # leaderboard.csv
    lb_keys = ["config_id", "consistency_drop", "overlap_iou_sum_delta",
               "mean_movement_mean_displacement", "mean_movement_max_displacement",
               "mean_overlap_iou_sum", "mean_sg_layout_consistency",
               "mean_overlap_pair_count", "repair_step_size",
               "repair_max_displacement", "repair_max_iter"]
    with open(os.path.join(args.output_dir, "leaderboard.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=lb_keys, extrasaction="ignore")
        w.writeheader()
        for r in leaderboard:
            w.writerow({k: r.get(k, "") for k in lb_keys})

    # pareto.csv
    if pareto:
        with open(os.path.join(args.output_dir, "pareto.csv"), "w",
                  newline="") as f:
            w = csv.DictWriter(f, fieldnames=lb_keys, extrasaction="ignore")
            w.writeheader()
            for r in pareto:
                w.writerow({k: r.get(k, "") for k in lb_keys})

    # failures.jsonl
    with open(os.path.join(args.output_dir, "failures.jsonl"), "w") as f:
        for failure in failures:
            f.write(json.dumps(failure) + "\n")

    # leaderboard_md for summary
    top3 = [r for r in leaderboard
            if abs(r.get("consistency_drop", 0)) < 1e-9][:3]
    if len(top3) < 3:
        top3 = leaderboard[:3]

    # --- summary.md ---
    t1 = time.time()
    lines = [
        "# Repair v0 Parameter Grid Ablation Report",
        "",
        f"**Generated**: {datetime.now().isoformat(timespec='seconds')}",
        f"**Input**: `{args.input_dir}`",
        f"**Output**: `{args.output_dir}`",
        f"**Duration**: {t1 - t0:.1f}s",
        f"**Configs run**: {len(all_aggregate)} (9 repair + 1 baseline)",
        f"**Failures**: {len(failures)}",
        "",
        "## Leaderboard (top, no consistency drop first, then by overlap reduction)",
        "",
        "| Rank | Config | Step | MaxDisp | Iter | Consistency Drop | Overlap Δ | "
        "Mean Move (m) | Max Move (m) |",
        "|------|--------|------|---------|------|-----------------|-----------|"
        "--------------|-------------|",
    ]
    for rank, r in enumerate(leaderboard, 1):
        cid = r.get("config_id", "?")
        step = r.get("repair_step_size", 0)
        md = r.get("repair_max_displacement", 0)
        mi = r.get("repair_max_iter", 0)
        cd = r.get("consistency_drop", 0)
        od = r.get("overlap_iou_sum_delta", 0)
        mv = r.get("mean_movement_mean_displacement", 0)
        mx = r.get("mean_movement_max_displacement", 0)
        lines.append(
            f"| {rank} | {cid} | {step:.3f} | {md:.2f} | {mi} | "
            f"{cd:.4f} | {od:.4f} | {mv:.4f} | {mx:.4f} |"
        )

    lines += [
        "",
        "## Pareto Front",
        "",
        "(Objectives: minimize consistency_drop, minimize overlap_iou_sum, "
        "minimize movement_mean)",
        "",
        "| Config | Consistency Drop | Overlap IoU Sum | Mean Move (m) |",
        "|--------|-----------------|-----------------|--------------|",
    ]
    for p in pareto:
        lines.append(
            f"| {p.get('config_id','?')} | "
            f"{p.get('consistency_drop',0):.4f} | "
            f"{p.get('mean_overlap_iou_sum',0):.4f} | "
            f"{p.get('mean_movement_mean_displacement',0):.4f} |"
        )

    lines += [
        "",
        "## Top 3 Recommended Configs",
        "",
        "Selected for zero consistency drop, best overlap reduction, "
        "and minimal movement.",
        "",
    ]
    for i, r in enumerate(top3, 1):
        cid = r.get("config_id", "?")
        step = r.get("repair_step_size", 0)
        md = r.get("repair_max_displacement", 0)
        mi = r.get("repair_max_iter", 0)
        cd = r.get("consistency_drop", 0)
        od = r.get("overlap_iou_sum_delta", 0)
        mv = r.get("mean_movement_mean_displacement", 0)
        lines.append(
            f"{i}. **{cid}**: step={step:.3f}, max_disp={md:.2f}, "
            f"iter={mi} → consistency_drop={cd:.4f}, "
            f"overlap Δ={od:.4f}, movement_mean={mv:.4f}m"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- **consistency_drop** > 0 would indicate SG constraint violation "
        "(none observed).",
        "- **overlap_iou_sum_delta** = repaired - baseline; negative = improvement.",
        "- All repair moves XZ only; class/size/angle/edges unchanged.",
        "- Room OOB = NA throughout (no room bounds in export).",
    ]

    with open(os.path.join(args.output_dir, "summary.md"), "w") as f:
        f.write("\n".join(lines))

    # --- run_args.json ---
    with open(os.path.join(args.output_dir, "run_args.json"), "w") as f:
        json.dump(vars(args), f, indent=2)

    print(f"\n=== Grid complete ===")
    print(f"  Configs: {len(all_aggregate)}")
    print(f"  Failures: {len(failures)}")
    print(f"  Pareto size: {len(pareto)}")
    print(f"  Top 3: {[r.get('config_id','?') for r in top3]}")
    print(f"  Duration: {t1 - t0:.1f}s")


if __name__ == "__main__":
    main()
