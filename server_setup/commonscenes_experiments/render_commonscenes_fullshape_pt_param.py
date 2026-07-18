import os, glob, argparse, torch, numpy as np, seaborn as sns, trimesh, cv2, traceback
os.environ.setdefault('PYOPENGL_PLATFORM', 'egl')
from helpers.util import get_generated_models_v2
from helpers.visualize_scene import render_img

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pt-dir', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--classes', default='/root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT/classes_all.txt')
    args=ap.parse_args()
    classes=[line.strip() for line in open(args.classes) if line.strip()]
    pt_files=sorted(glob.glob(os.path.join(args.pt_dir,'*.pt')))
    png_dir=os.path.join(args.out_dir,'png'); glb_dir=os.path.join(args.out_dir,'glb'); mesh_root=os.path.join(args.out_dir,'object_meshes')
    os.makedirs(png_dir, exist_ok=True); os.makedirs(glb_dir, exist_ok=True); os.makedirs(mesh_root, exist_ok=True)
    print('num_files', len(pt_files), flush=True)
    ok=0; fail=0
    for idx, pt in enumerate(pt_files, 1):
        name=os.path.basename(pt).replace('.pt','')
        try:
            d=torch.load(pt, map_location='cpu')
            sel=d['selected_shape_ids'].long()
            cats=d['dec_objs'][sel].numpy()
            boxes=d['boxes'][sel]
            colors=np.array(sns.color_palette('hls', len(classes)))[cats]
            _, meshes, raw = get_generated_models_v2(boxes, d['generated_sdf'], cats, classes, os.path.join(mesh_root,name), render_boxes=False, colors=colors, without_lamp=False)
            trimesh.Scene(meshes).export(os.path.join(glb_dir,name+'.glb'))
            img=render_img(meshes)
            cv2.imwrite(os.path.join(png_dir,name+'.png'), cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))
            ok += 1
            if idx % 10 == 0 or idx == len(pt_files): print('progress',idx,'ok',ok,'fail',fail,flush=True)
        except Exception as e:
            fail += 1
            print('failed', name, type(e).__name__, str(e), flush=True)
            traceback.print_exc()
    print('done ok',ok,'fail',fail,'out',args.out_dir,flush=True)
if __name__ == '__main__': main()
