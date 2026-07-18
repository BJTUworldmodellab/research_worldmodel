import argparse,json,math
from pathlib import Path
P=['in','left','right','front','behind','close by','above','standing on','bigger than','smaller than','taller than','shorter than','symmetrical to','same style as','same super category as','same material as']
K=['left','right','front','behind','bigger than','smaller than','taller than','shorter than','standing on','close by','symmetrical to']
def gap(a,b):
 ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2; bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
 dx=max(bx0-ax1,ax0-bx1,0.0); dz=max(bz0-az1,az0-bz1,0.0); return math.sqrt(dx*dx+dz*dz)
def iou(a,b):
 ax0,az0,ax1,az1=a[3]-a[0]/2,a[5]-a[2]/2,a[3]+a[0]/2,a[5]+a[2]/2; bx0,bz0,bx1,bz1=b[3]-b[0]/2,b[5]-b[2]/2,b[3]+b[0]/2,b[5]+b[2]/2
 ix0,iz0=max(ax0,bx0),max(az0,bz0); ix1,iz1=min(ax1,bx1),min(az1,bz1); inter=max(ix1-ix0,0)*max(iz1-iz0,0); aa=max(ax1-ax0,0)*max(az1-az0,0); ab=max(bx1-bx0,0)*max(bz1-bz0,0); den=aa+ab-inter; return inter/den if den else 0
def ok(boxes,t):
 s,p,o=t
 if s>=len(boxes) or o>=len(boxes) or p>=len(P): return None
 a,b=boxes[s],boxes[o]; r=P[p]
 if r in {'left','right','front','behind'} and iou(a,b)>0.3: return False
 if r=='left': return a[5]-b[5]<-0.05
 if r=='right': return a[5]-b[5]>0.05
 if r=='front': return a[3]-b[3]>-0.05
 if r=='behind': return a[3]-b[3]<0.05
 if r=='bigger than':
  va,vb=a[0]*a[1]*a[2],b[0]*b[1]*b[2]; return (va-vb)/va>=0.15 if va else False
 if r=='smaller than':
  va,vb=a[0]*a[1]*a[2],b[0]*b[1]*b[2]; return (va-vb)/va<=-0.15 if va else False
 if r=='taller than':
  ha,hb=a[4]+a[1],b[4]+b[1]; return (ha-hb)/ha>=0.1 if ha else False
 if r=='shorter than':
  ha,hb=a[4]+a[1],b[4]+b[1]; return (ha-hb)/ha<=-0.1 if ha else False
 if r=='standing on': return abs(a[4]-b[4])<0.04
 if r=='close by': return gap(a,b)<=0.45
 if r=='symmetrical to': return min(math.dist(c,(b[3],b[5])) for c in [(-a[3],-a[5]),(-a[3],a[5]),(a[3],-a[5])])<0.45
 return None
def score(data):
 d={k:{'ok':0,'total':0} for k in K+['total']}
 for sc in data.values():
  boxes=sc['boxes_denormalized_xyzwhd']
  for t in sc['triples_s_p_o']:
   r=P[t[1]] if t[1]<len(P) else None; v=ok(boxes,t)
   if v is None or r not in d: continue
   d[r]['total']+=1; d[r]['ok']+=int(v); d['total']['total']+=1; d['total']['ok']+=int(v)
 return {k:{'ok':v['ok'],'total':v['total'],'acc':(v['ok']/v['total'] if v['total'] else None)} for k,v in d.items()}
def repair(data,passes=2,step=.65):
 res={}; edits=0; move=0.0
 for key,sc in data.items():
  boxes=[list(x) for x in sc['boxes_denormalized_xyzwhd']]
  for _ in range(passes):
   for s,p,o in sc['triples_s_p_o']:
    if s>=len(boxes) or o>=len(boxes) or p>=len(P): continue
    r=P[p]
    if r not in {'left','right','front','behind','close by'} or ok(boxes,[s,p,o]): continue
    old=(boxes[s][3],boxes[s][5]); ox,oz=boxes[o][3],boxes[o][5]
    if r=='left': boxes[s][5]=oz-max(step,(boxes[s][2]+boxes[o][2])*.35)
    elif r=='right': boxes[s][5]=oz+max(step,(boxes[s][2]+boxes[o][2])*.35)
    elif r=='front': boxes[s][3]=ox+max(step,(boxes[s][0]+boxes[o][0])*.35)
    elif r=='behind': boxes[s][3]=ox-max(step,(boxes[s][0]+boxes[o][0])*.35)
    elif r=='close by': boxes[s][3]=ox+min(step*.5,max(boxes[o][0],.1)); boxes[s][5]=oz
    edits+=1; move+=math.dist(old,(boxes[s][3],boxes[s][5]))
  ns=dict(sc); ns['boxes_denormalized_xyzwhd']=boxes; res[key]=ns
 return res,edits,move
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output-dir',required=True); ap.add_argument('--passes',type=int,default=2); a=ap.parse_args(); data=json.load(open(a.input)); base=score(data); rep,e,m=repair(data,a.passes); rs=score(rep); out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); stem=Path(a.input).stem; rp=out/(stem+'_repair_v2_p%d.json'%a.passes); sp=out/(stem+'_repair_v2_p%d_summary.json'%a.passes); json.dump(rep,open(rp,'w'),indent=2); summ={'input':a.input,'repaired_boxes':str(rp),'scenes':len(data),'passes':a.passes,'edits':e,'movement_xz':m,'baseline':base,'repaired':rs}; json.dump(summ,open(sp,'w'),indent=2); print(json.dumps(summ,indent=2))
if __name__=='__main__': main()
