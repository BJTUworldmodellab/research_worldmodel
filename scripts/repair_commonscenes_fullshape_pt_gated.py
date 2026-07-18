import argparse, json, math, os, glob, torch
from pathlib import Path
PREDICATES=['in','left','right','front','behind','close by','above','standing on','bigger than','smaller than','taller than','shorter than','symmetrical to','same style as','same super category as','same material as']
METRIC_KEYS=['left','right','front','behind','bigger than','smaller than','taller than','shorter than','standing on','close by','symmetrical to']
def close_distance(a,b):
 ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2; bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
 dx=max(bx0-ax1,ax0-bx1,0.0); dz=max(bz0-az1,az0-bz1,0.0); return math.sqrt(dx*dx+dz*dz)
def footprint_iou(a,b):
 ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2; bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
 ix0,iz0=max(ax0,bx0),max(az0,bz0); ix1,iz1=min(ax1,bx1),min(az1,bz1); inter=max(ix1-ix0,0.0)*max(iz1-iz0,0.0); aa=max(ax1-ax0,0.0)*max(az1-az0,0.0); ab=max(bx1-bx0,0.0)*max(bz1-bz0,0.0); den=aa+ab-inter; return inter/den if den else 0.0
def sat(boxes,tri,strict=True):
 s,p,o=tri
 if s>=len(boxes) or o>=len(boxes) or p>=len(PREDICATES): return None
 bs,bo=boxes[s],boxes[o]; pr=PREDICATES[p]
 if strict and pr in {'left','right','front','behind'} and footprint_iou(bs,bo)>0.3: return False
 if pr=='left': return bs[5]-bo[5] < -0.05
 if pr=='right': return bs[5]-bo[5] > 0.05
 if pr=='front': return bs[3]-bo[3] > -0.05
 if pr=='behind': return bs[3]-bo[3] < 0.05
 if pr=='bigger than':
  vs,vo=bs[0]*bs[1]*bs[2],bo[0]*bo[1]*bo[2]; return (vs-vo)/vs >= 0.15 if vs else False
 if pr=='smaller than':
  vs,vo=bs[0]*bs[1]*bs[2],bo[0]*bo[1]*bo[2]; return (vs-vo)/vs <= -0.15 if vs else False
 if pr=='taller than':
  hs,ho=bs[4]+bs[1],bo[4]+bo[1]; return (hs-ho)/hs >= 0.1 if hs else False
 if pr=='shorter than':
  hs,ho=bs[4]+bs[1],bo[4]+bo[1]; return (hs-ho)/hs <= -0.1 if hs else False
 if pr=='standing on': return abs(bs[4]-bo[4]) < 0.04
 if pr=='close by': return close_distance(bs,bo)<=0.45
 if pr=='symmetrical to': return min(math.dist(c,(bo[3],bo[5])) for c in [(-bs[3],-bs[5]),(-bs[3],bs[5]),(bs[3],-bs[5])])<0.45
 return None
def totals0(): return {k:{'ok':0,'total':0} for k in METRIC_KEYS+['total']}
def score(boxes,triples):
 t=totals0()
 for tri in triples:
  if tri[1]>=len(PREDICATES): continue
  pr=PREDICATES[tri[1]]; ok=sat(boxes,tri)
  if ok is None or pr not in t: continue
  t[pr]['total']+=1; t[pr]['ok']+=int(ok); t['total']['total']+=1; t['total']['ok']+=int(ok)
 return t
def merge(a,b):
 for k,v in b.items(): a[k]['ok']+=v['ok']; a[k]['total']+=v['total']
def acc(t): return t['total']['ok']/t['total']['total'] if t['total']['total'] else 0
def summarize(t): return {k:{'ok':v['ok'],'total':v['total'],'acc':(v['ok']/v['total'] if v['total'] else None)} for k,v in t.items()}
def repair_once(boxes,triples,step=0.65):
 out=[list(b) for b in boxes]
 for s,p,o in triples:
  if s>=len(out) or o>=len(out) or p>=len(PREDICATES): continue
  pr=PREDICATES[p]
  if pr not in {'left','right','front','behind','close by'} or sat(out,[s,p,o]): continue
  ox,oz=out[o][3],out[o][5]
  if pr=='left': out[s][5]=oz-max(step,(out[s][2]+out[o][2])*0.35)
  elif pr=='right': out[s][5]=oz+max(step,(out[s][2]+out[o][2])*0.35)
  elif pr=='front': out[s][3]=ox+max(step,(out[s][0]+out[o][0])*0.35)
  elif pr=='behind': out[s][3]=ox-max(step,(out[s][0]+out[o][0])*0.35)
  elif pr=='close by': out[s][3]=ox+min(step*0.5,max(out[o][0],0.1)); out[s][5]=oz
 return out
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--pt-dir',required=True); ap.add_argument('--layout-json',required=True); ap.add_argument('--out-dir',required=True); ap.add_argument('--passes',type=int,default=2); ap.add_argument('--max-move',type=float,default=1.5); ap.add_argument('--min-gain',type=float,default=0.0); args=ap.parse_args()
 layout=json.load(open(args.layout_json)); Path(args.out_dir).mkdir(parents=True,exist_ok=True)
 baseT,repT=totals0(),totals0(); accepted=0; rejected=0; total_files=0; changed_boxes=0; total_boxes=0; moves=[]
 for pt in sorted(glob.glob(os.path.join(args.pt_dir,'*.pt'))):
  d=torch.load(pt,map_location='cpu'); scan=str(d['scan'])
  if scan not in layout: continue
  triples=layout[scan]['triples_s_p_o']; boxes=d['boxes'].clone().float(); b6=boxes[:,:6].tolist(); base=score(b6,triples)
  r6=b6
  for _ in range(args.passes): r6=repair_once(r6,triples)
  rep=score(r6,triples); centers=[math.dist((a[3],a[4],a[5]),(b[3],b[4],b[5])) for a,b in zip(b6,r6)]; max_move=max(centers) if centers else 0.0
  accept=(acc(rep) > acc(base)+args.min_gain and max_move <= args.max_move)
  final6=r6 if accept else b6
  final=score(final6,triples); merge(baseT,base); merge(repT,final)
  out=dict(d); out_boxes=boxes.clone(); out_boxes[:,:6]=torch.tensor(final6,dtype=out_boxes.dtype); out['boxes']=out_boxes; out['repair_meta']={'gated':True,'accepted':accept,'max_move':max_move,'passes':args.passes,'threshold':args.max_move}
  torch.save(out, os.path.join(args.out_dir, os.path.basename(pt)))
  accepted += int(accept); rejected += int(not accept); total_files += 1; changed_boxes += sum(c>1e-6 for c in centers) if accept else 0; total_boxes += len(centers); moves.extend(centers if accept else [0.0]*len(centers))
 summary={'out_dir':args.out_dir,'files':total_files,'accepted_scenes':accepted,'rejected_scenes':rejected,'passes':args.passes,'max_move_threshold':args.max_move,'changed_boxes':changed_boxes,'total_boxes':total_boxes,'changed_box_ratio':changed_boxes/total_boxes if total_boxes else None,'mean_center_movement':sum(moves)/len(moves) if moves else None,'max_center_movement':max(moves) if moves else None,'baseline':summarize(baseT),'gated_repaired':summarize(repT)}
 json.dump(summary,open(os.path.join(args.out_dir,'repair_summary.json'),'w'),indent=2); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
