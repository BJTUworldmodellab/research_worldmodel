import csv
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim


ROOT = Path(__file__).resolve().parents[1]
VISUAL = ROOT / "visual"
TABLES = ROOT / "results" / "tables"


def image_stats(path):
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img).astype(np.float32)
    gray = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_RGB2GRAY)
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    prob = hist / max(hist.sum(), 1.0)
    entropy = -float(np.sum(prob[prob > 0] * np.log2(prob[prob > 0])))
    hsv = cv2.cvtColor(arr.astype(np.uint8), cv2.COLOR_RGB2HSV)
    return {
        "brightness": float(gray.mean()),
        "contrast": float(gray.std()),
        "sharpness_lap_var": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "entropy": entropy,
        "saturation": float(hsv[:, :, 1].mean()),
    }


def image_ssim(path_a, path_b):
    a = cv2.imread(str(path_a), cv2.IMREAD_GRAYSCALE)
    b = cv2.imread(str(path_b), cv2.IMREAD_GRAYSCALE)
    if a is None or b is None:
        return None
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    return float(ssim(a, b, data_range=255))


def load_clip(device):
    try:
        import torch
        import clip

        model, preprocess = clip.load("ViT-B/32", device=device)
        model.eval()
        return torch, clip, model, preprocess
    except Exception as exc:
        print(f"CLIP unavailable: {exc}")
        return None


def clip_scores(rows):
    try:
        import torch
    except Exception:
        torch = None
    device = "cuda" if torch is not None and torch.cuda.is_available() else "cpu"
    clip_pack = load_clip(device)
    if clip_pack is None:
        for row in rows:
            row["clip_text_before"] = ""
            row["clip_text_after"] = ""
            row["clip_delta"] = ""
        return rows

    torch, clip, model, preprocess = clip_pack
    with torch.no_grad():
        for row in rows:
            text = clip.tokenize([row["text"]], truncate=True).to(device)
            text_feat = model.encode_text(text)
            text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
            scores = []
            for key in ["before_path", "after_path"]:
                image = preprocess(Image.open(row[key]).convert("RGB")).unsqueeze(0).to(device)
                image_feat = model.encode_image(image)
                image_feat = image_feat / image_feat.norm(dim=-1, keepdim=True)
                scores.append(float((image_feat @ text_feat.T).item()))
            row["clip_text_before"] = scores[0]
            row["clip_text_after"] = scores[1]
            row["clip_delta"] = scores[1] - scores[0]
    return rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def rows_from_manifest(showcase_name):
    manifest_path = VISUAL / showcase_name / "manifest.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    for item in manifest:
        before = VISUAL / showcase_name / Path(item["before"]).name
        after = VISUAL / showcase_name / Path(item["after"]).name
        before_stats = image_stats(before)
        after_stats = image_stats(after)
        row = {
            "showcase": showcase_name,
            "variant": item.get("variant", "direct_yfix_mesh"),
            "room": item["room"],
            "idx": item["idx"],
            "text": item["text"],
            "before_path": str(before),
            "after_path": str(after),
            "before_relation_score": item["beforeScore"],
            "after_relation_score": item["afterScore"],
            "relation_total": item["total"],
            "before_mesh_pairs": item["beforePairs"],
            "after_mesh_pairs": item["afterPairs"],
            "ssim_before_after": image_ssim(before, after),
        }
        for key, value in before_stats.items():
            row[f"before_{key}"] = value
        for key, value in after_stats.items():
            row[f"after_{key}"] = value
            row[f"delta_{key}"] = value - before_stats[key]
        rows.append(row)
    return rows


def paired_real_mesh_rows():
    rows = []
    for showcase_name in ["real_mesh_showcase_v3", "floor_prior_showcase"]:
        rows.extend(rows_from_manifest(showcase_name))
    return clip_scores(rows)


def mesh_projection_rows():
    rows = []
    for room_dir in sorted((VISUAL / "mesh_renders").glob("*")):
        if not room_dir.is_dir():
            continue
        before_paths = sorted(room_dir.glob("*_before.png"))
        for before in before_paths:
            after = before.with_name(before.name.replace("_before.png", "_after.png"))
            if not after.exists():
                continue
            before_stats = image_stats(before)
            after_stats = image_stats(after)
            row = {
                "room": room_dir.name,
                "scene": before.name[:-11],
                "before_path": str(before),
                "after_path": str(after),
                "ssim_before_after": image_ssim(before, after),
            }
            for key, value in before_stats.items():
                row[f"before_{key}"] = value
            for key, value in after_stats.items():
                row[f"after_{key}"] = value
                row[f"delta_{key}"] = value - before_stats[key]
            rows.append(row)
    return rows


def mean(values):
    values = [float(v) for v in values if v != "" and v is not None and not math.isnan(float(v))]
    return sum(values) / len(values) if values else 0.0


def visual_src(path):
    path = Path(path)
    try:
        return path.resolve().relative_to(VISUAL.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_html(real_rows, mesh_rows):
    real_clip_delta = mean([r.get("clip_delta", "") for r in real_rows])
    real_rel_gain = mean([float(r["after_relation_score"]) - float(r["before_relation_score"]) for r in real_rows])
    mesh_ssim = mean([r["ssim_before_after"] for r in mesh_rows])
    real_cards = "\n".join(
        f"""
        <article>
          <h3>{row['room']} #{row['idx']}</h3>
          <div class="pair"><img src="{visual_src(row['before_path'])}"><img src="{visual_src(row['after_path'])}"></div>
          <p>Relation {row['before_relation_score']}/{row['relation_total']} -> {row['after_relation_score']}/{row['relation_total']}; mesh pairs {row['before_mesh_pairs']} -> {row['after_mesh_pairs']}; CLIP delta {float(row.get('clip_delta') or 0):+.4f}; SSIM {float(row['ssim_before_after']):.4f}</p>
        </article>
        """
        for row in real_rows
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Relation-Aware Visual Quality Diagnostics</title>
  <style>
    body {{ margin:0; font-family:Inter,Arial,sans-serif; background:#101315; color:#edf5ef; }}
    header, main {{ padding:28px 5vw; }}
    header {{ background:#182120; border-bottom:1px solid #2b3835; }}
    h1 {{ margin:0 0 10px; font-size:38px; letter-spacing:0; }}
    p {{ color:#b9cac4; line-height:1.5; }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:22px 0; }}
    .stat {{ background:#17201f; border:1px solid #2c3a37; padding:16px; border-radius:8px; }}
    .stat strong {{ display:block; font-size:28px; color:#70ffd4; }}
    article {{ border-top:1px solid #2c3a37; padding:22px 0; }}
    .pair {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
    img {{ width:100%; display:block; border-radius:6px; background:#080a0c; }}
    a {{ color:#70ffd4; }}
  </style>
</head>
<body>
  <header>
    <h1>Visual Quality Diagnostics</h1>
    <p>Real 3D-FUTURE before/after renders plus automatic diagnostics. Treat these as visual-consistency evidence, not as a human-preference proof.</p>
  </header>
  <main>
    <section class="stats">
      <div class="stat"><span>Real mesh examples</span><strong>{len(real_rows)}</strong></div>
      <div class="stat"><span>Mean relation gain</span><strong>{real_rel_gain:+.3f}</strong></div>
      <div class="stat"><span>Mean CLIP delta</span><strong>{real_clip_delta:+.4f}</strong></div>
      <div class="stat"><span>Mesh projection mean SSIM</span><strong>{mesh_ssim:.3f}</strong></div>
    </section>
    {real_cards}
    <p>Tables: <a href="../results/tables/visual_quality_real_mesh.csv">visual_quality_real_mesh.csv</a> and <a href="../results/tables/visual_quality_mesh_projection.csv">visual_quality_mesh_projection.csv</a>.</p>
  </main>
</body>
</html>"""
    out = VISUAL / "a_conf_visual_quality.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    real_rows = paired_real_mesh_rows()
    mesh_rows = mesh_projection_rows()
    write_csv(TABLES / "visual_quality_real_mesh.csv", real_rows)
    write_csv(TABLES / "visual_quality_mesh_projection.csv", mesh_rows)
    html = write_html(real_rows, mesh_rows)
    print(TABLES / "visual_quality_real_mesh.csv")
    print(TABLES / "visual_quality_mesh_projection.csv")
    print(html)
    print(f"real_rows={len(real_rows)} mesh_projection_rows={len(mesh_rows)}")


if __name__ == "__main__":
    main()
