#!/usr/bin/env python3
"""Ablation runner — eval-only baseline or repair-then-eval.

Loads exported scene_*.npz files, optionally applies overlap-reduction repair
with SG consistency guard, then runs bbox-level evaluators
(no mesh / retrieval / render), and writes metrics to an output directory.

Usage (eval-only):
    python3 src/ablation_runner.py \
        --input_dir outputs/official_baseline/bedroom_export_5scene_seed42 \
        --output_dir outputs/ablations/baseline_eval_5scene_seed42 \
        --bounds_path out/bedroom_sgdiffusion_vq_objfeat/bounds.npz

Usage (repair + eval):
    python3 src/ablation_runner.py \
        --input_dir ... --output_dir ... \
        --repair \
        --repair_max_iter 50 --repair_step_size 0.05 --repair_max_displacement 0.25
"""

import argparse
import copy
import json
import os
import sys
import time
from datetime import datetime

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ablation.io import (
    load_scenes_from_dir,
    load_metadata,
    load_bounds,
    save_metrics,
    save_repaired_scenes,
)
from src.ablation.evaluators import evaluate_all, evaluate_scene
from src.ablation.repairers import repair_overlap_with_sg_guard


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def build_summary_md(
    per_scene, aggregate, run_args, input_dir, output_dir, duration_s, repair_logs
) -> str:
    """Build a human-readable summary.md string."""
    agg = aggregate
    n = agg.get("n_scenes", 0)
    repair_mode = run_args.get("repair", False)

    title = "# Repair v0 Baseline Ablation Report" if repair_mode else "# Ablation Baseline Eval Report"
    lines = [
        title,
        "",
        f"**Generated**: {datetime.now().isoformat(timespec='seconds')}",
        f"**Input**: `{input_dir}`",
        f"**Output**: `{output_dir}`",
        f"**Duration**: {duration_s:.1f}s",
        f"**Scenes evaluated**: {n}",
    ]

    if repair_mode:
        lines += [
            f"**Repair**: overlap reduction + SG consistency guard",
            f"**max_iter**: {run_args.get('repair_max_iter', 50)}",
            f"**step_size**: {run_args.get('repair_step_size', 0.05)} m",
            f"**max_displacement**: {run_args.get('repair_max_displacement', 0.25)} m",
        ]

    lines += [
        "",
        "## Aggregate Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
    ]
    metric_labels = {
        "mean_n_active_objects": "Mean active objects",
        "mean_overlap_pair_count": "Mean overlapping pairs",
        "mean_overlap_iou_sum": "Mean overlap IoU sum",
        "mean_mean_pair_iou": "Mean per-pair IoU",
        "mean_total_pairs": "Mean object pairs",
        "mean_sg_total_constraints": "Mean SG constraints",
        "mean_sg_satisfied_constraints": "Mean satisfied constraints",
        "mean_sg_layout_consistency": "SG-Layout Consistency",
        "mean_sg_layout_consistency_easy": "SG-Layout Consistency (easy)",
        "mean_movement_mean_displacement": "Mean movement displacement (m)",
        "mean_movement_max_displacement": "Mean max displacement per scene (m)",
        "mean_proxy_translation_violation_rate": "Translation violation rate (proxy)",
        "room_oob": "Room OOB",
        "n_scenes": "Scene count",
    }
    for k, v in agg.items():
        label = metric_labels.get(k, k)
        if isinstance(v, float):
            lines.append(f"| {label} | {v:.4f} |")
        else:
            lines.append(f"| {label} | {v} |")

    if repair_logs:
        lines += [
            "",
            "## Per-Scene Repair Logs",
            "",
            "| Scene | Moves | Baseline IoU Sum | Repaired IoU Sum | "
            "Baseline Cons. | Repaired Cons. | Mean Move (m) | Max Move (m) |",
            "|-------|-------|-----------------|-----------------|"
            "---------------|---------------|--------------|-------------|",
        ]
        for rl in repair_logs:
            lines.append(
                f"| {rl['scene_index']} | {rl['accepted_moves']} | "
                f"{rl['baseline_overlap_iou_sum']:.4f} | "
                f"{rl['repaired_overlap_iou_sum']:.4f} | "
                f"{rl['baseline_sg_consistency']:.4f} | "
                f"{rl['repaired_sg_consistency']:.4f} | "
                f"{rl['movement_mean']:.4f} | "
                f"{rl['movement_max']:.4f} |"
            )

    lines += [
        "",
        "## Notes",
        "",
        "- **room_oob**: NA — no room geometry in export.",
        "- **sg_layout_consistency**: Generated bbox vs. generated scene graph edges. "
        "NOT official relation accuracy (no GT).",
        "- **overlap**: Ground-plane (XZ) oriented bbox polygon IoU via shapely.",
    ]
    if repair_mode:
        lines.append(
            "- **repair**: Overlap reduction pushing objects apart in XZ, "
            "guarded by SG consistency (must not drop below baseline). "
            "Per-object max displacement capped at 0.25m."
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Ablation runner — eval-only or repair+eval"
    )
    parser.add_argument(
        "--input_dir", type=str, required=True,
        help="Directory containing scene_*.npz files + metadata.json",
    )
    parser.add_argument(
        "--output_dir", type=str, required=True,
        help="Directory to write metrics outputs",
    )
    parser.add_argument(
        "--bounds_path", type=str, default=None,
        help="Path to bounds.npz for dataset_bounds_violation_proxy (optional)",
    )
    parser.add_argument(
        "--repair", action="store_true",
        help="Enable overlap-reduction repair with SG consistency guard",
    )
    parser.add_argument(
        "--repair_max_iter", type=int, default=50,
        help="Max repair iterations (default: 50)",
    )
    parser.add_argument(
        "--repair_step_size", type=float, default=0.05,
        help="Per-iteration push step in meters (default: 0.05)",
    )
    parser.add_argument(
        "--repair_max_displacement", type=float, default=0.25,
        help="Max per-object cumulative displacement in meters (default: 0.25)",
    )
    parser.add_argument(
        "--repair_seed", type=int, default=42,
        help="RNG seed for repair (default: 42)",
    )
    args = parser.parse_args()

    t0 = time.time()

    # --- Load ---
    print(f"Loading scenes from {args.input_dir}")
    scenes = load_scenes_from_dir(args.input_dir)
    print(f"  Loaded {len(scenes)} scene(s)")
    if len(scenes) == 0:
        print("ERROR: No scene files found.")
        sys.exit(1)

    metadata = load_metadata(args.input_dir)
    print(f"  Metadata: {metadata['n_object_types']} object types, "
          f"{metadata['n_predicate_types']} predicate types")

    obj_types = metadata["object_types"]
    pred_types = metadata["predicate_types"]

    bounds = None
    if args.bounds_path:
        if os.path.exists(args.bounds_path):
            bounds = load_bounds(args.bounds_path)
            print(f"  Bounds loaded from {args.bounds_path}")
        else:
            print(f"  WARNING: bounds_path={args.bounds_path} not found")

    # --- Repair (optional) ---
    repair_logs = []
    if args.repair:
        print(f"\nRepair: overlap reduction + SG guard")
        print(f"  max_iter={args.repair_max_iter}, "
              f"step_size={args.repair_step_size}, "
              f"max_displacement={args.repair_max_displacement}")

        for scene in scenes:
            idx = scene["scene_index"]
            bbox_orig = scene["bbox_params"]
            repaired, rlog = repair_overlap_with_sg_guard(
                bbox_orig,
                scene["objs"],
                scene["edges"],
                scene["obj_masks"],
                obj_types,
                pred_types,
                max_iter=args.repair_max_iter,
                step_size=args.repair_step_size,
                max_displacement=args.repair_max_displacement,
                seed=args.repair_seed,
            )
            scene["bbox_params"] = repaired
            rlog["scene_index"] = idx
            repair_logs.append(rlog)
            print(f"  scene_{idx:06d}: {rlog['accepted_moves']} moves, "
                  f"IoU sum {rlog['baseline_overlap_iou_sum']:.4f} → "
                  f"{rlog['repaired_overlap_iou_sum']:.4f}, "
                  f"cons {rlog['baseline_sg_consistency']:.4f} → "
                  f"{rlog['repaired_sg_consistency']:.4f}, "
                  f"move mean={rlog['movement_mean']:.3f}m max={rlog['movement_max']:.3f}m")

        save_repaired_scenes(args.output_dir, scenes)
        print(f"  Repaired layouts saved to {args.output_dir}/repaired_layouts/")

    # --- Evaluate ---
    print("\nEvaluating...")
    per_scene, aggregate = evaluate_all(
        scenes, obj_types, pred_types, bounds,
    )

    # Inject per-object movement from repair logs
    if repair_logs:
        for i, ps in enumerate(per_scene):
            ps["movement_mean_displacement"] = repair_logs[i]["movement_mean"]
            ps["movement_max_displacement"] = repair_logs[i]["movement_max"]
        all_movement_mean = [r["movement_mean"] for r in repair_logs]
        all_movement_max = [r["movement_max"] for r in repair_logs]
        aggregate["mean_movement_mean_displacement"] = float(
            sum(all_movement_mean) / len(all_movement_mean)
        )
        aggregate["mean_movement_max_displacement"] = float(
            max(all_movement_max)
        )

    # --- Save ---
    t1 = time.time()
    duration = t1 - t0

    run_args = vars(args)

    summary_md = build_summary_md(
        per_scene, aggregate, run_args, args.input_dir, args.output_dir,
        duration, repair_logs,
    )

    save_metrics(args.output_dir, per_scene, aggregate, run_args, summary_md)
    print(f"\nMetrics written to {args.output_dir}")
    print(f"  Duration: {duration:.1f}s")
    print(f"  Scenes: {len(scenes)}")
    print(f"  Mean sg_layout_consistency: "
          f"{aggregate.get('mean_sg_layout_consistency', float('nan')):.4f}")
    print(f"  Mean overlap_pair_count: "
          f"{aggregate.get('mean_overlap_pair_count', float('nan')):.2f}")


if __name__ == "__main__":
    main()
