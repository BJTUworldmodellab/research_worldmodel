import json
import random
from pathlib import Path


ROOT = Path("docs/commonscenes_experiment_pack_20260713/data/bootstrap")
OUT_JSON = ROOT / "bootstrap_ci_summary.json"
OUT_MD = ROOT / "bootstrap_ci_summary.md"
ROOMS = ["bedroom", "livingroom", "diningroom", "library"]
METRICS = {
    "mean_ssim": ("image", "ssim"),
    "mean_abs_pixel_diff": ("image", "mean_abs_pixel_diff"),
    "mean_changed_pixel_ratio": ("image", "changed_pixel_ratio"),
    "mean_chamfer": ("mesh", "chamfer"),
}


def load_values(room, source, field):
    if source == "image":
        path = ROOT / f"{room}_image_quality_by_scene.json"
    else:
        path = ROOT / f"{room}_mesh_chamfer_by_scene.json"
    rows = json.loads(path.read_text())
    vals = [float(row[field]) for row in rows if field in row and row[field] is not None]
    if not vals:
        raise RuntimeError(f"no values for {room} {source} {field}")
    return vals


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    idx = (len(values) - 1) * p
    lo = int(idx)
    hi = min(lo + 1, len(values) - 1)
    frac = idx - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def bootstrap_mean_ci(values, rounds=5000, seed=20260714):
    rng = random.Random(seed)
    n = len(values)
    means = []
    for _ in range(rounds):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    return {
        "n": n,
        "mean": sum(values) / n,
        "ci95_low": percentile(means, 0.025),
        "ci95_high": percentile(means, 0.975),
    }


def main():
    summary = {}
    for room in ROOMS:
        summary[room] = {}
        for metric, (source, field) in METRICS.items():
            summary[room][metric] = bootstrap_mean_ci(load_values(room, source, field))

    OUT_JSON.write_text(json.dumps(summary, indent=2))

    lines = [
        "# Bootstrap CI Summary",
        "",
        "Bootstrap over scenes, 5000 resamples per room. CIs describe visual/geometric disturbance metrics, not relation-score uncertainty.",
        "",
        "| room | metric | n | mean | 95% CI |",
        "|---|---|---:|---:|---:|",
    ]
    for room in ROOMS:
        for metric in METRICS:
            item = summary[room][metric]
            lines.append(
                f"| {room} | {metric} | {item['n']} | {item['mean']:.6f} | "
                f"[{item['ci95_low']:.6f}, {item['ci95_high']:.6f}] |"
            )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
