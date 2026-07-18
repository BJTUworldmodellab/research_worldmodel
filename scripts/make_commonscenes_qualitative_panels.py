import json
import os
from pathlib import Path

import cv2
import numpy as np


ROOT = Path("/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair")
ROOMS = {
    "bedroom": {
        "quality": ROOT / "commonscenes_ours_generic_gate_t1.5_compare_epoch195_bedroom" / "image_quality_by_scene.json",
        "base_png": Path("/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom/png"),
        "ours_png": ROOT / "commonscenes_render_ours_generic_gate_t1.5_epoch195_bedroom/png",
    },
    "livingroom": {
        "quality": ROOT / "commonscenes_ours_generic_gate_t1.5_quality_epoch195_livingroom" / "image_quality_by_scene.json",
        "base_png": ROOT / "commonscenes_render_baseline_epoch195_livingroom/png",
        "ours_png": ROOT / "commonscenes_render_ours_generic_gate_t1.5_epoch195_livingroom/png",
    },
    "diningroom": {
        "quality": ROOT / "commonscenes_ours_generic_gate_t1.5_quality_epoch195_diningroom" / "image_quality_by_scene.json",
        "base_png": ROOT / "commonscenes_render_baseline_epoch195_diningroom/png",
        "ours_png": ROOT / "commonscenes_render_ours_generic_gate_t1.5_epoch195_diningroom/png",
    },
    "library": {
        "quality": ROOT / "commonscenes_ours_generic_gate_t1.5_quality_epoch195_library" / "image_quality_by_scene.json",
        "base_png": ROOT / "commonscenes_render_baseline_epoch195_library/png",
        "ours_png": ROOT / "commonscenes_render_ours_generic_gate_t1.5_epoch195_library/png",
    },
}
OUT = ROOT / "paper_qualitative_panels"


def read_image(path):
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return img


def label(img, text):
    bar_h = 34
    out = np.full((img.shape[0] + bar_h, img.shape[1], 3), 255, dtype=np.uint8)
    out[bar_h:, :, :] = img
    cv2.putText(out, text, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (20, 20, 20), 2, cv2.LINE_AA)
    return out


def make_pair(base_path, ours_path, title, metrics):
    base = read_image(base_path)
    ours = read_image(ours_path)
    h = min(base.shape[0], ours.shape[0])
    w = min(base.shape[1], ours.shape[1])
    base = cv2.resize(base, (w, h), interpolation=cv2.INTER_AREA)
    ours = cv2.resize(ours, (w, h), interpolation=cv2.INTER_AREA)
    left = label(base, "baseline")
    right = label(ours, "ours")
    gap = np.full((left.shape[0], 10, 3), 245, dtype=np.uint8)
    pair = np.concatenate([left, gap, right], axis=1)
    header = np.full((58, pair.shape[1], 3), 255, dtype=np.uint8)
    cv2.putText(header, title, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.64, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(header, metrics, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (60, 60, 60), 1, cv2.LINE_AA)
    return np.concatenate([header, pair], axis=0)


def pick_cases(rows):
    valid = [r for r in rows if r.get("mean_abs_pixel_diff", 0) > 1e-5 and r.get("ssim") is not None]
    low_change = sorted(valid, key=lambda r: (r["mean_abs_pixel_diff"], -r.get("ssim", 0)))[0]
    high_change = sorted(valid, key=lambda r: r["mean_abs_pixel_diff"], reverse=True)[0]
    return low_change, high_change


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    low_panels = []
    high_panels = []
    for room, cfg in ROOMS.items():
        rows = json.loads(cfg["quality"].read_text())
        low, high = pick_cases(rows)
        for kind, row, sink in [("low_change", low, low_panels), ("high_change", high, high_panels)]:
            scan = row["scan"]
            base_path = cfg["base_png"] / f"{scan}.png"
            ours_path = cfg["ours_png"] / f"{scan}.png"
            metrics = (
                f"SSIM={row.get('ssim', 0):.4f}  "
                f"mean_abs_diff={row.get('mean_abs_pixel_diff', 0):.3f}  "
                f"changed_px={row.get('changed_pixel_ratio', 0):.4f}"
            )
            panel = make_pair(base_path, ours_path, f"{room}: {scan} ({kind})", metrics)
            out_path = OUT / f"{room}_{kind}_{scan}.png"
            cv2.imwrite(str(out_path), panel)
            sink.append(panel)
            manifest.append(
                {
                    "room": room,
                    "kind": kind,
                    "scan": scan,
                    "ssim": row.get("ssim"),
                    "mean_abs_pixel_diff": row.get("mean_abs_pixel_diff"),
                    "changed_pixel_ratio": row.get("changed_pixel_ratio"),
                    "panel": str(out_path),
                }
            )

    def stack_grid(panels):
        widths = [p.shape[1] for p in panels]
        max_w = max(widths)
        padded = []
        for p in panels:
            if p.shape[1] < max_w:
                pad = np.full((p.shape[0], max_w - p.shape[1], 3), 255, dtype=np.uint8)
                p = np.concatenate([p, pad], axis=1)
            padded.append(p)
        gap = np.full((12, max_w, 3), 245, dtype=np.uint8)
        pieces = []
        for idx, p in enumerate(padded):
            if idx:
                pieces.append(gap)
            pieces.append(p)
        return np.concatenate(pieces, axis=0)

    cv2.imwrite(str(OUT / "low_change_examples_grid.png"), stack_grid(low_panels))
    cv2.imwrite(str(OUT / "high_change_risk_examples_grid.png"), stack_grid(high_panels))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"out": str(OUT), "cases": manifest}, indent=2))


if __name__ == "__main__":
    main()
