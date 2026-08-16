# EG-07 Final Evaluation Report (2026-08-14)

Final evaluation of the frozen Collision-gated Floor-Prior method on the
531-scene formal candidate. Runbook Step 4–6. Protocol `eg2027-eg05-v1`.

## VERDICT: GO (EG07_FINAL_PASS)

Structural completion gate passes. Scientific metrics are reported; statistical
significance is deferred to EG-08 (paired confidence intervals) per the frozen
handoff. No development-anchor (EG-01/EG-04 "current result anchor") values are
used as thresholds.

## 1. Input identity

| item | value |
|---|---|
| layouts.json | `results/eg07/formal_candidate/layouts.json` |
| size (bytes) | 5952882 |
| SHA-256 | `663ce5ff76698358c47e9542563bd01a788bc90efb9f299e7c261da2399e281d` |
| export validation.json | PASS, errors `[]`, warnings `[]` |
| validation_recheck.json | PASS, errors `[]`, warnings `[]` |

## 2. Final relation metrics (EG-05, fair-comparison order)

| room | n_scenes | n_relations | baseline acc | main acc | gain | baseline sat | main sat |
|---|---:|---:|---:|---:|---:|---:|---:|
| bedroom | 162 | 245 | 0.7265 | 0.7306 | +0.0041 | 178 | 179 |
| livingroom | 192 | 294 | 0.6054 | 0.6122 | +0.0068 | 178 | 180 |
| diningroom | 177 | 269 | 0.5836 | 0.5874 | +0.0037 | 157 | 158 |
| **overall** | 531 | 808 | 0.6349 | 0.6399 | **+0.0050** | 513 | 517 |

- missing target objects (per variant, remain in denominator): overall 93
  (bedroom 17, livingroom 40, diningroom 36); unsupported predicates: 0
  (explicitly counted, none present — not silently dropped).

## 3. Movement / movement-matched baselines (EG-06, overall)

| variant | overall relation accuracy |
|---|---:|
| baseline | 0.6349 |
| **collision_gated_floor_prior (main)** | **0.6399** |
| random_movement_matched_seed0 | 0.6225 |
| random_movement_matched_seed1 | 0.6250 |
| random_movement_matched_seed2 | 0.6287 |
| random mean (seeds 0/1/2) | 0.6254 |
| generic_relation_optimizer | 0.6411 |

- main vs baseline: +0.0050 (517 vs 513 satisfied)
- main vs random-mean: +0.0144
- main vs generic_relation_optimizer: **-0.0012** (518 vs 517 — the generic
  budget-matched optimizer is 1 relation ahead; significance deferred to EG-08)
- fairness: random baselines are exact per-object XZ movement-matched; generic
  optimizer is within the per-object movement budget.

## 4. Structural counts, gate, mesh / collision

| item | value |
|---|---|
| scenes / layouts | 531 / 1062 |
| bedroom / livingroom / diningroom | 162 / 192 / 177 |
| target_relations (baseline) | 808 (direct 678, protocol_mapped_composite 130) |
| gate repair / fallback_baseline | 492 / 39 |
| mesh collision available | 531 / 531 scenes |
| baseline collision pairs (total) | 1075 |
| repair collision pairs (total, raw) | 1114 |
| chosen main collision pairs (total) | 1061 (≤ baseline; safety non-worsening) |

## 5. Sample / seed / provenance

| item | value |
|---|---|
| artifact_status | formal_candidate |
| generator seed policy | seed 0; one generated layout per validation scene |
| EG-06 movement-baseline seeds | 0, 1, 2 (movement seeds, not generator seeds) |
| code_commit (generation) | `3a167d813d74ab18df8762d57ff3b4a47789e3af` |
| exporter fix commit | `e5fe83731bae789350574312847db5eaeacb8259` |
| method code anchor | `feb37414db42faec3d600b66d17186ed3da8a22e` |
| source_config_id | `floor_prior_max1.8_mesh_p2_close0.75_far1.6` |
| frozen config SHA-256 | `052ACE5B295348483CE9B6110B5BD7933235424A55CC2108C966431E516829E2` |

## 6. GO / NO-GO

See `eg07_gonogo_20260814.md` for the full itemized table with evidence paths.
Summary: **all structural gates GO**; scientific metric gates REPORTED
(significance -> EG-08); mesh safety GO; unsupported/missing relations
explicitly counted (GO).

## 7. Output files

- `eg07_final_report_20260814.md` (this file)
- `eg07_gonogo_20260814.md` / `.csv` / `.json`
- `eg07_final_metrics_20260814.json` / `.csv`
- EG-05 outputs: `results/independent_eval/eg2027/eg07_full_independent_eval/`
- EG-06 outputs: `results/independent_eval/eg2027/eg06_full_movement_baselines/`
