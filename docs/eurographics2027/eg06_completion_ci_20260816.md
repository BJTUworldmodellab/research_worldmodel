# EG-06 Completion Check With Paired Bootstrap CI

Date: 2026-08-16
Branch snapshot: `agent/eg01-eg02-eurographics2027`
Commit checked: `5c6f059`
Input package: `eg07_final_delivery_20260814`

## Verdict

EG-06 is complete for the fair movement-matched random baseline claim.

It is not complete for a stronger claim that the main method beats the generic
relation optimizer. The generic optimizer has a slightly higher point estimate,
and the paired CI crosses zero.

## Evidence Inputs

- Full layout package: `eg07_final_delivery_20260814/layouts/layouts.json`
- Layout SHA-256:
  `663ce5ff76698358c47e9542563bd01a788bc90efb9f299e7c261da2399e281d`
- EG-06 per-scene table: `eg07_final_delivery_20260814/eg06/per_scene.csv`
- EG-06 per-relation table: `eg07_final_delivery_20260814/eg06/per_relation.csv`
- EG-06 movement audit: `eg07_final_delivery_20260814/eg06/movement_audit.csv`

## Structural Completion

| Check | Result |
|---|---:|
| Scenes | 531 |
| EG-06 movement audit rows | 2655 |
| Expected rows, 531 scenes x 5 movement variants | 2655 |
| Random seeds | 0, 1, 2 |
| Random exact movement matched | PASS |
| Generic optimizer within movement budget | PASS |

## Overall Relation Accuracy

| Variant | Accuracy |
|---|---:|
| baseline | 0.634901 |
| collision_gated_floor_prior | 0.639851 |
| random_movement_matched_seed0 | 0.622525 |
| random_movement_matched_seed1 | 0.625000 |
| random_movement_matched_seed2 | 0.628713 |
| random mean | 0.625413 |
| generic_relation_optimizer | 0.641089 |

## Paired Bootstrap CI

Bootstrap used 10,000 scene-level resamples with seed `20260816`.

Two paired estimates are reported:

- `scene_unweighted`: mean of per-scene relation-accuracy differences.
- `relation_weighted`: scene bootstrap of total satisfied-relation differences
  divided by total target relations in the sampled scenes.

Positive values mean the main method is better than the comparison variant.

| Comparison | Scene-unweighted diff | Scene-unweighted 95% CI | Relation-weighted diff | Relation-weighted 95% CI |
|---|---:|---:|---:|---:|
| main - baseline | +0.004708 | [-0.000942, +0.011299] | +0.004950 | [-0.001252, +0.012226] |
| main - random seed0 | +0.015066 | [+0.006591, +0.024482] | +0.017327 | [+0.007547, +0.028290] |
| main - random seed1 | +0.014124 | [+0.005650, +0.024482] | +0.014851 | [+0.006127, +0.024969] |
| main - random seed2 | +0.011299 | [+0.003766, +0.019774] | +0.011139 | [+0.003690, +0.019633] |
| main - random mean | +0.013497 | [+0.006905, +0.020716] | +0.014439 | [+0.007453, +0.022005] |
| main - generic optimizer | -0.001883 | [-0.007533, +0.002825] | -0.001238 | [-0.006329, +0.003759] |

## Claim Status

Safe paper claim:

> Collision-gated Floor-Prior outperforms exact movement-matched random
> baselines on the 531-scene formal candidate under the EG-05 independent
> evaluator.

Do not claim:

> Collision-gated Floor-Prior outperforms the generic relation optimizer.

The generic optimizer is 518/808 satisfied relations, while the main method is
517/808. Its paired CI also crosses zero, so this comparison should be reported
as not beaten / inconclusive.

## Remaining Boundary

EG-06 can be marked complete if its acceptance target is the random movement
baseline. If the project defines EG-06 as requiring superiority over the generic
optimizer too, then EG-06 remains partially complete and the main paper claim
must be narrowed.
