from pathlib import Path
import pickle, shutil
from collections import defaultdict
import numpy as np

base = Path('/root/RelationAwareInstructScene/repos/InstructScene/dataset/InstructScene')
backup_dir = Path('/root/RelationAwareInstructScene/backups/object_size_pickles')
backup_dir.mkdir(parents=True, exist_ok=True)

for room in ['bedroom', 'livingroom', 'diningroom']:
    sizes = defaultdict(list)
    for box_path in (base / f'threed_front_{room}').glob('*/boxes.npz'):
        data = np.load(box_path, allow_pickle=True)
        if 'jids' not in data or 'sizes' not in data:
            continue
        for jid, size in zip(data['jids'], data['sizes']):
            sizes[str(jid)].append(np.asarray(size, dtype='float32'))
    pkl = base / f'threed_future_model_{room}.pkl'
    backup = backup_dir / f'{pkl.name}.before_size_backfill'
    if not backup.exists():
        shutil.copy2(pkl, backup)
    ds = pickle.load(open(pkl, 'rb'))
    objs = getattr(ds, 'objects', ds)
    updated = 0
    missing = []
    for obj in objs:
        jid = str(getattr(obj, 'model_jid', ''))
        vals = sizes.get(jid)
        if not vals:
            missing.append(jid)
            continue
        arr = np.stack(vals, axis=0)
        # Median is robust if the same model appears in multiple scenes.
        obj.__dict__['size'] = np.median(arr, axis=0).astype('float32')
        updated += 1
    if missing:
        raise RuntimeError(f'{room}: missing sizes for {len(missing)} objects, first={missing[:5]}')
    with open(pkl, 'wb') as f:
        pickle.dump(ds, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f'{room}: updated_size_cache={updated}, backup={backup}')
