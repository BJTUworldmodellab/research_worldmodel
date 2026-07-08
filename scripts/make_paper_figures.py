import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.transforms import Affine2D


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "visual" / "paper_figures"

EXAMPLES = {
    "bedroom": [78, 22],
    "livingroom": [148, 29],
    "diningroom": [82, 39],
}

PALETTE = [
    "#4e79a7",
    "#59a14f",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#8cd17d",
    "#499894",
    "#d37295",
]


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    total = 0
    for rel in map(tuple, target):
        if rel in pred:
            total += 1
            pred.remove(rel)
    return total


def short_name(name):
    name = name.replace("_", " ")
    replacements = {
        "multi seat sofa": "sofa",
        "corner side table": "side table",
        "double bed": "bed",
        "dining table": "table",
        "dining chair": "chair",
        "coffee table": "coffee tbl",
        "pendant lamp": "lamp",
        "nightstand": "nightstand",
        "bookshelf": "shelf",
        "wardrobe": "wardrobe",
        "tv stand": "tv stand",
    }
    for k, v in replacements.items():
        if k in name:
            return v
    words = name.split()
    return " ".join(words[:2]) if len(words) > 2 else name


def class_color(class_name, color_map):
    if class_name not in color_map:
        color_map[class_name] = PALETTE[len(color_map) % len(PALETTE)]
    return color_map[class_name]


def rect_bounds(box):
    x, _, z = box["translation"]
    sx, _, sz = box["size"]
    return x, z, max(sx * 2.0, 0.05), max(sz * 2.0, 0.05), box["angle"]


def draw_box(ax, box, color_map, highlight=False):
    x, z, w, h, angle = rect_bounds(box)
    color = class_color(box["class_name"], color_map)
    rect = Rectangle(
        (x - w / 2, z - h / 2),
        w,
        h,
        linewidth=2.1 if highlight else 1.25,
        edgecolor="#202421" if not highlight else "#0f7c63",
        facecolor=color,
        alpha=0.46 if not highlight else 0.62,
    )
    transform = Affine2D().rotate_around(x, z, angle) + ax.transData
    rect.set_transform(transform)
    ax.add_patch(rect)
    ax.text(
        x,
        z,
        short_name(box["class_name"]),
        ha="center",
        va="center",
        fontsize=7.5,
        color="#111614",
        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", alpha=0.72, edgecolor="none"),
    )


def find_box_pair(boxes, rel):
    subj, _pred, obj = rel
    subj_boxes = [b for b in boxes if int(b["class_id"]) == int(subj)]
    obj_boxes = [b for b in boxes if int(b["class_id"]) == int(obj)]
    if not subj_boxes or not obj_boxes:
        return None
    best = None
    best_dist = 1e9
    for a in subj_boxes:
        ax, _, az = a["translation"]
        for b in obj_boxes:
            bx, _, bz = b["translation"]
            d = (ax - bx) ** 2 + (az - bz) ** 2
            if d < best_dist:
                best_dist = d
                best = (a, b)
    return best


def relation_arrows(scene):
    selected = [tuple(x) for x in scene["selected_relations"]]
    before = set(map(tuple, scene["layout_relations"]))
    after = set(map(tuple, scene["repair_relations"]))
    improved = [rel for rel in selected if rel not in before and rel in after]
    return improved[:2] or selected[:1]


def draw_scene(ax, boxes, scene, title, score, collision_pairs, color_map, arrows, after=False):
    ax.set_title(f"{title}  relation {score}  mesh pairs {collision_pairs}", fontsize=11, pad=8)
    arrow_classes = set()
    for rel in arrows:
        pair = find_box_pair(boxes, rel)
        if pair:
            arrow_classes.add(pair[0]["index"])
            arrow_classes.add(pair[1]["index"])
    for box in boxes:
        draw_box(ax, box, color_map, highlight=box["index"] in arrow_classes)
    for rel in arrows:
        pair = find_box_pair(boxes, rel)
        if not pair:
            continue
        a, b = pair
        ax_, _, az = a["translation"]
        bx, _, bz = b["translation"]
        arrow = FancyArrowPatch(
            (bx, bz),
            (ax_, az),
            arrowstyle="-|>",
            mutation_scale=15,
            linewidth=2.2,
            color="#0f7c63" if after else "#9b4d2e",
            alpha=0.95,
            linestyle="solid" if after else "dashed",
            connectionstyle="arc3,rad=0.08",
        )
        ax.add_patch(arrow)
    ax.grid(True, color="#d8ddd6", linewidth=0.45, alpha=0.75)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x", fontsize=9)
    ax.set_ylabel("z", fontsize=9)


def scene_limits(scene):
    xs, zs = [], []
    for key in ["layout_boxes", "repair_boxes"]:
        for box in scene[key]:
            x, z, w, h, _ = rect_bounds(box)
            xs.extend([x - w / 2, x + w / 2])
            zs.extend([z - h / 2, z + h / 2])
    margin = 0.45
    return min(xs) - margin, max(xs) + margin, min(zs) - margin, max(zs) + margin


def render_example(room, idx, scene):
    color_map = {}
    arrows = relation_arrows(scene)
    selected = scene["selected_relations"]
    base_score = exact_count(selected, scene["layout_relations"])
    repair_score = exact_count(selected, scene["repair_relations"])
    base_pairs = scene["layout_mesh_collision"]["collision_pairs"]
    repair_pairs = scene["repair_mesh_collision"]["collision_pairs"]
    x0, x1, z0, z1 = scene_limits(scene)

    fig, axes = plt.subplots(1, 2, figsize=(14.5, 7.2), dpi=180)
    fig.patch.set_facecolor("#f7f7f4")
    prompt = textwrap.fill(scene["text"], width=118)
    fig.suptitle(f"{room} example {idx}: {prompt}", fontsize=13, y=0.98)
    draw_scene(
        axes[0],
        scene["layout_boxes"],
        scene,
        "Before",
        f"{base_score}/{len(selected)}",
        base_pairs,
        color_map,
        arrows,
        after=False,
    )
    draw_scene(
        axes[1],
        scene["repair_boxes"],
        scene,
        "After",
        f"{repair_score}/{len(selected)}",
        repair_pairs,
        color_map,
        arrows,
        after=True,
    )
    for ax in axes:
        ax.set_xlim(x0, x1)
        ax.set_ylim(z0, z1)
        ax.set_facecolor("#ffffff")
    fig.text(
        0.5,
        0.02,
        "Dashed/green arrows mark selected relation targets; boxes are generated oriented footprints from retrieved 3D-FUTURE objects.",
        ha="center",
        fontsize=9,
        color="#647067",
    )
    fig.tight_layout(rect=[0, 0.045, 1, 0.935])
    stem = f"{room}_{idx:04d}_{scene['scene_uid']}".replace("/", "_")
    png = OUT / f"{stem}.png"
    svg = OUT / f"{stem}.svg"
    fig.savefig(png, facecolor=fig.get_facecolor())
    fig.savefig(svg, facecolor=fig.get_facecolor())
    plt.close(fig)
    return png, svg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gallery = []
    for room, indices in EXAMPLES.items():
        data_path = ROOT / "results" / "full" / room / "relation_aware_parsed_mesh_p2_close0.75_far1.6_eval.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        for idx in indices:
            scene = data["per_scene"][idx]
            png, svg = render_example(room, idx, scene)
            gallery.append((room, idx, scene["text"], png, svg))

    cards = []
    for room, idx, text, png, svg in gallery:
        rel = png.resolve().as_posix()
        cards.append(
            f'<article class="card"><h2>{room} #{idx}</h2><p>{text}</p>'
            f'<img src="{rel}" alt="{room} example {idx}"></article>'
        )
    html = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paper-Style Relation-Aware Figures</title>
  <style>
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui; background: #f7f7f4; color: #202421; }
    header { padding: 38px 5vw 24px; background: #e9ede8; border-bottom: 1px solid #d8ddd6; }
    main { padding: 24px 5vw 48px; display: grid; gap: 18px; }
    h1 { margin: 0; font-size: 42px; }
    p { color: #647067; line-height: 1.45; }
    .card { background: white; border: 1px solid #d8ddd6; border-radius: 8px; padding: 16px; }
    .card h2 { margin: 0 0 8px; font-size: 18px; }
    .card img { width: 100%; height: auto; border: 1px solid #d8ddd6; border-radius: 6px; background: #fff; }
  </style>
</head>
<body>
  <header>
    <h1>Paper-Style Before/After Figures</h1>
    <p>Clean oriented-footprint visualizations from generated layouts. These are designed for paper figures; mesh projection diagnostics remain in mesh_renders_gallery.html.</p>
  </header>
  <main>
""" + "\n".join(cards) + """
  </main>
</body>
</html>
"""
    (ROOT / "visual" / "paper_figures_gallery.html").write_text(html, encoding="utf-8")
    print(f"wrote {len(gallery)} examples to {OUT}")
    print(ROOT / "visual" / "paper_figures_gallery.html")


if __name__ == "__main__":
    main()
