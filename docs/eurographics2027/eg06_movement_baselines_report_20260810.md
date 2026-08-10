# EG-06 Movement-Matched Baselines Report

Date: 2026-08-10
Task: EG-06 add fair random/generic optimization baselines
Branch: `agent/eg01-eg02-eurographics2027`
Depends on: EG-04 freeze and EG-05 independent evaluator

## Verdict

EG-06 has started. The baseline runner is implemented and validated on a small
fixture with the EG-05 independent evaluator.

It is **not final evidence complete** because the branch still lacks the EG-07
normalized 531-scene layout export. The current result is a runnable fixture
and protocol proof, not the full paper baseline table.

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

## What This Does Not Prove Yet

- It does not prove the main method beats random baselines on the full dataset.
- It does not provide confidence intervals.
- It does not include mesh collision, because the fixture is center/box-only.
- It does not replace EG-07 full rerun or EG-08 statistics.

## Next Step

After EG-07 exports the full normalized layouts, run:

```powershell
& "C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/run_eg06_movement_baselines.py --input <eg07_layout_export.json> --output-dir results/independent_eval/eg2027/<eg06_full_run_id>
```

Then EG-08 should compute paired confidence intervals comparing:

- `collision_gated_floor_prior` vs `baseline`;
- `collision_gated_floor_prior` vs each random seed;
- `collision_gated_floor_prior` vs random-seed mean;
- `collision_gated_floor_prior` vs `generic_relation_optimizer`.
