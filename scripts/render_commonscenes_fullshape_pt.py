import os, glob, torch, numpy as np, seaborn as sns, trimesh, cv2, traceback
os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')
from helpers.util import get_generated_models_v2
from helpers.visualize_scene import render_img
classes=[line.strip() for line in open('/root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT/classes_all.txt') if line.strip()]
pt_files=sorted(glob.glob('/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195/*.pt'))
out='/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom'
png_dir=os.path.join(out,'png')
glb_dir=os.path.join(out,'glb')
mesh_root=os.path.join(out,'object_meshes')
os.makedirs(png_dir, exist_ok=True)
os.makedirs(glb_dir, exist_ok=True)
os.makedirs(mesh_root, exist_ok=True)
print('num_files', len(pt_files), flush=True)
ok=0
fail=0
for idx, pt in enumerate(pt_files, 1):
    name=os.path.basename(pt).replace('.pt','')
    try:
        d=torch.load(pt, map_location='cpu')
        sel=d['selected_shape_ids'].long()
        cats=d['dec_objs'][sel].numpy()
        boxes=d['boxes'][sel]
        colors=np.array(sns.color_palette('hls', len(classes)))[cats]
        mesh_dir=os.path.join(mesh_root, name)
        _, meshes, raw = get_generated_models_v2(boxes, d['generated_sdf'], cats, classes, mesh_dir, render_boxes=False, colors=colors, without_lamp=False)
        scene=trimesh.Scene(meshes)
        glb=os.path.join(glb_dir, name+'.glb')
        scene.export(glb)
        img=render_img(meshes)
        png=os.path.join(png_dir, name+'.png')
        cv2.imwrite(png, cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))
        ok += 1
        if idx % 10 == 0 or idx == len(pt_files):
            print('progress', idx, 'ok', ok, 'fail', fail, flush=True)
    except Exception as e:
        fail += 1
        print('failed', name, type(e).__name__, str(e), flush=True)
        traceback.print_exc()
print('done ok', ok, 'fail', fail, 'out', out, flush=True)
