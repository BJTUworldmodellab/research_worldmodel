# EG-05 Independent Evaluator Report

Date: 2026-08-05
Task: EG-05 implement and validate independent evaluator
Branch: `agent/eg01-eg02-eurographics2027`
Depends on: EG-02 protocol and EG-04 method freeze

## Verdict

EG-05 implementation is usable for the current Eurographics branch. The
independent evaluator is available as a runnable module with unit tests, a smoke
fixture, per-scene CSV output, an audit JSON, and a repair-coordinate alignment
against the adjudicated EG-02 human subset.

It is **not yet final evidence-gate complete** because the evaluator has not
been run against a normalized full EG-07 layout export. The human subset check
has been completed for repair coordinates.

## Implemented Evaluator

Path:

`evaluation/independent_relation_evaluator.py`

Protocol version:

`eg2027-eg05-v1`

EG-05 fixes a coordinate-convention inconsistency in the older EG-02 draft:
the evaluator now follows the adjudicated human-review table convention
`behind dz<0` and `in_front_of dz>0`.

The evaluator does not import repair, verifier, candidate-scoring, or fallback
code from the optimizer.

Output:

```text
per_relation.csv
per_scene.csv
summary.csv
audit.json
```

## Independence Controls

| Control | Status |
|---|---|
| Does not import `scripts/compute_gated_floorprior.py` | PASS |
| Does not import `scripts/summarize_floorprior_results.py` | PASS |
| Does not import `scripts/sync_parallel_floorprior_results.py` | PASS |
| Does not import optimizer repair modules | PASS |
| Reads only final layout objects and target relations | PASS |
| Uses baseline layout to freeze instance pairs before evaluating variants | PASS |

## Unit Test Coverage

Command:

```powershell
& "C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -p "test_independent_relation_evaluator.py" -v
```

Result:

```text
Ran 4 tests
OK
```

Covered cases:

| Requirement | Covered by test/smoke? | Notes |
|---|---|---|
| Boundary distance threshold | Yes | `dx=0.04` fails left/right with `direction_margin=0.05`. |
| Rotation object input | Yes | Objects include yaw; evaluator reads final centers and tolerates yaw. |
| Missing object | Yes | Missing subject remains in denominator as `missing_subject`. |
| Repeated instances | Yes | Baseline chooses nearest XZ pair and reuses the same indices for repair. |
| Conflict relation handling | Yes | Same pair with left/right conflict sets `has_conflicting_targets=1`. |
| Unsupported predicate | Yes | Marked as `unsupported_predicate`, not dropped. |
| EG-02 front/behind coordinate convention | Yes | `behind dz<0`, `in_front_of dz>0`. |
| Deterministic CLI output | Yes | Smoke fixture writes all four expected files. |

## Smoke Output

Input fixture:

`evaluation/fixtures/eg05_smoke_layouts.json`

Generated files:

- `results/independent_eval/eg2027/eg05_smoke_fixture/per_relation.csv`
- `results/independent_eval/eg2027/eg05_smoke_fixture/per_scene.csv`
- `results/independent_eval/eg2027/eg05_smoke_fixture/summary.csv`
- `results/independent_eval/eg2027/eg05_smoke_fixture/audit.json`

## Human-Subset Alignment

Script:

`scripts/run_eg05_human_subset_alignment.py`

Source labels:

`results/eurographics2027/eg02_human_review_v2_final/final_labels.csv`

Generated files:

- `results/independent_eval/eg2027/eg05_human_subset_repair/human_subset_repair_layouts.json`
- `results/independent_eval/eg2027/eg05_human_subset_repair/per_relation.csv`
- `results/independent_eval/eg2027/eg05_human_subset_repair/per_scene.csv`
- `results/independent_eval/eg2027/eg05_human_subset_repair/summary.csv`
- `results/independent_eval/eg2027/eg05_human_subset_repair/audit.json`
- `results/independent_eval/eg2027/eg05_human_subset_repair/human_alignment.csv`
- `results/independent_eval/eg2027/eg05_human_subset_repair/human_alignment_summary.json`

Human-subset result:

| Metric | Value |
|---|---:|
| Source human rows | 90 |
| Converted repair-coordinate rows | 84 |
| Skipped missing pair/center rows | 6 |
| Binary-evaluable rows | 79 |
| Accuracy vs adjudicated human labels | 0.822785 |
| Precision satisfied | 0.896552 |
| Recall satisfied | 0.866667 |
| Specificity not satisfied | 0.684211 |

## Current Status

| Item | Status |
|---|---|
| EG-05 independent evaluator exists | DONE |
| Unit tests pass | DONE |
| Smoke fixture writes required outputs | DONE |
| Human repair-coordinate subset converted and evaluated | DONE |
| Agreement against adjudicated labels reported | DONE |
| Full normalized EG-07 layout export evaluated | TODO |

## Next Work

1. Export the full EG-07 frozen rerun layouts into the evaluator JSON schema.
2. Run `evaluation/independent_relation_evaluator.py` on the full 531-scene
   InstructScene output package.
3. Use EG-08 to compute paired confidence intervals from the full evaluator
   per-scene CSV.
