import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "results" / "floor_prior_remote"
TABLE_DIR = ROOT / "results" / "tables"
VISUAL_DIR = ROOT / "visual"


def parse_meta(path):
    name = path.name
    if name.startswith("bedroom_"):
        room = "bedroom"
    elif name.startswith("livingroom_"):
        room = "livingroom"
    elif name.startswith("diningroom_"):
        room = "diningroom"
    else:
        room = "unknown"
    variant = name.split("_relation_aware_parsed_", 1)[1].rsplit("_eval_cfg", 1)[0]
    return room, variant


def load_rows():
    rows = []
    paths = sorted(IN_DIR.glob("*_relation_aware_parsed_*mesh*_eval_cfg1.0_1.0.json"))
    for path in paths:
        room, variant = parse_meta(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        scores = data["scores"]
        rows.append({
            "room": room,
            "variant": variant,
            "path": str(path),
            "baseline_relation_acc": scores["baseline_relation_acc"],
            "repair_relation_acc": scores["repaired_relation_acc"],
            "relation_gain": scores["repaired_relation_acc"] - scores["baseline_relation_acc"],
            "avg_repair_movement": scores["avg_repair_movement"],
            "repair_overlap_ratio": scores["repair_overlap_ratio"],
            "repair_out_of_bounds_rate": scores["repair_out_of_bounds_rate"],
            "mesh_scenes": scores["mesh_collision_scenes_evaluated"],
            "baseline_mesh_pair_rate": scores["layout_mesh_collision_pair_rate"],
            "repair_mesh_pair_rate": scores["repair_mesh_collision_pair_rate"],
            "mesh_pair_delta": scores["repair_mesh_collision_pair_rate"] - scores["layout_mesh_collision_pair_rate"],
            "baseline_mesh_scene_rate": scores["layout_mesh_collision_scene_rate"],
            "repair_mesh_scene_rate": scores["repair_mesh_collision_scene_rate"],
        })
    rows.sort(key=lambda r: (r["room"], r["variant"]))
    return rows


def write_csv(rows):
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    out = TABLE_DIR / "floor_prior_results.csv"
    if not rows:
        return out
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return out


def fmt(x):
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def write_html(rows):
    VISUAL_DIR.mkdir(parents=True, exist_ok=True)
    table_rows = "\n".join(
        "<tr>"
        + "".join(
            f"<td>{fmt(row[key])}</td>"
            for key in [
                "room",
                "variant",
                "baseline_relation_acc",
                "repair_relation_acc",
                "relation_gain",
                "avg_repair_movement",
                "baseline_mesh_pair_rate",
                "repair_mesh_pair_rate",
                "mesh_pair_delta",
                "repair_overlap_ratio",
            ]
        )
        + "</tr>"
        for row in rows
    )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Floor-Prior Relation-Aware InstructScene Results</title>
  <style>
    body {{ margin:0; font-family:Inter,ui-sans-serif,system-ui; background:#f6f7f4; color:#202421; }}
    header {{ padding:36px 5vw; background:#e9eee9; border-bottom:1px solid #d5ddd4; }}
    main {{ padding:28px 5vw 60px; }}
    h1 {{ margin:0; font-size:42px; letter-spacing:0; }}
    p {{ color:#596861; line-height:1.45; max-width:980px; }}
    table {{ width:100%; border-collapse:collapse; background:white; border:1px solid #d8ddd6; }}
    th,td {{ padding:11px 10px; border-bottom:1px solid #e3e8e1; text-align:left; font-size:14px; }}
    th {{ background:#f0f4ef; }}
    .note {{ margin-top:18px; padding:16px; border-left:4px solid #2c7a62; background:#fff; }}
  </style>
</head>
<body>
  <header>
    <h1>Floor-Prior Relation-Aware InstructScene</h1>
    <p>Parallel experiment summary for the height-fixed and scene-prior-constrained repair variants. The paper-facing claim should prefer floor_prior when it preserves relation gains with better mesh and movement behavior.</p>
  </header>
  <main>
    <table>
      <thead>
        <tr>
          <th>Room</th><th>Variant</th><th>Base Rel</th><th>Repair Rel</th><th>Gain</th><th>Move</th><th>Base Mesh</th><th>Repair Mesh</th><th>Mesh Delta</th><th>Overlap</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>
    <div class="note">Use this page together with <a href="real_mesh_showcase.html">real_mesh_showcase.html</a>. Relation improvement alone is not enough; prefer results where mesh collision does not increase and movement stays bounded.</div>
  </main>
</body>
</html>"""
    out = VISUAL_DIR / "a_conf_floor_prior_results.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    rows = load_rows()
    csv_path = write_csv(rows)
    html_path = write_html(rows)
    print(csv_path)
    print(html_path)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
