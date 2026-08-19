# EG-06 Movement-Matched Baselines Report

Date: 2026-08-10
Task: EG-06 add fair random/generic optimization baselines
Branch: `agent/eg01-eg02-eurographics2027`
Depends on: EG-04 freeze and EG-05 independent evaluator

## Verdict

EG-06 is now full-run complete on the EG-07 formal evidence package. The
baseline runner is implemented, fixture-validated, and run on the same 531-scene
layout export used by EG-05.

It is evidence-gate complete for point estimates and fairness checks. It is
**not a final paper claim of statistical significance** because paired
confidence intervals are deferred to EG-08.

Persuasiveness audit:

`docs/eurographics2027/eg06_persuasiveness_audit_20260810.md`

## Implemented Runner

Script:

`scripts/run_eg06_movement_baselines.py`

Input:

An evaluator-layout JSON containing paired `baseline` and
`collision_gated_floor_prior` layouts for each scene.

Output:

- `eg06_augmented_layouts.json`
- `movement_audit.csv`
- `per_relation.csv`
- `per_scene.csv`
- `summary.csv`
- `audit.json`

## Baselines

| Baseline | What it does | Fairness rule |
|---|---|---|
| `random_movement_matched_seed0/1/2` | Moves the same objects by the same XZ distance as the frozen main method, but in random directions. | Exact per-object XZ movement magnitude match. |
| `generic_relation_optimizer` | Applies a simple relation-directed correction without using Floor-Prior candidate scoring or collision gate logic. | Uses the same per-object movement budget as an upper bound; actual movement may be smaller if the relation is satisfied earlier. |

The generic optimizer is therefore **budget-matched**, not exact-distance
matched. The random baselines are the exact movement-matched controls.

## Fixture Run

Input fixture:

`evaluation/fixtures/eg06_movement_baseline_fixture.json`

Command:

```powershell
& "C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/run_eg06_movement_baselines.py
```

Output directory:

`results/independent_eval/eg2027/eg06_movement_baseline_fixture`

## Fixture Summary

The fixture has one simple relation in each room type. This is only a smoke
test showing that baseline generation and evaluator integration work.

| Variant | Bedroom | Living room | Dining room |
|---|---:|---:|---:|
| baseline | 0.0 | 0.0 | 0.0 |
| collision_gated_floor_prior | 1.0 | 1.0 | 1.0 |
| generic_relation_optimizer | 1.0 | 1.0 | 1.0 |
| random_movement_matched_seed0 | 0.0 | 0.0 | 0.0 |
| random_movement_matched_seed1 | 0.0 | 0.0 | 0.0 |
| random_movement_matched_seed2 | 0.0 | 0.0 | 0.0 |

## Movement Audit

The movement audit confirms that random baselines match the frozen main method's
per-object movement magnitude on the fixture:

| Scene | Main budget | Random seeds | Generic optimizer |
|---|---:|---:|---:|
| `eg06_bedroom_001` | 0.45 | 0.45 / 0.45 / 0.45 | 0.275 |
| `eg06_livingroom_001` | 0.55 | 0.55 / 0.55 / 0.55 | 0.50 |
| `eg06_diningroom_001` | 0.40 | 0.40 / 0.40 / 0.40 | 0.275 |

## EG-07 Full Movement-Baseline Run

Source package:

`eg07_final_delivery_20260814/`

Input layout export:

`eg07_final_delivery_20260814/layouts/layouts.json`

Input SHA-256:

`663ce5ff76698358c47e9542563bd01a788bc90efb9f299e7c261da2399e281d`

Full-run outputs:

- `eg07_final_delivery_20260814/eg06/eg06_augmented_layouts.json`
- `eg07_final_delivery_20260814/eg06/movement_audit.csv`
- `eg07_final_delivery_20260814/eg06/per_relation.csv`
- `eg07_final_delivery_20260814/eg06/per_scene.csv`
- `eg07_final_delivery_20260814/eg06/summary.csv`
- `eg07_final_delivery_20260814/eg06/audit.json`

Audit status:

| Check | Value |
|---|---:|
| Run scope | full |
| Input scenes | 531 |
| Random seeds | 0, 1, 2 |
| Movement-audit rows | 2655 |
| Random exact movement match | true |
| Generic optimizer within budget | true |
| Missing baseline scenes | 0 |

Full-run relation accuracy:

| Variant | Overall accuracy | Satisfied / total | Relation to main |
|---|---:|---:|---:|
| Collision-gated Floor-Prior | 0.6399 | 517 / 808 | Reference |
| InstructScene baseline | 0.6349 | 513 / 808 | -0.50 pp vs main |
| Random movement matched, seed 0 | 0.6225 | 503 / 808 | -1.73 pp vs main |
| Random movement matched, seed 1 | 0.6250 | 505 / 808 | -1.49 pp vs main |
| Random movement matched, seed 2 | 0.6287 | 508 / 808 | -1.11 pp vs main |
| Random movement matched, mean | 0.6254 | about 505.3 / 808 | -1.44 pp vs main |
| Generic relation optimizer | 0.6411 | 518 / 808 | +0.12 pp vs main |

Interpretation:

- The main method is above all three random movement-matched baselines.
- The main method is slightly above the original InstructScene baseline.
- The generic relation optimizer is 1 satisfied relation higher than the main
  method, so EG-06 does **not** support claiming that the main method beats the
  generic optimizer.
- The main method still has a useful safety point: chosen-main mesh collision
  pairs are 1061, lower than the baseline count of 1075.

## What This Does Not Prove Yet

- It does not prove the main method is statistically significantly above random
  baselines until EG-08 computes paired confidence intervals.
- It does not prove the main method beats a generic optimizer; the generic
  optimizer is 518/808 while the main method is 517/808.
- It does not provide confidence intervals.
- It supports "mesh collision non-worsening" at the chosen-main aggregate level,
  not a broad claim that every physical-quality metric improves.
- It does not replace EG-08 statistics.

## Next Step

EG-08 should compute paired confidence intervals comparing:

- `collision_gated_floor_prior` vs `baseline`;
- `collision_gated_floor_prior` vs each random seed;
- `collision_gated_floor_prior` vs random-seed mean;
- `collision_gated_floor_prior` vs `generic_relation_optimizer`.

The paper table should separate "relation accuracy" from "mesh collision
non-worsening" instead of treating them as one combined win.
