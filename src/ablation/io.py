"""I/O utilities for loading exported scene .npz files and saving metrics."""

import json
import os
import csv
from typing import Dict, List, Any

import numpy as np


def load_scenes_from_dir(input_dir: str) -> List[Dict[str, Any]]:
    """Load all scene_*.npz files from a directory, sorted by index.

    Returns a list of dicts, each containing all npz arrays plus a
    'scene_index' key parsed from the filename.
    """
    scenes = []
    for fname in sorted(os.listdir(input_dir)):
        if not fname.startswith("scene_") or not fname.endswith(".npz"):
            continue
        path = os.path.join(input_dir, fname)
        data = dict(np.load(path, allow_pickle=True))
        data["scene_index"] = int(
            fname.replace("scene_", "").replace(".npz", "")
        )
        scenes.append(data)
    return scenes


def load_metadata(input_dir: str) -> Dict[str, Any]:
    """Load metadata.json from an export directory."""
    path = os.path.join(input_dir, "metadata.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"metadata.json not found in {input_dir}")
    with open(path) as f:
        return json.load(f)


def load_bounds(bounds_path: str) -> Dict[str, np.ndarray]:
    """Load bounds.npz (dataset scale bounds from training).

    Keys: 'translations' (2,3), 'sizes' (2,3), 'angles' (2,).
    """
    bounds = dict(np.load(bounds_path, allow_pickle=True))
    return bounds


def save_metrics(
    output_dir: str,
    per_scene: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    run_args: Dict[str, Any],
    summary_md: str,
) -> None:
    """Write all metrics outputs to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    # --- metrics_per_scene.csv ---
    if per_scene:
        fieldnames = list(per_scene[0].keys())
        csv_path = os.path.join(output_dir, "metrics_per_scene.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(per_scene)

    # --- metrics_aggregate.csv ---
    if aggregate:
        agg_path = os.path.join(output_dir, "metrics_aggregate.csv")
        with open(agg_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            for k, v in aggregate.items():
                writer.writerow([k, v])

    # --- run_args.json ---
    with open(os.path.join(output_dir, "run_args.json"), "w") as f:
        json.dump(run_args, f, indent=2)

    # --- summary.md ---
    with open(os.path.join(output_dir, "summary.md"), "w") as f:
        f.write(summary_md)


def save_repaired_scenes(
    output_dir: str, scenes: List[Dict[str, Any]]
) -> None:
    """Save repaired bbox_params as scene_*.npz files in repaired_layouts/."""
    layout_dir = os.path.join(output_dir, "repaired_layouts")
    os.makedirs(layout_dir, exist_ok=True)
    for scene in scenes:
        idx = scene["scene_index"]
        out = {}
        for key in (
            "bbox_params", "objs", "edges", "obj_masks",
            "objfeat_vq_indices", "objfeats",
        ):
            if key in scene:
                out[key] = scene[key]
        if "text" in scene:
            out["text"] = scene["text"]
        np.savez(os.path.join(layout_dir, f"scene_{idx:06d}.npz"), **out)
