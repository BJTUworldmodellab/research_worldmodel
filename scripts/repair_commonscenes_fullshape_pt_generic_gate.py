import argparse, json, math, os, glob, torch
from pathlib import Path

PREDICATES=['in','left','right','front','behind','close by','above','standing on','bigger than','smaller than','taller than','shorter than','symmetrical to','same style as','same super category as','same material as']
REL_KEYS=['left','right','front','behind','close by','bigger than','smaller than','taller than','shorter than','standing on','symmetrical to']
MOVE_RELS={'left','right','front','behind','close by'}

def footprint(box):
    return (box[3]-box[0]/2, box[5]-box[2]/2, box[3]+box[0]/2, box[5]+box[2]/2)

def footprint_iou(a,b):
    ax0,az0,ax1,az1=footprint(a); bx0,bz0,bx1,bz1=footprint(b)
    ix0,iz0=max(ax0,bx0),max(az0,bz0); ix1,iz1=min(ax1,bx1),min(az1,bz1)
    inter=max(ix1-ix0,0.0)*max(iz1-iz0,0.0)
    aa=max(ax1-ax0,0.0)*max(az1-az0,0.0); ab=max(bx1-bx0,0.0)*max(bz1-bz0,0.0)
    den=aa+ab-inter
    return inter/den if den else 0.0

def footprint_gap(a,b):
    ax0,az0,ax1,az1=footprint(a); bx0,bz0,bx1,bz1=footprint(b)
    dx=max(bx0-ax1, ax0-bx1, 0.0); dz=max(bz0-az1, az0-bz1, 0.0)
    return math.sqrt(dx*dx+dz*dz)

def rel_ok(boxes, tri, strict=True):
    s,p,o=tri
    if s>=len(boxes) or o>=len(boxes) or p>=len(PREDICATES): return None
    bs,bo=boxes[s],boxes[o]; pred=PREDICATES[p]
    if strict and pred in {'left','right','front','behind'} and footprint_iou(bs,bo)>0.3: return False
    if pred=='left': return bs[5]-bo[5] < -0.05
    if pred=='right': return bs[5]-bo[5] > 0.05
    if pred=='front': return bs[3]-bo[3] > -0.05
    if pred=='behind': return bs[3]-bo[3] < 0.05
    if pred=='close by': return footprint_gap(bs,bo) <= 0.45
    if pred=='bigger than':
        vs,vo=bs[0]*bs[1]*bs[2],bo[0]*bo[1]*bo[2]
        return (vs-vo)/vs >= 0.15 if vs else False
    if pred=='smaller than':
        vs,vo=bs[0]*bs[1]*bs[2],bo[0]*bo[1]*bo[2]
        return (vs-vo)/vs <= -0.15 if vs else False
    if pred=='taller than':
        hs,ho=bs[4]+bs[1],bo[4]+bo[1]
        return (hs-ho)/hs >= 0.1 if hs else False
    if pred=='shorter than':
        hs,ho=bs[4]+bs[1],bo[4]+bo[1]
        return (hs-ho)/hs <= -0.1 if hs else False
    if pred=='standing on': return abs(bs[4]-bo[4]) < 0.04
    if pred=='symmetrical to':
        return min(math.dist(c,(bo[3],bo[5])) for c in [(-bs[3],-bs[5]),(-bs[3],bs[5]),(bs[3],-bs[5])]) < 0.45
    return None

def score_relations(boxes, triples):
    totals={k:{'ok':0,'total':0} for k in REL_KEYS+['total']}
    for tri in triples:
        if tri[1]>=len(PREDICATES): continue
        pred=PREDICATES[tri[1]]
        if pred not in totals: continue
        ok=rel_ok(boxes,tri)
        if ok is None: continue
        totals[pred]['ok']+=int(ok); totals[pred]['total']+=1
        totals['total']['ok']+=int(ok); totals['total']['total']+=1
    return totals

def collision_penalty(boxes):
    penalty=0.0; pairs=0; max_iou=0.0
    for i in range(len(boxes)):
        for j in range(i+1,len(boxes)):
            # skip floor/_scene-like very large or zero labels by geometry only: still conservative.
            iou=footprint_iou(boxes[i],boxes[j])
            if iou>0.05:
                penalty += iou; pairs += 1; max_iou=max(max_iou,iou)
    return penalty,pairs,max_iou

def out_of_bound_penalty(boxes, bound=3.2):
    p=0.0
    for b in boxes:
        x,z=b[3],b[5]
        p += max(abs(x)-bound,0.0)+max(abs(z)-bound,0.0)
    return p

def objective(boxes, triples, base_boxes, collision_w=8.0, oob_w=4.0, move_w=0.03):
    rel=score_relations(boxes,triples)['total']
    rel_acc=rel['ok']/rel['total'] if rel['total'] else 0.0
    coll,_,_=collision_penalty(boxes)
    oob=out_of_bound_penalty(boxes)
    mean_move=sum(math.dist((a[3],a[4],a[5]),(b[3],b[4],b[5])) for a,b in zip(base_boxes,boxes))/max(len(boxes),1)
    return rel_acc - collision_w*coll/max(len(boxes),1) - oob_w*oob/max(len(boxes),1) - move_w*mean_move

def candidate_positions(boxes,s,p,o):
    bs,bo=boxes[s],boxes[o]
    c=[]; margin=0.08
    x,y,z=bs[3],bs[4],bs[5]; ox,oy,oz=bo[3],bo[4],bo[5]
    pred=PREDICATES[p]
    if pred=='left': c.append((x,y,oz-max(0.12,(bs[2]+bo[2])*0.55+margin)))
    elif pred=='right': c.append((x,y,oz+max(0.12,(bs[2]+bo[2])*0.55+margin)))
    elif pred=='front': c.append((ox+max(0.12,(bs[0]+bo[0])*0.55+margin),y,z))
    elif pred=='behind': c.append((ox-max(0.12,(bs[0]+bo[0])*0.55+margin),y,z))
    elif pred=='close by':
        # Move near, but not necessarily on top of target; generic, not evaluator-specific.
        radii=[0.2,0.35,0.5]
        dirs=[(1,0),(-1,0),(0,1),(0,-1),(0.7,0.7),(0.7,-0.7),(-0.7,0.7),(-0.7,-0.7)]
        for r in radii:
            for dx,dz in dirs:
                n=math.sqrt(dx*dx+dz*dz); c.append((ox+dx/n*r,y,oz+dz/n*r))
    return c

def repair_scene(base_boxes, triples, max_move=1.2, passes=2, min_gain=1e-9):
    cur=[list(b) for b in base_boxes]
    cur_obj=objective(cur,triples,base_boxes)
    edits=0
    for _ in range(passes):
        improved=False
        for s,p,o in triples:
            if p>=len(PREDICATES) or PREDICATES[p] not in MOVE_RELS or s>=len(cur) or o>=len(cur): continue
            if rel_ok(cur,[s,p,o]) is True: continue
            best_obj=cur_obj; best=None
            for nx,ny,nz in candidate_positions(cur,s,p,o):
                if math.dist((base_boxes[s][3],base_boxes[s][4],base_boxes[s][5]),(nx,ny,nz)) > max_move: continue
                cand=[list(b) for b in cur]
                cand[s][3],cand[s][4],cand[s][5]=nx,ny,nz
                obj=objective(cand,triples,base_boxes)
                if obj > best_obj + min_gain:
                    best_obj=obj; best=cand
            if best is not None:
                cur=best; cur_obj=best_obj; edits+=1; improved=True
        if not improved: break
    return cur,edits,cur_obj

def merge(dst,src):
    for k,v in src.items(): dst[k]['ok']+=v['ok']; dst[k]['total']+=v['total']

def summarize(t):
    return {k:{'ok':v['ok'],'total':v['total'],'acc':(v['ok']/v['total'] if v['total'] else None)} for k,v in t.items()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pt-dir',required=True); ap.add_argument('--layout-json',required=True); ap.add_argument('--out-dir',required=True)
    ap.add_argument('--max-move',type=float,default=1.2); ap.add_argument('--passes',type=int,default=2)
    args=ap.parse_args()
    layout=json.load(open(args.layout_json)); Path(args.out_dir).mkdir(parents=True,exist_ok=True)
    T0={k:{'ok':0,'total':0} for k in REL_KEYS+['total']}; T1={k:{'ok':0,'total':0} for k in REL_KEYS+['total']}
    files=0; accepted=0; edits_total=0; changed=0; total_boxes=0; moves=[]; coll0=coll1=0.0; pairs0=pairs1=0
    for pt in sorted(glob.glob(os.path.join(args.pt_dir,'*.pt'))):
        d=torch.load(pt,map_location='cpu'); scan=str(d['scan'])
        if scan not in layout: continue
        triples=layout[scan]['triples_s_p_o']; boxes=d['boxes'].clone().float(); base6=boxes[:,:6].tolist()
        rep6,edits,obj=repair_scene(base6,triples,args.max_move,args.passes)
        accept=edits>0
        final6=rep6 if accept else base6
        merge(T0,score_relations(base6,triples)); merge(T1,score_relations(final6,triples))
        c0,p0,_=collision_penalty(base6); c1,p1,_=collision_penalty(final6); coll0+=c0; coll1+=c1; pairs0+=p0; pairs1+=p1
        centers=[math.dist((a[3],a[4],a[5]),(b[3],b[4],b[5])) for a,b in zip(base6,final6)]
        changed+=sum(c>1e-6 for c in centers); total_boxes+=len(centers); moves.extend(centers)
        out=dict(d); out_boxes=boxes.clone(); out_boxes[:,:6]=torch.tensor(final6,dtype=out_boxes.dtype); out['boxes']=out_boxes
        out['repair_meta']={'generic_relation_collision_gate':True,'accepted':accept,'edits':edits,'max_move_threshold':args.max_move,'objective':obj}
        torch.save(out, os.path.join(args.out_dir, os.path.basename(pt)))
        files+=1; accepted+=int(accept); edits_total+=edits
    summary={'out_dir':args.out_dir,'files':files,'accepted_scenes':accepted,'edits':edits_total,'max_move_threshold':args.max_move,'changed_boxes':changed,'total_boxes':total_boxes,'changed_box_ratio':changed/total_boxes if total_boxes else None,'mean_center_movement':sum(moves)/len(moves) if moves else None,'max_center_movement':max(moves) if moves else None,'baseline_generic':summarize(T0),'repaired_generic':summarize(T1),'baseline_collision_penalty':coll0,'repaired_collision_penalty':coll1,'baseline_collision_pairs':pairs0,'repaired_collision_pairs':pairs1}
    json.dump(summary,open(os.path.join(args.out_dir,'repair_summary.json'),'w'),indent=2)
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
