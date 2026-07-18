from dataset.threedfront_dataset import ThreedFrontDatasetSceneGraph
root = '/root/autodl-tmp/RelationAwareInstructScene/commonscenes_FRONT'
d = ThreedFrontDatasetSceneGraph(root=root, split='val_scans', eval=True, with_CLIP=False, use_SDF=False, large=False, room_type='bedroom')
print('len', len(d))
print('vocab_objs', len(d.vocab['object_idx_to_name']))
print('vocab_preds', len(d.vocab['pred_idx_to_name']))
item = d[0]
print('item_type', type(item))
print('item_keys', sorted(item.keys()) if hasattr(item, 'keys') else 'no_keys')
