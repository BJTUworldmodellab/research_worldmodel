import argparse, json, math, os, glob, torch
from pathlib import Path
from helpers.metrics_3dfront import validate_constrains
P=['in','left','right','front','behind','close by','above','standing on','bigger than','smaller than','taller than','shorter than','symmetrical to','same style as','same super category as','same material as']
KEYS=['left','right','front','behind','smaller','bigger','shorter','taller','standing on','close by','symmetrical to','total']
def acc0(): return {k:[] for k in KEYS}
def score_acc(boxes7, triples):
    vocab={'pred_idx_to_name':[p+'\n' for p in P]}
    acc=validate_constrains(torch.tensor(triples,dtype=torch.long), torch.tensor(boxes7,dtype=torch.float32), None, None, vocab, acc0(), file_dist=None, with_norm=False)
    t=acc['total']; return (sum(t)/len(t) if t else 0.0), acc
def merge(dst, src):
    for k,v in src.items(): dst[k].extend(v)
def summarize(acc):
    out={}
    for k,v in acc.items(): out[k]={'ok':int(sum(v)),'total':len(v),'acc':float(sum(v)/len(v)) if v else None}
    vals=[out[k]['acc'] for k in KEYS if k!='total' and out[k]['acc'] is not None]
    out['mean_of_means']=float(sum(vals)/len(vals)) if vals else None
    return out
def candidate_positions(boxes, s, p, o):
    bs,bo=boxes[s],boxes[o]
    sx,sy,sz=bs[0],bs[1],bs[2]; ox,oy,oz=bo[3],bo[4],bo[5]
    cur=(bs[3],bs[4],bs[5])
    c=[]
    margin=0.08
    if P[p]=='left': c.append((bs[3],bs[4],oz - max(0.12, (sz+bo[2])*0.55 + margin)))
    elif P[p]=='right': c.append((bs[3],bs[4],oz + max(0.12, (sz+bo[2])*0.55 + margin)))
    elif P[p]=='front': c.append((ox + max(0.12, (sx+bo[0])*0.55 + margin),bs[4],bs[5]))
    elif P[p]=='behind': c.append((ox - max(0.12, (sx+bo[0])*0.55 + margin),bs[4],bs[5]))
    elif P[p]=='close by':
        # Try several non-overlapping nearby placements around the object.
        radii=[0.15,0.3,0.45,0.6]
        dirs=[(1,0),(-1,0),(0,1),(0,-1),(0.7,0.7),(0.7,-0.7),(-0.7,0.7),(-0.7,-0.7)]
        for r in radii:
            for dx,dz in dirs:
                n=math.sqrt(dx*dx+dz*dz); c.append((ox+dx/n*r, bs[4], oz+dz/n*r))
        # Also try halfway toward object.
        c.append(((bs[3]+ox)/2, bs[4], (bs[5]+oz)/2))
    return c
def repair_scene(boxes7, triples, max_move=2.0, passes=2, eps=1e-9):
    base=[list(b) for b in boxes7]; cur=[list(b) for b in boxes7]
    cur_score,_=score_acc(cur, triples); edits=0
    for _ in range(passes):
        improved=False
        for s,p,o in triples:
            if p>=len(P) or P[p] not in {'left','right','front','behind','close by'} or s>=len(cur) or o>=len(cur): continue
            best_score=cur_score; best=None
            for x,y,z in candidate_positions(cur,s,p,o):
                dist=math.dist((base[s][3],base[s][4],base[s][5]),(x,y,z))
                if dist > max_move: continue
                cand=[list(b) for b in cur]; cand[s][3]=x; cand[s][4]=y; cand[s][5]=z
                sc,_=score_acc(cand, triples)
                if sc > best_score + eps:
                    best_score=sc; best=cand
            if best is not None:
                cur=best; cur_score=best_score; edits+=1; improved=True
        if not improved: break
    centers=[math.dist((a[3],a[4],a[5]),(b[3],b[4],b[5])) for a,b in zip(base,cur)]
    return cur, cur_score, edits, centers
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pt-dir',required=True); ap.add_argument('--layout-json',required=True); ap.add_argument('--out-dir',required=True); ap.add_argument('--max-move',type=float,default=2.0); ap.add_argument('--passes',type=int,default=2); args=ap.parse_args()
    layout=json.load(open(args.layout_json)); Path(args.out_dir).mkdir(parents=True,exist_ok=True)
    baseA=acc0(); repA=acc0(); accepted=0; improved=0; files=0; changed=0; total=0; moves=[]; edits_total=0
    for pt in sorted(glob.glob(os.path.join(args.pt_dir,'*.pt'))):
        d=torch.load(pt,map_location='cpu'); scan=str(d['scan'])
        if scan not in layout: continue
        triples=layout[scan]['triples_s_p_o']; boxes=d['boxes'].clone().float(); b7=boxes.tolist(); bsc,bacc=score_acc(b7,triples)
        r7,rsc,edits,centers=repair_scene(b7,triples,args.max_move,args.passes)
        accept=rsc > bsc + 1e-9
        f7=r7 if accept else b7; fsc,facc=score_acc(f7,triples)
        merge(baseA,bacc); merge(repA,facc)
        out=dict(d); out_boxes=boxes.clone(); out_boxes[:,:6]=torch.tensor([x[:6] for x in f7],dtype=out_boxes.dtype); out['boxes']=out_boxes; out['repair_meta']={'official_search':True,'accepted':accept,'base_score':bsc,'candidate_score':rsc,'final_score':fsc,'edits':edits,'max_move':max(centers) if centers else 0.0}
        torch.save(out, os.path.join(args.out_dir, os.path.basename(pt)))
        files+=1; accepted+=int(accept); improved+=int(rsc>bsc); edits_total+=edits if accept else 0; changed+=sum(c>1e-6 for c in centers) if accept else 0; total+=len(centers); moves.extend(centers if accept else [0.0]*len(centers))
    summary={'out_dir':args.out_dir,'files':files,'accepted_scenes':accepted,'candidate_improved_scenes':improved,'edits':edits_total,'max_move_threshold':args.max_move,'changed_boxes':changed,'total_boxes':total,'changed_box_ratio':changed/total if total else None,'mean_center_movement':sum(moves)/len(moves) if moves else None,'max_center_movement':max(moves) if moves else None,'baseline_official':summarize(baseA),'official_search':summarize(repA)}
    json.dump(summary,open(os.path.join(args.out_dir,'repair_summary.json'),'w'),indent=2); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
