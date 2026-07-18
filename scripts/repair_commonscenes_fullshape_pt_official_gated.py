import argparse, json, math, os, glob, torch
from pathlib import Path
from helpers.metrics_3dfront import validate_constrains
PREDICATES=['in','left','right','front','behind','close by','above','standing on','bigger than','smaller than','taller than','shorter than','symmetrical to','same style as','same super category as','same material as']
OFF_KEYS=['left','right','front','behind','smaller','bigger','shorter','taller','standing on','close by','symmetrical to','total']
def make_acc(): return {k:[] for k in OFF_KEYS}
def official_score(boxes, triples):
    vocab={'pred_idx_to_name':[p+'\n' for p in PREDICATES]}
    acc=validate_constrains(torch.tensor(triples,dtype=torch.long), torch.tensor(boxes,dtype=torch.float32), None, None, vocab, make_acc(), file_dist=None, with_norm=False)
    total=acc['total']; return sum(total)/len(total) if total else 0.0, acc
def close_distance(a,b):
    ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2; bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
    dx=max(bx0-ax1,ax0-bx1,0.0); dz=max(bz0-az1,az0-bz1,0.0); return math.sqrt(dx*dx+dz*dz)
def footprint_iou(a,b):
    ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2; bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
    ix0,iz0=max(ax0,bx0),max(az0,bz0); ix1,iz1=min(ax1,bx1),min(az1,bz1); inter=max(ix1-ix0,0.0)*max(iz1-iz0,0.0); aa=max(ax1-ax0,0.0)*max(az1-az0,0.0); ab=max(bx1-bx0,0.0)*max(bz1-bz0,0.0); den=aa+ab-inter; return inter/den if den else 0.0
def sat(boxes,tri):
    s,p,o=tri
    if s>=len(boxes) or o>=len(boxes) or p>=len(PREDICATES): return None
    bs,bo=boxes[s],boxes[o]; pr=PREDICATES[p]
    if pr in {'left','right','front','behind'} and footprint_iou(bs,bo)>0.3: return False
    if pr=='left': return bs[5]-bo[5] < -0.05
    if pr=='right': return bs[5]-bo[5] > 0.05
    if pr=='front': return bs[3]-bo[3] > -0.05
    if pr=='behind': return bs[3]-bo[3] < 0.05
    if pr=='close by': return close_distance(bs,bo) <= 0.45
    return None
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
def merge(dst, src):
    for k,v in src.items(): dst[k].extend(v)
def summarize(acc):
    out={}
    for k,v in acc.items(): out[k]={'ok':int(sum(v)),'total':len(v),'acc':float(sum(v)/len(v)) if v else None}
    vals=[out[k]['acc'] for k in OFF_KEYS if k!='total' and out[k]['acc'] is not None]
    out['mean_of_means']=float(sum(vals)/len(vals)) if vals else None
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pt-dir',required=True); ap.add_argument('--layout-json',required=True); ap.add_argument('--out-dir',required=True); ap.add_argument('--passes',type=int,default=2); ap.add_argument('--max-move',type=float,default=2.0); ap.add_argument('--min-gain',type=float,default=0.0); args=ap.parse_args()
    layout=json.load(open(args.layout_json)); Path(args.out_dir).mkdir(parents=True,exist_ok=True)
    baseA=make_acc(); finalA=make_acc(); accepted=0; rejected=0; changed=0; total_boxes=0; moves=[]; files=0
    for pt in sorted(glob.glob(os.path.join(args.pt_dir,'*.pt'))):
        d=torch.load(pt,map_location='cpu'); scan=str(d['scan'])
        if scan not in layout: continue
        triples=layout[scan]['triples_s_p_o']; boxes=d['boxes'].clone().float(); b7=boxes.tolist(); b6=[x[:6] for x in b7]
        r6=b6
        for _ in range(args.passes): r6=repair_once(r6,triples)
        r7=[list(r6[i])+[b7[i][6]] for i in range(len(b7))]
        bscore,bacc=official_score(b7,triples); rscore,racc=official_score(r7,triples)
        centers=[math.dist((a[3],a[4],a[5]),(b[3],b[4],b[5])) for a,b in zip(b6,r6)]
        maxm=max(centers) if centers else 0.0
        accept=(rscore > bscore + args.min_gain and maxm <= args.max_move)
        final7=r7 if accept else b7; fscore,facc=official_score(final7,triples)
        merge(baseA,bacc); merge(finalA,facc)
        out=dict(d); out_boxes=boxes.clone(); out_boxes[:,:6]=torch.tensor([x[:6] for x in final7],dtype=out_boxes.dtype); out['boxes']=out_boxes; out['repair_meta']={'official_gated':True,'accepted':accept,'base_score':bscore,'candidate_score':rscore,'final_score':fscore,'max_move':maxm,'passes':args.passes,'threshold':args.max_move}
        torch.save(out, os.path.join(args.out_dir, os.path.basename(pt)))
        accepted+=int(accept); rejected+=int(not accept); files+=1; changed+=sum(c>1e-6 for c in centers) if accept else 0; total_boxes+=len(centers); moves.extend(centers if accept else [0.0]*len(centers))
    summary={'out_dir':args.out_dir,'files':files,'accepted_scenes':accepted,'rejected_scenes':rejected,'passes':args.passes,'max_move_threshold':args.max_move,'changed_boxes':changed,'total_boxes':total_boxes,'changed_box_ratio':changed/total_boxes if total_boxes else None,'mean_center_movement':sum(moves)/len(moves) if moves else None,'max_center_movement':max(moves) if moves else None,'baseline_official':summarize(baseA),'official_gated':summarize(finalA)}
    json.dump(summary,open(os.path.join(args.out_dir,'repair_summary.json'),'w'),indent=2); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
