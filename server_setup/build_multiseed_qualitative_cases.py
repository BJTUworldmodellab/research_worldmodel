import html
import json
from pathlib import Path

ROOT = Path('/root/RelationAwareInstructScene')
REPO = ROOT / 'repos' / 'InstructScene'
VIS = ROOT / 'visual'
STAMP = '20260708_134245'
VIS.mkdir(parents=True, exist_ok=True)

paths = []
for room, epoch in [('bedroom','01999'),('livingroom','01459'),('diningroom','01239')]:
    d = REPO / 'out' / f'{room}_sgdiffusion_vq_objfeat' / 'generated_scenes' / f'epoch_{epoch}'
    paths.extend(sorted(d.glob(f'relation_aware_parsed_strict_floorprior_seed*_max1p8_mesh_p2_{STAMP}_eval_cfg1.0_1.0.json')))

def exact_count(target, pred):
    pred = list(map(tuple, pred))
    c = 0
    for rel in map(tuple, target):
        if rel in pred:
            c += 1
            pred.remove(rel)
    return c

def room_seed(path):
    room = 'unknown'
    for part in path.parts:
        if part.endswith('_sgdiffusion_vq_objfeat'):
            room = part.replace('_sgdiffusion_vq_objfeat','')
    name = path.name
    seed = '1' if 'seed1' in name else '2' if 'seed2' in name else '0'
    return room, seed

def scene_score(scene):
    selected = scene.get('selected_relations', [])
    base = exact_count(selected, scene.get('layout_relations', []))
    rep = exact_count(selected, scene.get('repair_relations', []))
    lm = scene.get('layout_mesh_collision') or {}
    rm = scene.get('repair_mesh_collision') or {}
    return {
        'total': len(selected),
        'base': base,
        'repair': rep,
        'gain': rep - base,
        'base_mesh': lm.get('collision_pairs', 0),
        'repair_mesh': rm.get('collision_pairs', 0),
        'mesh_delta': rm.get('collision_pairs', 0) - lm.get('collision_pairs', 0),
        'gated_keep': rm.get('collision_pairs', 0) <= lm.get('collision_pairs', 0),
        'move': (scene.get('repair_stats') or {}).get('total_movement', 0),
    }

def color(name):
    palette = ['#3b75af','#4f9d69','#d99036','#bc5148','#7e65a7','#c76c9c','#668c99','#8c7a45']
    return palette[abs(hash(name)) % len(palette)]

def svg_for(boxes, title):
    if not boxes:
        return '<svg viewBox="0 0 100 100"></svg>'
    xs=[]; zs=[]
    for b in boxes:
        x,y,z = b['translation']
        sx,sy,sz = b['size']
        xs += [x-sx/2, x+sx/2]
        zs += [z-sz/2, z+sz/2]
    xmin,xmax = min(xs)-0.5, max(xs)+0.5
    zmin,zmax = min(zs)-0.5, max(zs)+0.5
    w=max(xmax-xmin,1e-6); h=max(zmax-zmin,1e-6)
    rects=[]
    labels=[]
    for b in boxes:
        x,_,z=b['translation']; sx,_,sz=b['size']; ang=b.get('angle',0)
        px=(x-xmin)/w*420; py=(z-zmin)/h*320
        rw=sx/w*420; rh=sz/h*320
        cls=b.get('class_name','obj')
        rects.append(f'<rect x="{px-rw/2:.1f}" y="{py-rh/2:.1f}" width="{rw:.1f}" height="{rh:.1f}" rx="2" fill="{color(cls)}" fill-opacity="0.55" stroke="#26312d" stroke-width="0.8" transform="rotate({-ang*57.2958:.1f} {px:.1f} {py:.1f})"/>')
        labels.append(f'<text x="{px:.1f}" y="{py:.1f}" text-anchor="middle" dominant-baseline="middle" font-size="8" fill="#17201c">{html.escape(cls[:12])}</text>')
    return f'<svg class="scene" viewBox="0 0 420 320" role="img" aria-label="{html.escape(title)}"><rect x="0" y="0" width="420" height="320" fill="#f8faf7" stroke="#d7ded7"/>{"".join(rects)}{"".join(labels)}</svg>'

cards=[]
for path in paths:
    room, seed = room_seed(path)
    data=json.load(open(path,encoding='utf-8'))
    scenes=[]
    for scene in data['per_scene']:
        sc=scene_score(scene)
        if sc['total'] == 0:
            continue
        scenes.append((sc, scene))
    improved_safe=[x for x in scenes if x[0]['gain']>0 and x[0]['gated_keep']]
    improved_fallback=[x for x in scenes if x[0]['gain']>0 and not x[0]['gated_keep']]
    nochange_safe=[x for x in scenes if x[0]['gain']==0 and x[0]['gated_keep']]
    picks=[]
    picks += [('关系提升且 mesh 不变坏', x) for x in sorted(improved_safe, key=lambda v:(-v[0]['gain'], v[0]['mesh_delta'], -v[0]['move']))[:2]]
    picks += [('关系提升但需要 gated 回退', x) for x in sorted(improved_fallback, key=lambda v:(-v[0]['gain'], -v[0]['mesh_delta']))[:1]]
    picks += [('稳定样例', x) for x in nochange_safe[:1]]
    for label,(sc,scene) in picks:
        cards.append(f'''
        <article class="card">
          <h3>{html.escape(room)} seed {seed}: {html.escape(label)}</h3>
          <p class="text">{html.escape(scene.get('text',''))}</p>
          <p class="meta">relation {sc['base']}/{sc['total']} -> {sc['repair']}/{sc['total']} · gain {sc['gain']} · mesh pairs {sc['base_mesh']} -> {sc['repair_mesh']} · move {sc['move']:.3f}</p>
          <div class="pair"><div><b>before</b>{svg_for(scene.get('layout_boxes',[]),'before')}</div><div><b>after</b>{svg_for(scene.get('repair_boxes',[]),'after')}</div></div>
          <p class="path"><code>{html.escape(str(path))}</code><br><code>{html.escape(scene.get('scene_uid',''))}</code></p>
        </article>''')

html_doc=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Multiseed Floor-Prior Qualitative Cases</title>
<style>
body{{margin:0;background:#f6f7f4;color:#1d2522;font-family:Inter,system-ui,sans-serif;line-height:1.55}}header{{padding:34px 5vw;background:#fff;border-bottom:1px solid #d8ded8}}main{{padding:24px 5vw 60px}}h1{{margin:0 0 8px;font-size:38px;letter-spacing:0}}p{{color:#5d6b66}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(560px,1fr));gap:18px}}.card{{background:#fff;border:1px solid #d8ded8;border-radius:8px;padding:16px}}h3{{margin:0 0 8px}}.text{{color:#30413b}}.meta{{font-size:14px}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.pair b{{display:block;margin-bottom:6px;color:#24765d}}svg.scene{{width:100%;height:auto;border:1px solid #d8ded8;border-radius:6px}}.path{{font-size:12px;word-break:break-all}}code{{background:#eef1ed;padding:2px 4px;border-radius:4px}}</style></head>
<body><header><h1>Multiseed Floor-Prior Qualitative Cases</h1><p>Top-down box visualizations generated from strict mesh multi-seed JSON. These are qualitative case indices, not rendered photorealistic images.</p></header><main><div class="grid">{''.join(cards)}</div></main></body></html>'''
out=VIS / f'multiseed_floorprior_qualitative_cases_{STAMP}.html'
out.write_text(html_doc,encoding='utf-8')
print('QUAL_HTML', out)
print('QUAL_CASES', len(cards))
