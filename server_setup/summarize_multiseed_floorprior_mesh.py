import csv
import glob
import json
import sys
from pathlib import Path

ROOT = Path('/root/RelationAwareInstructScene')
REPO = ROOT / 'repos' / 'InstructScene'
OUTDIR = ROOT / 'results' / 'tables'
VISDIR = ROOT / 'visual'
OUTDIR.mkdir(parents=True, exist_ok=True)
VISDIR.mkdir(parents=True, exist_ok=True)
stamp = sys.argv[1] if len(sys.argv) > 1 else ''


def exact_count(target, pred):
    pred = list(map(tuple, pred))
    count = 0
    for rel in map(tuple, target):
        if rel in pred:
            count += 1
            pred.remove(rel)
    return count


def room_from_path(path):
    for part in Path(path).parts:
        if part.endswith('_sgdiffusion_vq_objfeat'):
            return part.replace('_sgdiffusion_vq_objfeat', '')
    return 'unknown'


def seed_from_path(path):
    name = Path(path).name
    for seed in ('seed1', 'seed2'):
        if seed in name:
            return seed.replace('seed', '')
    return '0'

paths = []
for room, epoch in [('bedroom', '01999'), ('livingroom', '01459'), ('diningroom', '01239')]:
    base = REPO / 'out' / f'{room}_sgdiffusion_vq_objfeat' / 'generated_scenes' / f'epoch_{epoch}'
    paths.extend(glob.glob(str(base / f'relation_aware_parsed_strict_floorprior_seed*_max1p8_mesh_p2_{stamp}_eval_cfg1.0_1.0.json')))

rows = []
gated_rows = []
for path in sorted(paths):
    d = json.load(open(path, encoding='utf-8'))
    s = d['scores']
    room = room_from_path(path)
    seed = seed_from_path(path)
    row = {
        'room': room,
        'seed': seed,
        'scenes': len(d.get('per_scene', [])),
        'baseline_relation_acc': s['baseline_relation_acc'],
        'repair_relation_acc': s['repaired_relation_acc'],
        'repair_gain': s['repaired_relation_acc'] - s['baseline_relation_acc'],
        'avg_repair_movement': s['avg_repair_movement'],
        'baseline_mesh_pair_rate': s['layout_mesh_collision_pair_rate'],
        'repair_mesh_pair_rate': s['repair_mesh_collision_pair_rate'],
        'mesh_pair_delta': s['repair_mesh_collision_pair_rate'] - s['layout_mesh_collision_pair_rate'],
        'source': path,
    }
    rows.append(row)

    rel_total = base_correct = repair_correct = gated_correct = 0
    base_pairs = repair_pairs = gated_pairs = 0
    base_total = repair_total = gated_total = 0
    fallback = evaluated = 0
    for scene in d['per_scene']:
        selected = scene['selected_relations']
        rel_total += len(selected)
        base_rel = scene['layout_relations']
        repair_rel = scene['repair_relations']
        base_correct += exact_count(selected, base_rel)
        repair_correct += exact_count(selected, repair_rel)
        lm = scene.get('layout_mesh_collision') or {}
        rm = scene.get('repair_mesh_collision') or {}
        if lm.get('available') and rm.get('available'):
            evaluated += 1
            if rm.get('collision_pairs', 0) <= lm.get('collision_pairs', 0):
                gated_rel = repair_rel
                gm = rm
            else:
                gated_rel = base_rel
                gm = lm
                fallback += 1
        else:
            gated_rel = repair_rel
            gm = rm
        gated_correct += exact_count(selected, gated_rel)
        base_pairs += lm.get('collision_pairs', 0)
        repair_pairs += rm.get('collision_pairs', 0)
        gated_pairs += gm.get('collision_pairs', 0)
        base_total += lm.get('total_pairs', 0)
        repair_total += rm.get('total_pairs', 0)
        gated_total += gm.get('total_pairs', 0)
    gated_rows.append({
        'room': room,
        'seed': seed,
        'baseline_relation_acc': base_correct / max(rel_total, 1),
        'repair_relation_acc': repair_correct / max(rel_total, 1),
        'gated_relation_acc': gated_correct / max(rel_total, 1),
        'repair_gain': repair_correct / max(rel_total, 1) - base_correct / max(rel_total, 1),
        'gated_gain': gated_correct / max(rel_total, 1) - base_correct / max(rel_total, 1),
        'baseline_mesh_pair_rate': base_pairs / max(base_total, 1),
        'repair_mesh_pair_rate': repair_pairs / max(repair_total, 1),
        'gated_mesh_pair_rate': gated_pairs / max(gated_total, 1),
        'fallback_scenes': fallback,
        'mesh_scenes_evaluated': evaluated,
        'source': path,
    })

summary_path = OUTDIR / f'multiseed_floorprior_mesh_{stamp}.csv'
gated_path = OUTDIR / f'multiseed_floorprior_gated_{stamp}.csv'
for out, data in [(summary_path, rows), (gated_path, gated_rows)]:
    if data:
        with out.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)

# Compact qualitative inventory. Link paths are remote filesystem paths for traceability.
render_files = []
for path in paths:
    root = Path(path).parent
    render_files.extend(sorted(str(p) for p in root.glob('*strict_floorprior_seed*_max1p8_mesh_p2*/*.png')))
    render_files.extend(sorted(str(p) for p in root.glob('*strict_floorprior_seed*_max1p8_mesh_p2*.png')))
render_files = render_files[:80]
html_rows = '\n'.join(f'<tr><td>{idx+1}</td><td><code>{p}</code></td></tr>' for idx, p in enumerate(render_files))
metric_rows = '\n'.join(
    '<tr>' + ''.join(f'<td>{r.get(k, "")}</td>' for k in ['room','seed','baseline_relation_acc','repair_relation_acc','repair_gain','avg_repair_movement','mesh_pair_delta']) + '</tr>'
    for r in rows
)
html = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Multiseed Floor-Prior Mesh Qualitative Inventory</title>
<style>body{{font-family:Inter,system-ui,sans-serif;margin:32px;background:#f6f7f4;color:#1d2522}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{border:1px solid #d8ded8;padding:8px;text-align:left;font-size:13px}}th{{background:#eef1ed}}code{{font-family:Consolas,monospace}}</style></head>
<body><h1>Multiseed Floor-Prior Mesh Results</h1><p>Stamp: {stamp}. This page records metric rows and render/image file inventory generated on the remote server.</p>
<h2>Metrics</h2><table><thead><tr><th>room</th><th>seed</th><th>baseline</th><th>repair</th><th>gain</th><th>avg move</th><th>mesh delta</th></tr></thead><tbody>{metric_rows}</tbody></table>
<h2>Render/Image Inventory</h2><table><thead><tr><th>#</th><th>remote path</th></tr></thead><tbody>{html_rows}</tbody></table>
</body></html>'''
html_path = VISDIR / f'multiseed_floorprior_mesh_inventory_{stamp}.html'
html_path.write_text(html, encoding='utf-8')
print('SUMMARY_CSV', summary_path)
print('GATED_CSV', gated_path)
print('HTML', html_path)
print('ROWS', len(rows), 'GATED_ROWS', len(gated_rows), 'RENDER_FILES', len(render_files))
for r in rows:
    print('CSVROW', r['room'], 'seed', r['seed'], 'gain', r['repair_gain'], 'move', r['avg_repair_movement'], 'mesh_delta', r['mesh_pair_delta'])
for r in gated_rows:
    print('GATEDROW', r['room'], 'seed', r['seed'], 'gated_gain', r['gated_gain'], 'base_mesh', r['baseline_mesh_pair_rate'], 'gated_mesh', r['gated_mesh_pair_rate'], 'fallback', r['fallback_scenes'])
