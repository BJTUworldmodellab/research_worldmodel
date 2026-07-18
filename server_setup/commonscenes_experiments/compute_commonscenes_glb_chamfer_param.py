import argparse
import glob
import json
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree


def load_scene_mesh(path):
    obj = trimesh.load(path, force="scene")
    if isinstance(obj, trimesh.Scene):
        geoms = []
        for geom in obj.geometry.values():
            if isinstance(geom, trimesh.Trimesh) and len(geom.vertices) > 0 and len(geom.faces) > 0:
                geoms.append(geom)
        if not geoms:
            return None
        return trimesh.util.concatenate(geoms)
    return obj if isinstance(obj, trimesh.Trimesh) else None


def sample(mesh, n=2500):
    try:
        points, _ = trimesh.sample.sample_surface(mesh, n)
    except Exception:
        points = mesh.vertices
        if len(points) > n:
            rng = np.random.default_rng(0)
            points = points[rng.choice(len(points), n, replace=False)]
    return np.asarray(points, dtype=np.float32)


def chamfer(a, b):
    tree_a = cKDTree(a)
    tree_b = cKDTree(b)
    dist_a, _ = tree_b.query(a, k=1)
    dist_b, _ = tree_a.query(b, k=1)
    return float(dist_a.mean() + dist_b.mean()), float(dist_a.mean()), float(dist_b.mean())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-glb", required=True)
    parser.add_argument("--ours-glb", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--samples", type=int, default=2500)
    args = parser.parse_args()

    base_dir = Path(args.base_glb)
    ours_dir = Path(args.ours_glb)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for base_path in sorted(base_dir.glob("*.glb")):
        ours_path = ours_dir / base_path.name
        if not ours_path.exists():
            rows.append({"scan": base_path.stem, "error": "missing_ours"})
            continue
        base_mesh = load_scene_mesh(base_path)
        ours_mesh = load_scene_mesh(ours_path)
        if base_mesh is None or ours_mesh is None:
            rows.append({"scan": base_path.stem, "error": "load_failed"})
            continue
        base_points = sample(base_mesh, args.samples)
        ours_points = sample(ours_mesh, args.samples)
        cd, base_to_ours, ours_to_base = chamfer(base_points, ours_points)
        rows.append(
            {
                "scan": base_path.stem,
                "chamfer": cd,
                "baseline_to_generic": base_to_ours,
                "generic_to_baseline": ours_to_base,
                "baseline_vertices": int(len(base_mesh.vertices)),
                "generic_vertices": int(len(ours_mesh.vertices)),
            }
        )

    valid = [row for row in rows if "chamfer" in row]
    values = [row["chamfer"] for row in valid]
    summary = {
        "scenes": len(rows),
        "valid": len(valid),
        "mean_chamfer": float(np.mean(values)) if values else None,
        "median_chamfer": float(np.median(values)) if values else None,
        "max_chamfer": float(np.max(values)) if values else None,
        "mean_baseline_to_generic": float(np.mean([row["baseline_to_generic"] for row in valid])) if valid else None,
        "mean_generic_to_baseline": float(np.mean([row["generic_to_baseline"] for row in valid])) if valid else None,
        "top_chamfer": sorted(valid, key=lambda row: row["chamfer"], reverse=True)[:10],
    }

    (out_dir / "mesh_chamfer_summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / "mesh_chamfer_by_scene.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
