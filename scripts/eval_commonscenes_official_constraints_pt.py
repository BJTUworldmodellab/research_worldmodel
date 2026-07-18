import json, os, glob, torch, argparse
from collections import defaultdict
from helpers.metrics_3dfront import validate_constrains

PREDICATES = [
    'in','left','right','front','behind','close by','above','standing on',
    'bigger than','smaller than','taller than','shorter than','symmetrical to',
    'same style as','same super category as','same material as'
]
OFF_KEYS = ['left','right','front','behind','smaller','bigger','shorter','taller','standing on','close by','symmetrical to','total']

def make_acc():
    return {k: [] for k in OFF_KEYS}

def summarize(acc):
    out={}
    for k,v in acc.items():
        out[k]={'ok': int(sum(v)), 'total': len(v), 'acc': float(sum(v)/len(v)) if v else None}
    vals=[out[k]['acc'] for k in OFF_KEYS if k!='total' and out[k]['acc'] is not None]
    out['mean_of_means'] = float(sum(vals)/len(vals)) if vals else None
    return out

def eval_dir(pt_dir, layout_json):
    layout=json.load(open(layout_json))
    vocab={'pred_idx_to_name': [p+'\n' for p in PREDICATES]}
    acc=make_acc(); missing=[]; files=0
    for pt in sorted(glob.glob(os.path.join(pt_dir,'*.pt'))):
        d=torch.load(pt, map_location='cpu')
        scan=str(d['scan'])
        if scan not in layout:
            missing.append(scan); continue
        triples=torch.tensor(layout[scan]['triples_s_p_o'], dtype=torch.long)
        boxes=d['boxes'].float()
        acc=validate_constrains(triples, boxes, None, None, vocab, acc, file_dist=None, with_norm=False)
        files += 1
    return {'pt_dir': pt_dir, 'files': files, 'missing': missing, 'official_common_scenes_constraints': summarize(acc)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--layout-json', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('dirs', nargs='+')
    args=ap.parse_args()
    res={os.path.basename(d.rstrip('/')): eval_dir(d, args.layout_json) for d in args.dirs}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(res, open(args.out,'w'), indent=2)
    print(json.dumps(res, indent=2))
if __name__ == '__main__': main()
