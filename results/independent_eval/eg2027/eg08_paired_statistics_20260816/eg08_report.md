# EG-08 Paired Scene-Level Statistics

Date: 2026-08-16
Branch: `agent/eg01-eg02-eurographics2027`
Schema: `eg2027-eg08-paired-scene-bootstrap-v1`

## Verdict

**EG08_GO**

The frozen primary gate compares Collision-gated Floor-Prior with the mean of the three movement-matched random seeds. The gate is GO only when the overall 95% paired scene-cluster bootstrap CI lower bound is above zero.

Canonical primary gain: **1.444 pp**, relation-weighted 95% CI **[0.745, 2.201] pp**.

## 50,000-round stratified sensitivity comparisons

| Comparison | Main | Control | Gain (pp) | 95% CI (pp) | Classification | Gate |
|---|---:|---:|---:|---:|---|---|
| main_vs_baseline | 0.639851 | 0.634901 | +0.495 | [-0.126, +1.227] | INCONCLUSIVE | REPORTED |
| main_vs_random_seed0 | 0.639851 | 0.622525 | +1.733 | [+0.754, +2.806] | MAIN_HIGHER | REPORTED |
| main_vs_random_seed1 | 0.639851 | 0.625000 | +1.485 | [+0.606, +2.494] | MAIN_HIGHER | REPORTED |
| main_vs_random_seed2 | 0.639851 | 0.628713 | +1.114 | [+0.370, +1.966] | MAIN_HIGHER | REPORTED |
| main_vs_random_mean | 0.639851 | 0.625413 | +1.444 | [+0.741, +2.206] | MAIN_HIGHER | PRIMARY |
| main_vs_generic_optimizer | 0.639851 | 0.641089 | -0.124 | [-0.636, +0.376] | INCONCLUSIVE | REPORTED |

## Room-level stratified sensitivity for the primary comparison

| Room | Scenes | Relations | Gain (pp) | 95% CI (pp) | Classification |
|---|---:|---:|---:|---:|---|
| bedroom | 162 | 245 | +1.224 | [+0.285, +2.326] | MAIN_HIGHER |
| livingroom | 192 | 294 | +1.361 | [+0.000, +2.842] | INCONCLUSIVE |
| diningroom | 177 | 269 | +1.735 | [+0.615, +3.125] | MAIN_HIGHER |

## Methodology

- Canonical EG06 integration: both scene-unweighted and relation-weighted intervals, 10,000 unstratified scene resamples, seed 20260816.
- Estimand: `difference of relation-accuracy ratios (sum satisfied / sum target relations)`.
- Resampling unit: `paired scene cluster`.
- Overall stratification: `fixed bedroom/livingroom/diningroom scene counts`.
- Interval: percentile 95% CI, 50,000 rounds, base seed 20260816.
- Missing targets remain in the denominator; unsupported predicates are explicitly counted.
- Bootstrap fraction above zero is a stability diagnostic, not a p-value.

## Safety and claim boundary

- Mesh collision pairs: chosen main 1061 vs baseline 1075 — GO.
- Only the overall main-vs-random-mean interval is the frozen superiority gate.
- Baseline, individual random seeds, generic optimizer, and room-level intervals are reported, not silently promoted to additional gates.
- A CI that includes zero does not establish superiority; it must be described as inconclusive.

## Inputs

- `eg05_per_scene`: `eg07_final_delivery_20260814/eg05/per_scene.csv` — SHA-256 `a6a5f87d293ab89f546537bb2bd28010f655d28893c972dbd8f2fa760f6f8e7d`
- `eg06_per_scene`: `eg07_final_delivery_20260814/eg06/per_scene.csv` — SHA-256 `d67af62ce73fe344adb3ce83af9d2a2b7da3494a95675dea7585585b01882091`
- `eg07_final_metrics`: `eg07_final_delivery_20260814/final/eg07_final_metrics_20260814.json` — SHA-256 `79fc4c928f3c64b09589b0d4ea88819ec5e277c8b58e089868f276fadf768449`
