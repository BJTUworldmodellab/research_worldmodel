import argparse, json, math, os, glob, torch
from pathlib import Path

PREDICATES = [
    'in','left','right','front','behind','close by','above','standing on',
    'bigger than','smaller than','taller than','shorter than','symmetrical to',
    'same style as','same super category as','same material as'
]
METRIC_KEYS = ['left','right','front','behind','bigger than','smaller than','taller than','shorter than','standing on','close by','symmetrical to']

def close_distance(a,b):
    ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2
    bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
    dx=max(bx0-ax1,ax0-bx1,0.0); dz=max(bz0-az1,az0-bz1,0.0)
    return math.sqrt(dx*dx+dz*dz)

def footprint_iou(a,b):
    ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2
    bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
    ix0,iz0=max(ax0,bx0),max(az0,bz0); ix1,iz1=min(ax1,bx1),min(az1,bz1)
    inter=max(ix1-ix0,0.0)*max(iz1-iz0,0.0)
    aa=max(ax1-ax0,0.0)*max(az1-az0,0.0); ab=max(bx1-bx0,0.0)*max(bz1-bz0,0.0)
    den=aa+ab-inter
    return inter/den if den else 0.0

def satisfies(boxes, tri, strict=True):
    s,p,o=tri
    if s>=len(boxes) or o>=len(boxes) or p>=len(PREDICATES): return None
    bs,bo=boxes[s],boxes[o]; pred=PREDICATES[p]
    if strict and pred in {'left','right','front','behind'} and footprint_iou(bs,bo)>0.3: return False
    if pred=='left': return bs[5]-bo[5] < -0.05
    if pred=='right': return bs[5]-bo[5] > 0.05
    if pred=='front': return bs[3]-bo[3] > -0.05
    if pred=='behind': return bs[3]-bo[3] < 0.05
    if pred=='bigger than':
        vs,vo=bs[0]*bs[1]*bs[2],bo[0]*bo[1]*bo[2]; return (vs-vo)/vs >= 0.15 if vs else False
    if pred=='smaller than':
        vs,vo=bs[0]*bs[1]*bs[2],bo[0]*bo[1]*bo[2]; return (vs-vo)/vs <= -0.15 if vs else False
    if pred=='taller than':
        hs,ho=bs[4]+bs[1],bo[4]+bo[1]; return (hs-ho)/hs >= 0.1 if hs else False
    if pred=='shorter than':
        hs,ho=bs[4]+bs[1],bo[4]+bo[1]; return (hs-ho)/hs <= -0.1 if hs else False
    if pred=='standing on': return abs(bs[4]-bo[4]) < 0.04
    if pred=='close by': return close_distance(bs,bo) <= 0.45
    if pred=='symmetrical to':
        return min(math.dist(c,(bo[3],bo[5])) for c in [(-bs[3],-bs[5]),(-bs[3],bs[5]),(bs[3],-bs[5])]) < 0.45
    return None

def score_scene(boxes, triples):
    totals={k:{'ok':0,'total':0} for k in METRIC_KEYS+['total']}
    for tri in triples:
        if tri[1]>=len(PREDICATES): continue
        pred=PREDICATES[tri[1]]; ok=satisfies(boxes, tri)
        if ok is None or pred not in totals: continue
        totals[pred]['total'] += 1; totals[pred]['ok'] += int(ok)
        totals['total']['total'] += 1; totals['total']['ok'] += int(ok)
    return totals

def merge_scores(dst, src):
    for k,v in src.items():
        dst[k]['ok'] += v['ok']; dst[k]['total'] += v['total']

def summarize(totals):
    return {k:{'ok':v['ok'],'total':v['total'],'acc':(v['ok']/v['total'] if v['total'] else None)} for k,v in totals.items()}

def repair_once(boxes, triples, step=0.65):
    out=[list(b) for b in boxes]; edits=0; movement=0.0
    for s,p,o in triples:
        if s>=len(out) or o>=len(out) or p>=len(PREDICATES): continue
        pred=PREDICATES[p]
        if pred not in {'left','right','front','behind','close by'}: continue
        if satisfies(out, [s,p,o]): continue
        ox,oz=out[o][3],out[o][5]; old=(out[s][3],out[s][5])
        if pred=='left': out[s][5]=oz-max(step,(out[s][2]+out[o][2])*0.35)
        elif pred=='right': out[s][5]=oz+max(step,(out[s][2]+out[o][2])*0.35)
        elif pred=='front': out[s][3]=ox+max(step,(out[s][0]+out[o][0])*0.35)
        elif pred=='behind': out[s][3]=ox-max(step,(out[s][0]+out[o][0])*0.35)
        elif pred=='close by': out[s][3]=ox+min(step*0.5,max(out[o][0],0.1)); out[s][5]=oz
        edits += 1; movement += math.dist(old,(out[s][3],out[s][5]))
    return out, edits, movement

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pt-dir', required=True)
    ap.add_argument('--layout-json', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--passes', type=int, default=2)
    args=ap.parse_args()
    layout=json.load(open(args.layout_json))
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    total_base={k:{'ok':0,'total':0} for k in METRIC_KEYS+['total']}
    total_rep={k:{'ok':0,'total':0} for k in METRIC_KEYS+['total']}
    edits=0; movement=0.0; files=0; missing=[]
    for pt in sorted(glob.glob(os.path.join(args.pt_dir,'*.pt'))):
        d=torch.load(pt, map_location='cpu')
        scan=str(d['scan'])
        if scan not in layout:
            missing.append(scan); continue
        triples=layout[scan]['triples_s_p_o']
        boxes=d['boxes'].clone().float()
        base6=boxes[:,:6].tolist()
        merge_scores(total_base, score_scene(base6, triples))
        rep6=base6
        for _ in range(args.passes):
            rep6,e,m=repair_once(rep6, triples); edits += e; movement += m
        merge_scores(total_rep, score_scene(rep6, triples))
        rep_boxes=boxes.clone(); rep_boxes[:,:6]=torch.tensor(rep6, dtype=rep_boxes.dtype)
        out=dict(d); out['boxes']=rep_boxes; out['repair_meta']={'source':pt,'passes':args.passes,'layout_json':args.layout_json}
        torch.save(out, os.path.join(args.out_dir, os.path.basename(pt)))
        files += 1
    summary={'pt_dir':args.pt_dir,'layout_json':args.layout_json,'out_dir':args.out_dir,'files':files,'missing':missing,'passes':args.passes,'edits':edits,'movement_xz':movement,'baseline':summarize(total_base),'repaired':summarize(total_rep)}
    with open(os.path.join(args.out_dir,'repair_summary.json'),'w') as f: json.dump(summary,f,indent=2)
    print(json.dumps(summary, indent=2))
if __name__=='__main__': main()
