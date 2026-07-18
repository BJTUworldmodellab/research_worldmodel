import os, glob, json, torch, cv2, numpy as np, math
base_pt='/root/autodl-tmp/RelationAwareInstructScene/commonscenes_models/balancing/all/results/fullshape_pt_epoch195'
ours_pt='/root/RelationAwareInstructScene/results/commonscenes_ours_repair_pt_epoch195_bedroom'
base_png='/root/RelationAwareInstructScene/results/commonscenes_render_baseline_epoch195_bedroom/png'
ours_png='/root/RelationAwareInstructScene/results/commonscenes_render_ours_repair_epoch195_bedroom/png'
out='/root/RelationAwareInstructScene/results/commonscenes_ours_repair_compare_epoch195_bedroom'
os.makedirs(out, exist_ok=True)
rows=[]
movements=[]
changed_boxes=0
total_boxes=0
for bp in sorted(glob.glob(base_pt+'/*.pt')):
    name=os.path.basename(bp)
    op=os.path.join(ours_pt,name)
    if not os.path.exists(op): continue
    b=torch.load(bp,map_location='cpu'); o=torch.load(op,map_location='cpu')
    bb=b['boxes'][:,:6].float().numpy(); ob=o['boxes'][:,:6].float().numpy()
    diff=ob-bb
    center=np.linalg.norm(diff[:,3:6],axis=1)
    size=np.linalg.norm(diff[:,:3],axis=1)
    movements.extend(center.tolist())
    changed_boxes += int((center>1e-6).sum())
    total_boxes += len(center)
    rows.append({'scan':name[:-3],'boxes':len(center),'changed_boxes':int((center>1e-6).sum()),'mean_center_movement':float(center.mean()),'max_center_movement':float(center.max()),'mean_size_change':float(size.mean())})
# image diffs
img_rows=[]
for bp in sorted(glob.glob(base_png+'/*.png')):
    name=os.path.basename(bp)
    op=os.path.join(ours_png,name)
    if not os.path.exists(op): continue
    bi=cv2.imread(bp, cv2.IMREAD_COLOR); oi=cv2.imread(op, cv2.IMREAD_COLOR)
    if bi is None or oi is None or bi.shape!=oi.shape: continue
    d=np.abs(bi.astype(np.int16)-oi.astype(np.int16))
    img_rows.append({'scan':name[:-4],'mean_abs_pixel_diff':float(d.mean()),'max_abs_pixel_diff':int(d.max()),'changed_pixel_ratio':float((d.sum(axis=2)>0).mean())})
summary={
 'base_pt':base_pt,'ours_pt':ours_pt,'base_png':base_png,'ours_png':ours_png,
 'scenes_pt':len(rows),'scenes_png':len(img_rows),'total_boxes':total_boxes,'changed_boxes':changed_boxes,
 'changed_box_ratio':changed_boxes/total_boxes if total_boxes else None,
 'mean_center_movement':float(np.mean(movements)) if movements else None,
 'median_center_movement':float(np.median(movements)) if movements else None,
 'max_center_movement':float(np.max(movements)) if movements else None,
 'mean_abs_pixel_diff':float(np.mean([r['mean_abs_pixel_diff'] for r in img_rows])) if img_rows else None,
 'median_abs_pixel_diff':float(np.median([r['mean_abs_pixel_diff'] for r in img_rows])) if img_rows else None,
 'mean_changed_pixel_ratio':float(np.mean([r['changed_pixel_ratio'] for r in img_rows])) if img_rows else None,
 'max_changed_pixel_ratio':float(np.max([r['changed_pixel_ratio'] for r in img_rows])) if img_rows else None,
 'top_image_changes':sorted(img_rows,key=lambda r:r['mean_abs_pixel_diff'],reverse=True)[:10],
 'top_box_movements':sorted(rows,key=lambda r:r['max_center_movement'],reverse=True)[:10],
}
json.dump(summary, open(os.path.join(out,'comparison_summary.json'),'w'), indent=2)
json.dump(rows, open(os.path.join(out,'box_movement_by_scene.json'),'w'), indent=2)
json.dump(img_rows, open(os.path.join(out,'image_diff_by_scene.json'),'w'), indent=2)
print(json.dumps(summary, indent=2))
