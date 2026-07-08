# Floor-Plane Repair Fix

## Problem

Visual inspection of the real 3D-FUTURE mesh renders exposed a method bug: the relation repair sometimes copied the reference object's vertical coordinate into the moved object. This made floor-standing objects appear to float or sink when the reference object was a pendant lamp, cabinet, or another object with a different height.

Concrete examples from the curated showcase before the fix:

| Room | Object | Old repaired bottom | Fixed bottom | Cause |
| --- | ---: | ---: | ---: | --- |
| bedroom #145 | class 20 | -0.372 | -0.013 | moved object inherited a nightstand height |
| livingroom #159 | class 16 sofa | 1.684 | -0.001 | sofa inherited pendant-lamp height |
| diningroom #136 | class 11 table | 0.367 | 0.011 | table inherited cabinet height |

## Fix

The repair is now constrained to the floor plane:

- Pair selection uses x/z distance rather than full 3D distance.
- `clamp_pair_translation` changes only x/z. In this codebase `y` is vertical height, while `z` is floor-plane depth.
- Each object's original y coordinate is preserved.
- Reported repair movement is measured in x/z only.
- The paper-facing `floor_prior` variant still allows z/depth changes, but only within a bounded reasonable range via `--max_repair_move`.

This keeps the paper story aligned with the method: Relation-Aware InstructScene repairs horizontal spatial relations, not vertical support/contact relations.

The intended constraint is therefore:

```text
allowed:   small bounded x/z floor-plane movement
forbidden: changing y height or lifting/sinking furniture
```

## Verification

- Remote source patched at `/root/RelationAwareInstructScene/repos/InstructScene/src/relation_aware_generate_sg.py`.
- Syntax check passed with `python -m py_compile src/relation_aware_generate_sg.py`.
- Minimal remote unit check confirmed subject/object y coordinates remain unchanged after repair.
- New qualitative renders are under `visual/real_mesh_showcase_v3/`.
- The local showcase page now points to v3 assets: `visual/real_mesh_showcase.html`.

## Paper Impact

Previous relation-accuracy numbers are still useful for directionality, but paper-facing mesh-collision and qualitative claims should be recomputed with the floor-plane repair source before final submission. The previous direct-repair mesh-collision table used the height-changing variant and should not be treated as final.
