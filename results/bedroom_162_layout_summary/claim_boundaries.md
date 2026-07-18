# Claim Boundaries
**Generated**: 2026-07-08

## What This Work Evaluates

- **Layout-level**: bbox-only validation using official InstructScene model outputs (translation, size, angle).
- **SG-layout consistency**: Measures whether the generated bbox layout satisfies its own generated scene graph spatial relations, computed via `compute_loc_rel` (angle-based horizontal + polygon-based vertical).
- **Layout overlap**: Ground-plane (XZ) oriented bbox polygon IoU via shapely. Only active objects considered.
- **Repair**: Iterative overlap-reduction push in XZ, guarded by per-scene SG consistency baseline.

## What This Work Does NOT Evaluate

- **Mesh collision**: Not 3D collision detection. Overlap is 2D ground-plane IoU of oriented bounding boxes.
- **Rendering quality**: No Blender rendering; visual quality not assessed.
- **Furniture retrieval**: No trimesh mesh retrieval or OpenShape similarity ranking.
- **SOTA comparison**: Not directly comparable to ReSpace, SDGScenes, or other layout synthesis methods without equivalent bbox-level baselines.
- **Relation accuracy (official)**: The metric is named SG-layout consistency, not relation accuracy, because exported .npz files contain NO ground-truth relations. The metric compares generated bbox positions against generated scene graph edges — this is a self-consistency check, not accuracy against human annotations or GT scene graphs.
- **Room out-of-bounds**: Room OOB is reported as NA — no room geometry (floor_plan, room_mask, room_bounds) is present in the export.
- **Multi-room-type**: Bedroom only. Dining room and living room not yet evaluated.

## Metric Naming Conventions

| Metric Name | Meaning | Caveat |
|-------------|---------|--------|
| SG-layout consistency | Fraction of generated scene graph edges whose spatial relation matches the geometric bbox relation | Self-consistency, not GT accuracy |
| Layout overlap IoU sum | Sum of pairwise ground-plane XZ oriented-bbox IoU | 2D only, not 3D collision |
| Overlap reduction % | (baseline - repaired) / baseline × 100 | Higher is better |
| Movement (m) | Euclidean displacement in XZ plane | Does not include Y or rotation changes |
| Worse-overlap scenes | Scenes where repaired overlap_iou_sum > baseline + 1e-6 | Zero by guarantee design |

## Scope

- **Room type**: Bedroom (threed_front_bedroom), 162 validation scenes
- **Checkpoints**: Official InstructScene epoch 1999 (fVQ-VAE, SG Prior, SG2SC)
- **Seed**: 42
- **Device**: Single NVIDIA RTX 4090
