# EG-08 Paired Scene-Level Statistics Report

Date: 2026-08-16
Branch: `agent/eg01-eg02-eurographics2027`
Input commit: `2adeb442bd3d2d78520ac2b6e2d6322dbd4caa27`

## Verdict

**EG08_GO**

The frozen primary gate passes. Collision-gated Floor-Prior improves overall
relation accuracy over the mean of the three exact movement-matched random
baselines by **+1.444 percentage points**. The accepted EG06 paired scene-level
percentile bootstrap 95% confidence interval is **[+0.745, +2.201] pp**, so its lower
bound is above zero.

This closes the specific EG-08 gate defined by the EG-06 persuasiveness audit.
It does not establish superiority over every comparator.

## Overall paired comparisons

| Comparison | Main | Control | Gain (pp) | 95% CI (pp) | Interpretation |
|---|---:|---:|---:|---:|---|
| Main vs baseline | 0.639851 | 0.634901 | +0.495 | [-0.126, +1.227] | Inconclusive |
| Main vs random seed 0 | 0.639851 | 0.622525 | +1.733 | [+0.754, +2.806] | Main higher |
| Main vs random seed 1 | 0.639851 | 0.625000 | +1.485 | [+0.606, +2.494] | Main higher |
| Main vs random seed 2 | 0.639851 | 0.628713 | +1.114 | [+0.370, +1.966] | Main higher |
| **Main vs random-seed mean** | **0.639851** | **0.625413** | **+1.444** | **[+0.741, +2.206]** | **Primary gate GO** |
| Main vs generic optimizer | 0.639851 | 0.641089 | -0.124 | [-0.636, +0.376] | Inconclusive |

## Room-level sensitivity analysis

| Room | Scenes | Relations | Gain vs random mean (pp) | 95% CI (pp) | Interpretation |
|---|---:|---:|---:|---:|---|
| Bedroom | 162 | 245 | +1.224 | [+0.285, +2.326] | Main higher |
| Living room | 192 | 294 | +1.361 | [+0.000, +2.842] | Inconclusive; lower bound equals zero |
| Dining room | 177 | 269 | +1.735 | [+0.615, +3.125] | Main higher |

Room-level intervals come from the additional 50,000-round stratified
sensitivity analysis. They are secondary diagnostics, not three separate gates.

## Accepted statistical protocol and sensitivity analysis

- Accepted EG06 integration: 10,000 paired scene-level resamples over all 531
  scenes, seed `20260816`, using `scripts/check_eg06_full_completion.py`.
- Accepted estimators: scene-unweighted mean difference and relation-weighted
  difference of total satisfied / total target relations.
- Primary acceptance requires all three random seeds and their mean to have a
  positive lower bound under both accepted estimators. This passes.
- Additional sensitivity analysis: 50,000 relation-weighted scene-cluster
  resamples stratified by room, seed `20260816`.
- Sensitivity interval for Main vs random mean: `[+0.741, +2.206] pp`, consistent
  with the accepted interval `[+0.745, +2.201] pp`.
- Missing target objects remain in the denominator; unsupported predicates are
  explicitly counted.
- Primary gate: overall Main minus three-seed random mean CI lower bound `> 0`.

The accepted EG06 completion commit fixed the primary resampling details before
this EG08 upload. EG08 integrates those values and retains the higher-round,
room-stratified calculation only as a sensitivity check.

## Input and integrity checks

| Check | Result |
|---|---|
| Unique scenes | 531 |
| Room counts | bedroom 162 / livingroom 192 / diningroom 177 |
| Target relations | 808 |
| EG05 rows | 1,062 = 531 × 2 |
| EG06 rows | 3,186 = 531 × 6 |
| Missing targets | 93, retained in denominator |
| Unsupported predicates | 0 |
| EG05 baseline/main equals EG06 baseline/main | PASS, field-by-field |
| Random movement matching | PASS, exact per-object XZ magnitude |
| Generic optimizer budget | PASS |
| Mesh collision non-worsening | PASS, chosen main 1,061 ≤ baseline 1,075 |

Input SHA-256 values:

- EG05 `per_scene.csv`: `a6a5f87d293ab89f546537bb2bd28010f655d28893c972dbd8f2fa760f6f8e7d`
- EG06 `per_scene.csv`: `d67af62ce73fe344adb3ce83af9d2a2b7da3494a95675dea7585585b01882091`
- EG07 final metrics JSON: `79fc4c928f3c64b09589b0d4ea88819ec5e277c8b58e089868f276fadf768449`

## Independent validation

The primary interval was recomputed with a separate Python-standard-library
implementation, 20,000 replicates, and seed `9102`. It returned the same point
gain (`0.0144389439`) and a 95% interval of
`[0.0073347394, 0.0221130221]`. The positive lower bound is therefore not
specific to the NumPy implementation or primary random seed.

Four EG08 regression tests cover the ratio-of-sums estimand, three-seed random
mean, paired deterministic resampling, and interval classification. These four
tests and the four EG05 independent-evaluator tests pass. Full repository test
discovery additionally requires the optional `shapely` dependency used by the
pre-existing ablation regression test; that unrelated test was not executed in
the current bundled runtime.

## Safe paper claim

Safe:

> On the frozen 531-scene evaluation, Collision-gated Floor-Prior improves
> relation accuracy over the mean of three exact movement-matched random
> baselines by 1.44 percentage points (paired scene-level bootstrap 95% CI,
> 0.75 to 2.20 points), while the collision gate keeps the chosen main layouts'
> mesh-collision pair count no higher than baseline.

Not supported:

- Main is statistically superior to the original InstructScene baseline.
- Main is statistically superior to the budget-matched generic optimizer.
- Every individual room has a strictly positive 95% interval.

## Reproducible outputs

- `scripts/compute_eg08_paired_statistics.py`
- `tests/test_eg08_paired_statistics.py`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/paired_ci.csv`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/canonical_eg06_ci.json`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/paired_statistics.json`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/eg08_report.md`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/EG08_GO`

The lightweight EG07 delivery does not contain the three original room-level
generator JSON files. They are not required to reproduce this EG-08 calculation
from the committed EG05/EG06 per-scene tables, but remain a provenance archive
gap for full generator-to-statistics reproduction.
