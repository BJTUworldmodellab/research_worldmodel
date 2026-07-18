from pathlib import Path
import pickle
import shutil
import numpy as np

base = Path('/root/RelationAwareInstructScene/repos/InstructScene/dataset/InstructScene')
backup_dir = Path('/root/RelationAwareInstructScene/backups/object_feature_pickles')
backup_dir.mkdir(parents=True, exist_ok=True)

for room in ['bedroom', 'livingroom', 'diningroom']:
    feat_by_id = {}
    for mi_path in (base / f'threed_front_{room}').glob('*/models_info.pkl'):
        npy = mi_path.parent / 'openshape_pointbert_vitg14.npy'
        if not npy.exists():
            continue
        infos = pickle.load(open(mi_path, 'rb'))
        arr = np.load(npy)
        if len(infos) != len(arr):
            raise RuntimeError(f'length mismatch: {mi_path} {len(infos)} vs {len(arr)}')
        for info, feat in zip(infos, arr):
            mid = info.get('model_id')
            if not mid:
                continue
            feat = feat.astype('float32')
            norm = np.linalg.norm(feat)
            if not np.isfinite(norm) or norm == 0:
                raise RuntimeError(f'bad feature norm for {mid} in {mi_path}')
            feat_by_id[mid] = feat / norm

    pkl = base / f'threed_future_model_{room}.pkl'
    backup = backup_dir / f'{pkl.name}.before_openshape_backfill'
    if not backup.exists():
        shutil.copy2(pkl, backup)
    ds = pickle.load(open(pkl, 'rb'))
    objs = getattr(ds, 'objects', ds)
    updated = 0
    missing = []
    for obj in objs:
        mid = getattr(obj, 'model_jid', None)
        feat = feat_by_id.get(mid)
        if feat is None:
            missing.append(mid)
            continue
        setattr(obj, 'openshape_vitg14_features', feat)
        updated += 1
    if missing:
        raise RuntimeError(f'{room}: missing {len(missing)} object features, first={missing[:5]}')
    with open(pkl, 'wb') as f:
        pickle.dump(ds, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f'{room}: updated={updated}, backup={backup}')
