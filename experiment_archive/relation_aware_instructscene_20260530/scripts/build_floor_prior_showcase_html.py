import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "visual" / "floor_prior_showcase"
OUT = ROOT / "visual" / "floor_prior_showcase.html"


def local_img(name):
    return f"floor_prior_showcase/{name}"


def main():
    manifest = json.loads((SHOWCASE / "manifest.json").read_text(encoding="utf-8"))
    cards = []
    for item in manifest:
        before = Path(item["before"]).name
        after = Path(item["after"]).name
        combined = Path(item["combined"]).name
        text = item["text"]
        if len(text) > 220:
            text = text[:217] + "..."
        cards.append(f"""
        <article>
          <div class="meta">
            <span>{item['room']}</span>
            <strong>scene #{int(item['idx']):04d}</strong>
            <em>relation {item['beforeScore']}/{item['total']} -> {item['afterScore']}/{item['total']} · mesh pairs {item['beforePairs']} -> {item['afterPairs']}</em>
          </div>
          <img class="hero" src="{local_img(combined)}" alt="{item['room']} floor-prior comparison">
          <p>{text}</p>
          <div class="pair">
            <img src="{local_img(before)}" alt="before">
            <img src="{local_img(after)}" alt="after">
          </div>
        </article>
        """)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Floor-Prior Real Mesh Showcase</title>
  <style>
    body {{ margin:0; font-family:Inter,ui-sans-serif,system-ui; background:#080b0d; color:#eef8f4; }}
    header {{ min-height:72vh; display:flex; align-items:end; padding:42px 5vw; background:linear-gradient(180deg,rgba(8,11,13,.1),#080b0d), url("{local_img(Path(manifest[0]['combined']).name)}") center/cover; }}
    h1 {{ font-size:54px; max-width:940px; margin:0; letter-spacing:0; line-height:1.02; }}
    main {{ padding:34px 5vw 80px; }}
    .intro {{ max-width:980px; color:#b9cbc4; font-size:17px; line-height:1.55; }}
    article {{ padding:30px 0 42px; border-top:1px solid #24302e; }}
    .meta {{ display:flex; gap:14px; align-items:baseline; flex-wrap:wrap; margin-bottom:14px; }}
    .meta span {{ color:#7affd8; text-transform:uppercase; font-size:13px; letter-spacing:.08em; }}
    .meta strong {{ font-size:24px; }}
    .meta em {{ color:#aabbb5; font-style:normal; }}
    .hero {{ width:100%; border-radius:8px; display:block; background:#111; }}
    .pair {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:14px; }}
    .pair img {{ width:100%; border-radius:8px; display:block; background:#111; }}
    p {{ color:#b9cbc4; line-height:1.5; }}
    a {{ color:#7affd8; }}
    @media (max-width:800px) {{ h1 {{ font-size:38px; }} .pair {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Floor-Prior Relation-Aware InstructScene: Real 3D-FUTURE Mesh Comparisons</h1>
  </header>
  <main>
    <p class="intro">Fifteen automatically selected before/after examples where floor-prior repair improves explicit spatial relations without increasing mesh collision pairs. These are real retrieved 3D-FUTURE meshes with material-aware rendering, not just boxes.</p>
    {''.join(cards)}
  </main>
</body>
</html>"""
    OUT.write_text(html, encoding="utf-8")
    print(OUT)
    print(f"cards={len(manifest)}")


if __name__ == "__main__":
    main()
