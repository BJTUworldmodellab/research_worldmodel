import argparse, os, glob, json, cv2, numpy as np, torch
from skimage.metrics import structural_similarity as ssim
from math import log10

def psnr(a,b):
    mse=np.mean((a.astype(np.float32)-b.astype(np.float32))**2)
    return float('inf') if mse==0 else 20*log10(255.0/(mse**0.5))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-pt', required=True); ap.add_argument('--ours-pt', required=True)
    ap.add_argument('--base-png', required=True); ap.add_argument('--ours-png', required=True); ap.add_argument('--out-dir', required=True)
    args=ap.parse_args(); os.makedirs(args.out_dir, exist_ok=True)
    rows=[]; moves=[]; changed=0; total=0
    for bp in sorted(glob.glob(args.base_pt+'/*.pt')):
        name=os.path.basename(bp); op=os.path.join(args.ours_pt,name)
        if not os.path.exists(op): continue
        b=torch.load(bp,map_location='cpu'); o=torch.load(op,map_location='cpu')
        bb=b['boxes'][:,:6].float().numpy(); ob=o['boxes'][:,:6].float().numpy(); c=np.linalg.norm((ob-bb)[:,3:6],axis=1)
        rows.append({'scan':name[:-3],'boxes':len(c),'changed_boxes':int((c>1e-6).sum()),'mean_center_movement':float(c.mean()),'max_center_movement':float(c.max())})
        moves.extend(c.tolist()); changed += int((c>1e-6).sum()); total += len(c)
    imgs=[]
    for bp in sorted(glob.glob(args.base_png+'/*.png')):
        name=os.path.basename(bp); op=os.path.join(args.ours_png,name)
        if not os.path.exists(op): continue
        b=cv2.imread(bp, cv2.IMREAD_COLOR); o=cv2.imread(op, cv2.IMREAD_COLOR)
        if b is None or o is None or b.shape != o.shape: continue
        d=np.abs(b.astype(np.int16)-o.astype(np.int16))
        gray_b=cv2.cvtColor(b, cv2.COLOR_BGR2GRAY); gray_o=cv2.cvtColor(o, cv2.COLOR_BGR2GRAY)
        imgs.append({'scan':name[:-4],'mean_abs_pixel_diff':float(d.mean()),'max_abs_pixel_diff':int(d.max()),'changed_pixel_ratio':float((d.sum(axis=2)>0).mean()),'ssim':float(ssim(gray_b, gray_o, data_range=255)),'psnr':psnr(b,o)})
    summary={'scenes_pt':len(rows),'scenes_png':len(imgs),'total_boxes':total,'changed_boxes':changed,'changed_box_ratio':changed/total if total else None,'mean_center_movement':float(np.mean(moves)) if moves else None,'median_center_movement':float(np.median(moves)) if moves else None,'max_center_movement':float(np.max(moves)) if moves else None,'mean_abs_pixel_diff':float(np.mean([x['mean_abs_pixel_diff'] for x in imgs])) if imgs else None,'median_abs_pixel_diff':float(np.median([x['mean_abs_pixel_diff'] for x in imgs])) if imgs else None,'mean_changed_pixel_ratio':float(np.mean([x['changed_pixel_ratio'] for x in imgs])) if imgs else None,'max_changed_pixel_ratio':float(np.max([x['changed_pixel_ratio'] for x in imgs])) if imgs else None,'mean_ssim':float(np.mean([x['ssim'] for x in imgs])) if imgs else None,'median_ssim':float(np.median([x['ssim'] for x in imgs])) if imgs else None,'mean_psnr':float(np.mean([x['psnr'] for x in imgs if np.isfinite(x['psnr'])])) if imgs else None,'median_psnr':float(np.median([x['psnr'] for x in imgs if np.isfinite(x['psnr'])])) if imgs else None,'top_image_changes':sorted(imgs,key=lambda r:r['mean_abs_pixel_diff'],reverse=True)[:10],'top_box_movements':sorted(rows,key=lambda r:r['max_center_movement'],reverse=True)[:10]}
    json.dump(summary,open(os.path.join(args.out_dir,'comparison_summary.json'),'w'),indent=2)
    json.dump(rows,open(os.path.join(args.out_dir,'box_movement_by_scene.json'),'w'),indent=2)
    json.dump(imgs,open(os.path.join(args.out_dir,'image_quality_by_scene.json'),'w'),indent=2)
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
