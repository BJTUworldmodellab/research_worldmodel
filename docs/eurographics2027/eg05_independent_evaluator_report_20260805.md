# EG-05 Independent Evaluator Report

Date: 2026-08-05
Task: EG-05 implement and validate independent evaluator
Branch: `agent/eg01-eg02-eurographics2027`
Depends on: EG-02 protocol and EG-04 method freeze

## Verdict

EG-05 implementation has started and the independent evaluator is now available
as a runnable module with unit tests, a smoke fixture, per-scene CSV output, and
an audit JSON.

It is **not yet final evidence-gate complete** because the evaluator has not
been run against a normalized full EG-07 layout export or compared directly
against the adjudicated EG-02 human subset using the final evaluator outputs.

## Implemented Evaluator

Path:

`evaluation/independent_relation_evaluator.py`

The evaluator follows `evaluation/independent_protocol.md` and deliberately
does not import repair, verifier, candidate-scoring, or fallback code from the
optimizer.

Input:

```text
JSON list or object with layouts/scenes.
Each layout has scene_id, room_type, layout_variant, source_config_id, objects,
and target_relations.
```

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

Test path:

`tests/test_independent_relation_evaluator.py`

Command:

```powershell
& "C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -p "test_independent_relation_evaluator.py" -v
```

Result:

```text
Ran 3 tests
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
| Deterministic CLI output | Yes | Smoke fixture writes all four expected files. |

## Smoke Output

Input fixture:

`evaluation/fixtures/eg05_smoke_layouts.json`

Command:

```powershell
& "C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" evaluation/independent_relation_evaluator.py --input evaluation/fixtures/eg05_smoke_layouts.json --output-dir results/independent_eval/eg2027/eg05_smoke_fixture --run-id eg05_smoke_fixture
```

Generated files:

- `results/independent_eval/eg2027/eg05_smoke_fixture/per_relation.csv`
- `results/independent_eval/eg2027/eg05_smoke_fixture/per_scene.csv`
- `results/independent_eval/eg2027/eg05_smoke_fixture/summary.csv`
- `results/independent_eval/eg2027/eg05_smoke_fixture/audit.json`

Smoke summary:

| Layout variant | Room | Relations | Relation accuracy | Conditional accuracy | Missing rate | Unsupported rate |
|---|---|---:|---:|---:|---:|---:|
| baseline | bedroom | 2 | 0.50 | 1.00 | 0.50 | 0.00 |
| collision_gated_floor_prior | bedroom | 2 | 0.50 | 1.00 | 0.50 | 0.00 |
| baseline | livingroom | 3 | 0.00 | 0.00 | 0.00 | 0.3333 |

## Human-Subset Status

EG-02 produced an adjudicated human subset and an automatic-vs-human diagnostic
alignment report. However, EG-05 should not claim final human agreement until
the independent evaluator is run on the exact normalized layout export used for
the human subset.

Current status:

| Item | Status |
|---|---|
| EG-02 adjudicated human labels exist | DONE |
| EG-05 independent evaluator exists | DONE |
| Human subset converted to evaluator input schema | TODO |
| Independent evaluator run on human subset | TODO |
| Agreement against adjudicated labels reported from EG-05 outputs | TODO |

## Next Work To Finish EG-05 Fully

1. Export the EG-02 human-review scenes into the evaluator JSON schema.
2. Run `evaluation/independent_relation_evaluator.py` on that export.
3. Compare `per_relation.csv` against `results/eurographics2027/eg02_human_review_v2_final/final_labels.csv`.
4. Record agreement metrics in a versioned EG-05 human-alignment report.
5. If agreement is below the protocol threshold, do not use independent-evaluator
   numbers as final claim evidence until the protocol is revised before EG-07.
