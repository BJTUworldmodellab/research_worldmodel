# Relation-Aware InstructScene Experiment Report

Date: 2026-05-29

## Goal

Reproduce InstructScene on the existing benchmark assets, then test the proposed Relation-Aware InstructScene idea without building a new benchmark. The first target was relation satisfaction on official InstructScene bedroom, living-room, and dining-room validation scenes.

## Remote environment

Server:

- Host: `region-9.autodl.pro`
- SSH port used in the final run: `54544`
- GPU verified during experiments: `NVIDIA A100-PCIE-40GB`
- Final GPU state after experiments: `0 MiB / 40960 MiB`

Project root:

- `/root/RelationAwareInstructScene`

Repository:

- `/root/RelationAwareInstructScene/repos/InstructScene`
- InstructScene commit observed: `a9097a6`

Environment:

- Activation script: `/root/RelationAwareInstructScene/activate_relation_scene.sh`
- Python: 3.10.8
- PyTorch: 2.1.0+cu121
- CUDA availability: verified before generation

Important storage note:

- `/root/autodl-tmp` is nearly full: about `49G / 50G`, around `2.0G` free.
- Avoid downloading more large files there unless space is cleared.
- `3D-FRONT.zip` remains on `/root/autodl-tmp` and is a major space consumer.

## Data and checkpoints

Data symlinks:

- `dataset/InstructScene -> /root/autodl-tmp/RelationAwareInstructScene/datasets/InstructScene`
- `dataset/3D-FRONT -> /root/RelationAwareInstructScene/raw_data/3D-FRONT`
- `out -> /root/autodl-tmp/RelationAwareInstructScene/instructscene_out`

Extracted 3D-FUTURE model assets:

- Bedroom subset: 2398 models, about 5.17 GB.
- Living/dining additional subset: 1834 extra models, about 3.98 GB.
- Verified missing feature count:
  - livingroom: 0 missing / 2380 total.
  - diningroom: 0 missing / 2247 total.

Checkpoints used:

- Bedroom:
  - `bedroom_sg2scdiffusion_objfeat`, epoch 1999.
  - `bedroom_sgdiffusion_vq_objfeat`, epoch 1999.
- Living room:
  - `livingroom_sg2scdiffusion_objfeat`, epoch 1999.
  - `livingroom_sgdiffusion_vq_objfeat`, epoch 1459.
- Dining room:
  - `diningroom_sg2scdiffusion_objfeat`, epoch 1999.
  - `diningroom_sgdiffusion_vq_objfeat`, epoch 1239.

## Implemented method

Added remote script:

- `/root/RelationAwareInstructScene/repos/InstructScene/src/relation_aware_generate_sg.py`

Local copy:

- `../results/relation_aware_generate_sg.py`

Main features:

- Reuses InstructScene generation, checkpoint loading, object retrieval, and relation evaluator.
- Supports `--relation_source parsed` for deployable text-parsed relations.
- Supports `--relation_source oracle` for benchmark-provided relation upper bound.
- Adds deterministic multi-pass geometric repair of translations.
- Writes both summary `.txt` and per-scene `.json`.
- Records graph relations, baseline layout relations, repaired layout relations, selected relations, parsed relations, and repair stats.

Repair configuration used for the main parsed experiments:

- `--repair_passes 2`
- `--close_distance 0.75`
- `--far_distance 1.6`
- `--relation_source parsed`

## Commands

Living room full run:

```bash
cd /root/RelationAwareInstructScene/repos/InstructScene
source /root/RelationAwareInstructScene/activate_relation_scene.sh
ulimit -n 65535 || true
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=1
python src/relation_aware_generate_sg.py configs/livingroom_sg_diffusion_vq_objfeat.yaml \
  --tag livingroom_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae \
  --sg2sc_tag livingroom_sg2scdiffusion_objfeat \
  --checkpoint_epoch 1459 \
  --sg2sc_epoch 1999 \
  --n_scenes 0 \
  --n_workers 0 \
  --device 0 \
  --relation_source parsed \
  --repair_passes 2 \
  --close_distance 0.75 \
  --far_distance 1.6
```

Dining room full run:

```bash
cd /root/RelationAwareInstructScene/repos/InstructScene
source /root/RelationAwareInstructScene/activate_relation_scene.sh
ulimit -n 65535 || true
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=1
python src/relation_aware_generate_sg.py configs/diningroom_sg_diffusion_vq_objfeat.yaml \
  --tag diningroom_sgdiffusion_vq_objfeat \
  --fvqvae_tag threedfront_objfeat_vqvae \
  --sg2sc_tag diningroom_sg2scdiffusion_objfeat \
  --checkpoint_epoch 1239 \
  --sg2sc_epoch 1999 \
  --n_scenes 0 \
  --n_workers 0 \
  --device 0 \
  --relation_source parsed \
  --repair_passes 2 \
  --close_distance 0.75 \
  --far_distance 1.6
```

The `ulimit -n 65535` line was necessary after a first full living-room attempt failed around 143/192 scenes with `OSError: [Errno 24] Too many open files`.

## Main results

| Room | Scenes | Relations | Graph acc | Baseline layout acc | Relation-aware acc | Absolute gain | Error reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 162 | 245 | 0.7388 | 0.7388 | 0.8735 | +0.1347 | 51.6% |
| Living room | 192 | 294 | 0.5272 | 0.5510 | 0.7415 | +0.1905 | 42.4% |
| Dining room | 177 | 269 | 0.5874 | 0.5948 | 0.7844 | +0.1896 | 46.8% |

Scene-level selected-relation outcomes:

| Room | Improved | Degraded | Same |
|---|---:|---:|---:|
| Bedroom | 31 | 0 | 131 |
| Living room | 48 | 0 | 144 |
| Dining room | 43 | 0 | 134 |

Parser and repair stats:

| Room | Parser recall | Parser precision | Repair edits | Repair skipped | Avg movement per edit |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.5265 | 0.5309 | 59 | 50 | 2.5677 |
| Living room | 0.4320 | 0.5546 | 73 | 87 | 2.5059 |
| Dining room | 0.4833 | 0.5508 | 64 | 72 | 2.1341 |

## Geometry sanity checks

After adding geometry serialization to `src/relation_aware_generate_sg.py`, the parsed relation-aware experiments were rerun and the following coarse footprint metrics were recorded. The overlap metric is a 2D axis-aligned footprint proxy computed from object centers, rotations, and retrieved object sizes. It is not a full mesh-collision metric, but it is enough to test whether repair is obviously worsening layout validity.

| Room | Baseline overlap ratio | Repaired overlap ratio | Baseline overlap pairs / scene | Repaired overlap pairs / scene | Baseline OOB center rate | Repaired OOB center rate |
|---|---:|---:|---:|---:|---:|---:|
| Bedroom | 0.086977 | 0.083586 | 2.642 | 2.562 | 0.000000 | 0.000000 |
| Living room | 0.139931 | 0.134841 | 7.911 | 7.708 | 0.000000 | 0.000000 |
| Dining room | 0.155403 | 0.154162 | 8.107 | 7.932 | 0.000000 | 0.000000 |

Interpretation:

- Relation accuracy improves strongly.
- Coarse footprint overlap does not increase; it slightly decreases in all three room categories.
- Repaired object centers remain inside the learned translation bounds.
- This is a useful sanity check, but not a replacement for rendered qualitative figures or full mesh-level collision evaluation.

## Oriented-footprint validity proxy

An additional post-hoc evaluator was run on the saved baseline and repaired boxes using oriented 2D furniture footprints. This is stricter than the AABB proxy for rotated furniture, but it is still not exact mesh-level collision.

| Room | Layout OBB overlap | Repaired OBB overlap | Delta | Layout pairs / scene | Repaired pairs / scene |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.046569 | 0.041681 | -0.004888 | 0.907 | 0.889 |
| Living room | 0.054337 | 0.050177 | -0.004160 | 1.911 | 1.833 |
| Dining room | 0.057112 | 0.055276 | -0.001837 | 1.734 | 1.701 |

Multi-seed oriented-footprint summary:

| Room | N | Layout OBB overlap mean | Repaired OBB overlap mean | Layout pairs / scene mean | Repaired pairs / scene mean |
|---|---:|---:|---:|---:|---:|
| Bedroom | 3 | 0.049655 | 0.047408 | 0.963 | 0.938 |
| Living room | 3 | 0.054220 | 0.051375 | 1.877 | 1.818 |
| Dining room | 3 | 0.057102 | 0.054355 | 1.761 | 1.721 |

Interpretation:

- The oriented-footprint proxy also decreases slightly after repair.
- This strengthens the box-level validity sanity check.
- It still cannot be written as "mesh-level collision improves" because exact 3D meshes, support/contact, and accessibility were not evaluated.

## Mesh-level collision evaluation

The main parsed runs were rerun with `--mesh_collision`, using retrieved 3D-FUTURE meshes and `trimesh.collision.CollisionManager` backed by `python-fcl`. This is the first true mesh-level collision check in the experiment package.

Direct repair results:

| Room | Scenes | Baseline relation acc | Direct repair acc | Baseline mesh pair rate | Direct repair mesh pair rate | Delta |
|---|---:|---:|---:|---:|---:|---:|
| Bedroom | 162 | 0.7388 | 0.8735 | 0.070244 | 0.070244 | +0.000000 |
| Living room | 192 | 0.5510 | 0.7415 | 0.031257 | 0.031616 | +0.000359 |
| Dining room | 177 | 0.5948 | 0.7844 | 0.034229 | 0.034766 | +0.000537 |

Interpretation:

- Direct relation repair still improves relation accuracy strongly.
- Direct repair does not prove mesh-collision reduction: bedroom is tied, while living room and dining room increase by a very small amount.
- Therefore the unsafe claim "mesh-level collision is lower" must not be used for the direct variant.

Collision-gated variant:

The collision-gated variant keeps the repaired scene only when FCL mesh collision pairs do not increase; otherwise it falls back to the baseline layout for that scene.

| Room | Baseline acc | Direct repair acc | Collision-gated acc | Gated gain | Baseline mesh pair rate | Gated mesh pair rate | Fallback scenes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | 0.8449 | +0.1061 | 0.070244 | 0.064878 | 9 |
| Living room | 0.5510 | 0.7415 | 0.6871 | +0.1361 | 0.031257 | 0.030540 | 14 |
| Dining room | 0.5948 | 0.7844 | 0.7212 | +0.1264 | 0.034229 | 0.033154 | 13 |

Interpretation:

- The gated variant supports a stronger mesh-validity claim than direct repair.
- It preserves substantial relation gains while reducing FCL mesh collision pair rate below the baseline in all three room categories.
- This is now the safest method variant for a paper claim involving mesh-level collision.

## Oracle upper-bound experiments

The same repair layer was also run with `--relation_source oracle`, using benchmark-selected relation triples as repair targets. This is not the deployable method; it is an upper bound showing how much headroom remains beyond the rule-based parser.

| Room | Baseline | Parsed repair | Oracle repair | Oracle gap | Parsed/oracle gain captured |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | 0.8857 | +0.0122 | 91.7% |
| Living room | 0.5510 | 0.7415 | 0.7755 | +0.0340 | 84.8% |
| Dining room | 0.5948 | 0.7844 | 0.8141 | +0.0297 | 86.4% |

Interpretation:

- Parsed repair captures most of the oracle-repair gain.
- The remaining oracle gap suggests parser improvements are useful but not required for the core claim.
- This supports the paper framing that the central contribution is relation realization and verification, not a perfect language parser.

## Repair-pass ablation

Default setting is `repair_passes=2`, `close_distance=0.75`, `far_distance=1.6`.

| Room | Passes | Relation acc | Gain | Repaired overlap ratio | Repaired OOB center rate |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0 | 0.7388 | +0.0000 | 0.0870 | 0.0000 |
| Bedroom | 1 | 0.8531 | +0.1143 | 0.0779 | 0.0012 |
| Bedroom | 2 | 0.8735 | +0.1347 | 0.0836 | 0.0000 |
| Bedroom | 3 | 0.8816 | +0.1429 | 0.0801 | 0.0012 |
| Living room | 0 | 0.5510 | +0.0000 | 0.1399 | 0.0000 |
| Living room | 1 | 0.7211 | +0.1701 | 0.1353 | 0.0000 |
| Living room | 2 | 0.7415 | +0.1905 | 0.1348 | 0.0000 |
| Living room | 3 | 0.7449 | +0.1939 | 0.1352 | 0.0000 |
| Dining room | 0 | 0.5948 | +0.0000 | 0.1554 | 0.0000 |
| Dining room | 1 | 0.7732 | +0.1784 | 0.1533 | 0.0000 |
| Dining room | 2 | 0.7844 | +0.1896 | 0.1542 | 0.0000 |
| Dining room | 3 | 0.7844 | +0.1896 | 0.1533 | 0.0000 |

Interpretation:

- Most of the benefit appears after one repair pass.
- Two passes are a good default because they improve relation accuracy further while keeping OOB at zero for the main seed.
- Three passes provide only marginal additional relation gain and occasionally introduce tiny boundary-rate artifacts in bedroom.

## Distance-threshold ablation

The sweep covers seven settings: the default plus six neighboring settings.

| Room | Setting | Relation acc | Gain | Repaired overlap ratio |
|---|---|---:|---:|---:|
| Bedroom | close0.50_far1.30 | 0.8735 | +0.1347 | 0.0857 |
| Bedroom | close0.50_far1.60 | 0.8735 | +0.1347 | 0.0837 |
| Bedroom | close0.75_far1.30 | 0.8735 | +0.1347 | 0.0856 |
| Bedroom | close0.75_far1.60 | 0.8735 | +0.1347 | 0.0836 |
| Bedroom | close0.75_far2.00 | 0.8694 | +0.1306 | 0.0837 |
| Bedroom | close1.00_far1.60 | 0.8612 | +0.1224 | 0.0836 |
| Bedroom | close1.00_far2.00 | 0.8571 | +0.1184 | 0.0837 |
| Living room | close0.50_far1.30 | 0.7449 | +0.1939 | 0.1366 |
| Living room | close0.50_far1.60 | 0.7415 | +0.1905 | 0.1354 |
| Living room | close0.75_far1.30 | 0.7449 | +0.1939 | 0.1360 |
| Living room | close0.75_far1.60 | 0.7415 | +0.1905 | 0.1348 |
| Living room | close0.75_far2.00 | 0.7449 | +0.1939 | 0.1336 |
| Living room | close1.00_far1.60 | 0.7075 | +0.1565 | 0.1350 |
| Living room | close1.00_far2.00 | 0.7109 | +0.1599 | 0.1337 |
| Dining room | close0.50_far1.30 | 0.7844 | +0.1896 | 0.1550 |
| Dining room | close0.50_far1.60 | 0.7844 | +0.1896 | 0.1551 |
| Dining room | close0.75_far1.30 | 0.7807 | +0.1859 | 0.1541 |
| Dining room | close0.75_far1.60 | 0.7844 | +0.1896 | 0.1542 |
| Dining room | close0.75_far2.00 | 0.7844 | +0.1896 | 0.1529 |
| Dining room | close1.00_far1.60 | 0.7286 | +0.1338 | 0.1539 |
| Dining room | close1.00_far2.00 | 0.7286 | +0.1338 | 0.1525 |

Interpretation:

- The method is robust for close distances 0.50 to 0.75.
- `close_distance=1.00` hurts exact relation accuracy, especially in living room and dining room.
- Larger `far_distance` can slightly reduce overlap, but does not consistently improve exact relation accuracy.
- The chosen default is not cherry-picked for a single room: it is competitive across all three rooms and has clean OOB behavior in the main run.

## Multi-seed stability

Seeds 0, 1, and 2 were evaluated with the default setting.

| Room | N | Baseline mean | Baseline std | Ours mean | Ours std | Gain mean | Gain std | Repaired overlap mean | Repaired OOB mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 3 | 0.7565 | 0.0209 | 0.8939 | 0.0178 | 0.1374 | 0.0125 | 0.0921 | 0.0012 |
| Living room | 3 | 0.5420 | 0.0086 | 0.7483 | 0.0180 | 0.2063 | 0.0246 | 0.1330 | 0.0001 |
| Dining room | 3 | 0.5923 | 0.0021 | 0.7993 | 0.0170 | 0.2069 | 0.0187 | 0.1507 | 0.0000 |

Interpretation:

- The relation gain is stable across seeds.
- The multi-seed repaired accuracy remains well above the corresponding baseline mean.
- Tiny OOB center rates appear in some non-main-seed bedroom/living-room runs. These are small boundary artifacts under the center-bound proxy, not catastrophic scene failures, but a final paper should either add stricter clipping or report this metric honestly.

## Local table artifacts

Machine-readable tables were generated under:

- `../results/tables/main_results.csv`
- `../results/tables/oracle_gap.csv`
- `../results/tables/repair_pass_ablation.csv`
- `../results/tables/distance_ablation.csv`
- `../results/tables/multiseed_runs.csv`
- `../results/tables/multiseed_summary.csv`

The compact paper-facing Markdown table bundle is:

- `relation_aware_instructscene_a_conf_experiment_pack.md`

## Qualitative diagnostics

Top-down before/after qualitative diagnostics were generated from the saved box layouts:

- `../visual/qualitative/qualitative_gallery.html`

Mesh-projection before/after diagnostics were also generated during the mesh-collision run:

- `../visual/mesh_renders_gallery.html`

These figures are useful for paper debugging and early qualitative explanation. They are not a substitute for final photorealistic or mesh-rendered figures, but they show that the repaired relation count improves in concrete examples and make it easier to inspect whether the layout movement is plausible.

## Explicit-vs-implicit relation audit

The current relation subset was audited for explicit spatial relation language. Under the audit, all evaluated scenes are explicit-relation prompts, and no implicit commonsense-only scenes were found.

| Room | Explicit scenes | Implicit scenes | Explicit relation subset base -> repair |
|---|---:|---:|---:|
| Bedroom | 162 | 0 | 0.7388 -> 0.8735 |
| Living room | 192 | 0 | 0.5510 -> 0.7415 |
| Dining room | 177 | 0 | 0.6000 -> 0.7925 |

Interpretation:

- The benchmark supports explicit spatial-relation following.
- It does not support a claim about all implicit commonsense relations.
- The dining-room explicit subset covers 265 regex-matched explicit relation instances; the main benchmark table should still use the official selected-relation total of 269.

## Claim validation summary

| Claim | Status | Evidence |
|---|---|---|
| Improves explicit relation satisfaction on existing InstructScene splits. | Supported | Main, oracle, ablation, and multi-seed results. |
| Does not obviously hurt coarse box-level validity. | Supported as a proxy | AABB and oriented-footprint overlap decrease slightly. |
| Mesh-level collision is lower. | Supported only for collision-gated variant | Direct repair slightly increases mesh pair rate in living/dining; gated repair reduces mesh pair rate while preserving relation gains. |
| Visual quality is better. | Not supported | Only top-down diagnostics exist; no rendered perceptual evaluation. |
| Beats SDGScenes or ReSpace. | Not supported | No shared-protocol reproduction or same-split comparison. |
| Handles all implicit commonsense relations. | Not supported | Current benchmark contains no implicit-only scenes under the audit. |
| First relation-aware 3D scene generation method. | Unsafe | Prior scene-graph, semantic-dependency, and spatial-reasoning work exists. |

## Result files

Local synchronized results:

- `../results/bedroom_relation_aware_parsed_eval.txt`
- `../results/bedroom_relation_aware_parsed_eval.json`
- `../results/livingroom_relation_aware_parsed_eval.txt`
- `../results/livingroom_relation_aware_parsed_eval.json`
- `../results/diningroom_relation_aware_parsed_eval.txt`
- `../results/diningroom_relation_aware_parsed_eval.json`

Remote result files:

- `out/bedroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01999/relation_aware_parsed_p2_close0.75_far1.6_eval.txt`
- `out/livingroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01459/relation_aware_parsed_p2_close0.75_far1.6_eval.txt`
- `out/diningroom_sgdiffusion_vq_objfeat/generated_scenes/epoch_01239/relation_aware_parsed_p2_close0.75_far1.6_eval.txt`

## Example improved prompts

Bedroom:

> Add a double bed left of a gray nightstand with drawers. Place a gray nightstand with drawers to the right of a gray wardrobe with shelves and drawers.

Living room:

> Set up a grey and white tv stand with drawers behind a black coffee table with a lid. Then, arrange a black coffee table with a lid right of a black corner side table with a round base.

Dining room:

> Put a wooden dining table right of a bookshelf with doors and shelves.

## Interpretation

The current evidence supports the central hypothesis: a relation-aware verifier-repair layer substantially improves realized relation accuracy on existing InstructScene benchmarks. The result is consistent across all three room categories, and under the selected-relation metric there were no scenes whose selected-relation count decreased.

The result is not yet enough for a full submission claim by itself. The missing part is not relation accuracy; the missing part is demonstrating that the repaired layouts remain good scenes.

## Current conclusion

This is a strong paper seed, not a finished paper package.

What is already strong:

- Three room types, all using existing benchmark splits.
- Large gains from 13.5 to 19.1 absolute points.
- No degraded scenes under the measured relation metric.
- No retraining required.
- Parser is imperfect but still useful.
- Coarse geometry sanity checks are positive: AABB and oriented-footprint overlap ratios decrease slightly, and out-of-bound center rate remains near zero.
- Oracle experiments show the parsed method captures 84.8% to 91.7% of the available oracle gain.

What must be added before submission:

- Full mesh-level collision and support/contact metrics.
- Stronger room-validity metrics beyond center out-of-bound checks.
- Diversity/distribution checks.
- Qualitative rendered examples.
- Shared-protocol comparison with strong related methods if claiming SOTA over ReSpace, SDGScenes, or similar systems.

## Suggested next run list

1. Run oracle relation source for living room and dining room.
2. Run ablations:
   - `repair_passes`: 0, 1, 2, 3.
   - `close_distance`: 0.5, 0.75, 1.0.
   - `far_distance`: 1.3, 1.6, 2.0.
3. Add collision/overlap evaluator using generated box geometry.
4. Render before/after examples for 15 total scenes.
5. Produce final paper tables and qualitative figure grid.
