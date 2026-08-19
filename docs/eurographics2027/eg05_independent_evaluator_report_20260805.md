# EG-05 Independent Evaluator Report

Date: 2026-08-05
Task: EG-05 implement and validate independent evaluator
Branch: `agent/eg01-eg02-eurographics2027`
Depends on: EG-02 protocol and EG-04 method freeze

## Verdict

EG-05 is now full-run complete on the EG-07 formal evidence package. The
independent evaluator is available as a runnable module with unit tests, a smoke
fixture, per-scene CSV output, an audit JSON, a repair-coordinate alignment
against the adjudicated EG-02 human subset, and a full 531-scene EG-07
evaluation.

It is evidence-gate complete for point estimates. It is **not yet a final paper
claim of statistical significance** because paired confidence intervals are
deferred to EG-08.

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

## EG-07 Full Independent Evaluation

Source package:

`eg07_final_delivery_20260814/`

Input layout export:

`eg07_final_delivery_20260814/layouts/layouts.json`

Input SHA-256:

`663ce5ff76698358c47e9542563bd01a788bc90efb9f299e7c261da2399e281d`

Full-run outputs:

- `eg07_final_delivery_20260814/eg05/per_relation.csv`
- `eg07_final_delivery_20260814/eg05/per_scene.csv`
- `eg07_final_delivery_20260814/eg05/summary.csv`
- `eg07_final_delivery_20260814/eg05/audit.json`

Audit status:

| Check | Value |
|---|---:|
| Layout rows | 1062 |
| Per-scene rows | 1062 |
| Per-relation rows | 1616 |
| Missing baseline scenes | 0 |
| Unsupported predicates | 0 |
| Missing-object relation cases | 93 |

Full-run relation accuracy:

| Room | Baseline | Collision-gated Floor-Prior | Gain |
|---|---:|---:|---:|
| Bedroom | 0.7265 | 0.7306 | +0.0041 |
| Dining room | 0.5836 | 0.5874 | +0.0037 |
| Living room | 0.6054 | 0.6122 | +0.0068 |
| Overall | 0.6349 | 0.6399 | +0.0050 |

Count interpretation:

| Variant | Satisfied relations | Total target relations |
|---|---:|---:|
| Baseline | 513 | 808 |
| Collision-gated Floor-Prior | 517 | 808 |

This means the main method improves the point estimate by 4 satisfied target
relations out of 808. The direction is positive in all three room types, but the
effect size is small. The paper should report this as a modest point-estimate
gain until EG-08 computes paired confidence intervals.

## Current Status

| Item | Status |
|---|---|
| EG-05 independent evaluator exists | DONE |
| Unit tests pass | DONE |
| Smoke fixture writes required outputs | DONE |
| Human repair-coordinate subset converted and evaluated | DONE |
| Agreement against adjudicated labels reported | DONE |
| Full normalized EG-07 layout export evaluated | DONE |
| Paired confidence interval for final paper claim | TODO: EG-08 |

## Next Work

1. Use EG-08 to compute paired confidence intervals from
   `eg07_final_delivery_20260814/eg05/per_scene.csv` and
   `eg07_final_delivery_20260814/eg05/per_relation.csv`.
2. Keep the paper wording conservative until the confidence interval is known:
   "modest positive point-estimate gain" is supported; "statistically
   significant improvement" is not yet supported.
3. Preserve the missing-object convention in any table caption: missing target
   objects remain in the denominator.
