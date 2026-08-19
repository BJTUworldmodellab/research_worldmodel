# Eurographics 2027 Formal Claim-to-Evidence Map

Date: 2026-08-17

Task: EG-09 formal paper result freeze

Branch: `agent/eg01-eg02-eurographics2027`

## Status

**EG09_CLAIMS_FROZEN**

This file supersedes the EG-01 development anchor for paper-facing claims. The
EG-01 and EG-04 documents remain unchanged as historical audit records; their
numbers must not be copied into the current abstract, main-result narrative, or
formal tables.

## Frozen identity

| Field | Formal value |
|---|---|
| Main method | Collision-gated Floor-Prior |
| Config ID | `floor_prior_max1.8_mesh_p2_close0.75_far1.6` |
| Config SHA-256 | `052ACE5B295348483CE9B6110B5BD7933235424A55CC2108C966431E516829E2` |
| Generation commit | `3a167d813d74ab18df8762d57ff3b4a47789e3af` |
| Exporter-fix commit | `e5fe83731bae789350574312847db5eaeacb8259` |
| Formal layouts SHA-256 | `663ce5ff76698358c47e9542563bd01a788bc90efb9f299e7c261da2399e281d` |
| Scenes / layouts / relations | 531 / 1,062 / 808 |
| Room counts | bedroom 162 / living room 192 / dining room 177 |
| Generator seed policy | seed 0; one layout per validation scene |

## C-EG1: formal relation result

| Room | Scenes | Relations | Original baseline | Collision-gated Floor-Prior | Point gain (pp) |
|---|---:|---:|---:|---:|---:|
| Bedroom | 162 | 245 | 0.7265 | 0.7306 | +0.408 |
| Living room | 192 | 294 | 0.6054 | 0.6122 | +0.680 |
| Dining room | 177 | 269 | 0.5836 | 0.5874 | +0.372 |
| **Overall** | **531** | **808** | **0.6349** | **0.6399** | **+0.495** |

Evidence:

- `eg07_final_delivery_20260814/eg05/summary.csv`
- `eg07_final_delivery_20260814/eg05/per_scene.csv`
- `eg07_final_delivery_20260814/eg05/per_relation.csv`
- `eg07_final_delivery_20260814/eg05/audit.json`
- `eg07_final_delivery_20260814/final/eg07_final_metrics_20260814.json`

Boundary: the overall paired confidence interval against the original baseline
includes zero. These values may be reported as point estimates, but not as a
statistically established improvement over the original baseline.

## C-EG2: frozen primary statistical claim

| Field | Formal value |
|---|---:|
| Main relation accuracy | 0.639851 |
| Three-seed movement-matched random mean | 0.625413 |
| Difference | +1.4439 pp |
| Paired scene-level bootstrap 95% CI | [+0.7453, +2.2005] pp |
| Resamples / seed | 10,000 / 20260816 |
| Decision | GO; lower bound > 0 |

Safe wording:

> On the frozen 531-scene evaluation, Collision-gated Floor-Prior improves
> realized relation accuracy over the mean of three exact movement-matched
> random controls by 1.44 percentage points (paired scene-level bootstrap 95%
> CI, 0.75 to 2.20 points).

Evidence:

- `eg07_final_delivery_20260814/eg06/summary.csv`
- `eg07_final_delivery_20260814/eg06/per_scene.csv`
- `eg07_final_delivery_20260814/eg06/per_relation.csv`
- `eg07_final_delivery_20260814/eg06/movement_audit.csv`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/canonical_eg06_ci.json`
- `results/independent_eval/eg2027/eg08_paired_statistics_20260816/paired_ci.csv`

## C-EG3: collision-gate safety claim

| Field | Formal value |
|---|---:|
| Repair selected | 492 scenes |
| Baseline fallback | 39 scenes |
| Mesh evidence available | 531 / 531 scenes |
| Original collision pairs | 1,075 |
| Chosen-main collision pairs | 1,061 |
| Decision | non-worsening |

Safe wording:

> The collision gate keeps the chosen main layouts' aggregate FCL
> mesh-collision pair count no higher than the original layouts (1,061 versus
> 1,075).

Boundary: this is an aggregate non-worsening statement, not a claim that every
scene is collision-free.

## Comparator boundaries

| Comparator | Point result | 95% CI for main minus comparator | Allowed conclusion |
|---|---:|---:|---|
| Original InstructScene baseline | +0.495 pp | [-0.125, +1.223] pp | inconclusive |
| Random movement seed 0 | +1.733 pp | [+0.755, +2.829] pp | main higher |
| Random movement seed 1 | +1.485 pp | [+0.613, +2.497] pp | main higher |
| Random movement seed 2 | +1.114 pp | [+0.369, +1.963] pp | main higher |
| Random-seed mean | +1.444 pp | [+0.745, +2.201] pp | primary GO |
| Generic relation optimizer | -0.124 pp | [-0.633, +0.376] pp | inconclusive |

Not supported:

- Collision-gated Floor-Prior is statistically superior to the original
  InstructScene baseline.
- Collision-gated Floor-Prior is statistically superior to the budget-matched
  generic optimizer.
- Every room has a strictly positive 95% interval; the living-room sensitivity
  lower bound equals zero.
- The method outperforms ReSpace, SDGScenes, or another external system without
  a same-protocol evaluation.

## Historical-number boundary

The following are development or aggressive-ablation anchors, not formal EG09
paper numbers:

```text
Direct Repair: 0.8449 / 0.6871 / 0.7212; +10.2 / +14.3 / +13.4 pp
EG-01 Floor-Prior anchor: 0.8163 / 0.6395 / 0.6729; +7.76 / +8.84 / +7.81 pp
Weighted EG-01 anchor: 0.7040; +8.2 pp
```

They may remain in versioned EG-01/EG-04 audit material, but not in active
paper-facing prose or result tables.

## Active surfaces and historical exclusions

The EG09 consistency check treats these as active surfaces:

- `paper/neurips_ra_instructscene/main.tex`
- `docs/eurographics2027/claim_to_table_map_eg2027.md`
- `manifests/eurographics2027/eg09_paper_claim_freeze_manifest.json`

Historical documents, archived reports, visual diagnostics, and frozen EG-01
through EG-04 manifests are intentionally not rewritten. Preserving them keeps
the development-to-formal-result change auditable.

## Remaining provenance boundary

The committed lightweight evidence contains the complete EG05/EG06 per-scene
and per-relation tables needed to reproduce the formal statistics. It does not
contain the three original room-level generator JSON files. This does not block
the EG09 paper-number freeze, but it remains a gap for full
generator-to-statistics reconstruction.
