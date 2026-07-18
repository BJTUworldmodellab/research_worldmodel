import os, glob, json, numpy as np, trimesh
from scipy.spatial import cKDTree
from pathlib import Path

base_dir=Path('/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom/glb')
gen_dir=Path('/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_render_ours_generic_gate_t1.5_epoch195_bedroom/glb')
out=Path('/root/autodl-tmp/RelationAwareInstructScene/results_generic_repair/commonscenes_ours_generic_gate_t1.5_mesh_metrics_epoch195_bedroom')
out.mkdir(parents=True, exist_ok=True)

def load_scene_mesh(path):
    obj=trimesh.load(path, force='scene')
    if isinstance(obj, trimesh.Scene):
        geoms=[]
        for g in obj.geometry.values():
            if isinstance(g, trimesh.Trimesh) and len(g.vertices)>0 and len(g.faces)>0:
                geoms.append(g)
        if not geoms:
            return None
        return trimesh.util.concatenate(geoms)
    return obj if isinstance(obj, trimesh.Trimesh) else None

def sample(mesh, n=2500):
    try:
        pts,_=trimesh.sample.sample_surface(mesh, n)
    except Exception:
        pts=mesh.vertices
        if len(pts)>n:
            rng=np.random.default_rng(0); pts=pts[rng.choice(len(pts),n,replace=False)]
    return np.asarray(pts, dtype=np.float32)

def chamfer(a,b):
    ta=cKDTree(a); tb=cKDTree(b)
    da,_=tb.query(a,k=1); db,_=ta.query(b,k=1)
    return float(da.mean()+db.mean()), float(da.mean()), float(db.mean())
rows=[]
for bp in sorted(base_dir.glob('*.glb')):
    gp=gen_dir/bp.name
    if not gp.exists(): continue
    bm=load_scene_mesh(bp); gm=load_scene_mesh(gp)
    if bm is None or gm is None:
        rows.append({'scan':bp.stem,'error':'load_failed'}); continue
    bpts=sample(bm); gpts=sample(gm)
    cd,b2g,g2b=chamfer(bpts,gpts)
    rows.append({'scan':bp.stem,'chamfer':cd,'baseline_to_generic':b2g,'generic_to_baseline':g2b,'baseline_vertices':int(len(bm.vertices)),'generic_vertices':int(len(gm.vertices))})
valid=[r for r in rows if 'chamfer' in r]
summary={'scenes':len(rows),'valid':len(valid),'mean_chamfer':float(np.mean([r['chamfer'] for r in valid])) if valid else None,'median_chamfer':float(np.median([r['chamfer'] for r in valid])) if valid else None,'max_chamfer':float(np.max([r['chamfer'] for r in valid])) if valid else None,'mean_baseline_to_generic':float(np.mean([r['baseline_to_generic'] for r in valid])) if valid else None,'mean_generic_to_baseline':float(np.mean([r['generic_to_baseline'] for r in valid])) if valid else None,'top_chamfer':sorted(valid,key=lambda r:r['chamfer'],reverse=True)[:10]}
json.dump(summary, open(out/'mesh_chamfer_summary.json','w'), indent=2)
json.dump(rows, open(out/'mesh_chamfer_by_scene.json','w'), indent=2)
print(json.dumps(summary, indent=2))
