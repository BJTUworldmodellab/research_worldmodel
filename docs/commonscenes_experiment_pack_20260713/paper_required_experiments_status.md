# Paper-Required Experiment Status

## 1. Cross-Room Main Table

Setting: CommonScenes baseline vs `generic-gate t1.5`, no official-search, same renderer and same scene set per room.

| room | scenes | baseline generic total | repaired generic total | delta | collision penalty baseline -> repaired | changed box ratio | mean center move | mean SSIM | mean PSNR | mean GLB Chamfer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bedroom | 162 | 0.981312 | 0.984370 | +0.003058 | 164.012 -> 161.487 | 0.013805 | 0.015509 | 0.998014 | 80.293 | 0.128786 |
| livingroom | 52 | 0.970915 | 0.973113 | +0.002198 | 54.798 -> 51.841 | 0.036545 | 0.037404 | 0.994654 | 61.967 | 0.131053 |
| diningroom | 69 | 0.968892 | 0.970467 | +0.001575 | 103.200 -> 99.130 | 0.023392 | 0.018451 | 0.998741 | 77.319 | 0.087553 |
| library | 56 | 0.958588 | 0.964019 | +0.005431 | 72.028 -> 68.498 | 0.040541 | 0.038693 | 0.996117 | 56.616 | 0.130930 |

Interpretation: the same repair rule gives small but consistent relation-score gains and collision-penalty reductions across bedroom, livingroom, diningroom, and library. The visual-difference metrics remain small on average, but the maximum movement can approach the configured 1.5m gate, so the largest-change cases still need visual inspection.

Completed artifacts:

```text
docs/commonscenes_experiment_pack_20260713/data/
docs/commonscenes_experiment_pack_20260713/data/other_rooms/
```

## 2. Parameter Ablation: Bedroom Split

Setting: CommonScenes bedroom split, same baseline and renderer. `changed box ratio`, `mean move`, and `max move` below come from the repair summary because the image-quality script treats tiny floating-point box differences as changed boxes for `t0.8/t1.2`.

| threshold | accepted scenes | edits | baseline generic total | repaired generic total | delta | collision penalty baseline -> repaired | changed box ratio | mean move | max move | mean SSIM | mean PSNR | mean GLB Chamfer |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.8 | 3 | 3 | 0.981312 | 0.981821 | +0.000510 | 164.012 -> 163.575 | 0.002588 | 0.001824 | 0.727 | 0.999597 | 87.506 | 0.113173 |
| 1.2 | 13 | 13 | 0.981312 | 0.983860 | +0.002548 | 164.012 -> 162.251 | 0.011217 | 0.010009 | 1.197 | 0.998696 | 81.771 | 0.119049 |
| 1.5 | 16 | 16 | 0.981312 | 0.984370 | +0.003058 | 164.012 -> 161.487 | 0.013805 | 0.015509 | 1.490 | 0.998014 | 80.293 | 0.128786 |

Interpretation: `t1.5` gives the largest relation gain and collision reduction, but also the largest movement and geometry change. `t1.2` is the conservative alternative with most of the gain and lower Chamfer. `t0.8` is visually safest but under-edits.

Completed artifacts:

```text
docs/commonscenes_experiment_pack_20260713/data/generic_gate_t0.8_*
docs/commonscenes_experiment_pack_20260713/data/generic_gate_t1.2_*
docs/commonscenes_experiment_pack_20260713/data/generic_gate_t1.5_*
```

## 3. Original InstructScene Validation

The original InstructScene validation experiments are already available in:

```text
docs/relation_aware_instructscene_experiment_report.md
docs/relation_aware_mesh_visual_experiment_report.md
docs/relation_aware_additional_validity_experiments.md
```

Main selected-relation results:

| room | scenes | relations | baseline layout acc | relation-aware acc | absolute gain | error reduction |
|---|---:|---:|---:|---:|---:|---:|
| bedroom | 162 | 245 | 0.7388 | 0.8735 | +0.1347 | 51.6% |
| livingroom | 192 | 294 | 0.5510 | 0.7415 | +0.1905 | 42.4% |
| diningroom | 177 | 269 | 0.5948 | 0.7844 | +0.1896 | 46.8% |

Mesh-validity-safe variant:

| room | baseline acc | direct repair acc | collision-gated acc | gated gain | baseline mesh pair rate | gated mesh pair rate | fallback scenes |
|---|---:|---:|---:|---:|---:|---:|---:|
| bedroom | 0.7388 | 0.8735 | 0.8449 | +0.1061 | 0.070244 | 0.064878 | 9 |
| livingroom | 0.5510 | 0.7415 | 0.6871 | +0.1361 | 0.031257 | 0.030540 | 14 |
| diningroom | 0.5948 | 0.7844 | 0.7212 | +0.1264 | 0.034229 | 0.033154 | 13 |

Multi-seed summary:

| room | N | baseline mean | baseline std | repaired mean | repaired std | gain mean | gain std |
|---|---:|---:|---:|---:|---:|---:|---:|
| bedroom | 3 | 0.7565 | 0.0209 | 0.8939 | 0.0178 | 0.1374 | 0.0125 |
| livingroom | 3 | 0.5420 | 0.0086 | 0.7483 | 0.0180 | 0.2063 | 0.0246 |
| diningroom | 3 | 0.5923 | 0.0021 | 0.7993 | 0.0170 | 0.2069 | 0.0187 |

Interpretation: this is the main evidence that the method works on the original target setting. For paper claims involving mesh collision, use the collision-gated variant rather than the direct repair variant.

## 4. Success/Failure Visualization Panels

CommonScenes qualitative panels were generated from the same rendered PNGs used by the quantitative image-quality evaluation.

Local artifacts:

```text
visual/commonscenes_paper_panels/low_change_examples_grid.png
visual/commonscenes_paper_panels/high_change_risk_examples_grid.png
visual/commonscenes_paper_panels/manifest.json
```

Selected cases:

| room | low-change case | high-change risk case |
|---|---|---|
| bedroom | Bedroom-54233 | MasterBedroom-19531 |
| livingroom | LivingRoom-33324 | LivingRoom-1520 |
| diningroom | DiningRoom-9824 | DiningRoom-9630 |
| library | Library-40642 | Library-35695 |

Interpretation: the low-change grid supports the claim that many repairs are visually tiny. The high-change grid should be used as a failure/risk analysis figure, not as the main teaser, because these are the cases where the repair still changes scene geometry noticeably.

## 5. Bootstrap Robustness

Bootstrap over scenes was run for visual/geometric disturbance metrics using 5000 resamples per room.

Artifacts:

```text
docs/commonscenes_experiment_pack_20260713/data/bootstrap/bootstrap_ci_summary.json
docs/commonscenes_experiment_pack_20260713/data/bootstrap/bootstrap_ci_summary.md
```

Compact result:

| room | mean SSIM 95% CI | mean changed-pixel ratio 95% CI | mean GLB Chamfer 95% CI |
|---|---:|---:|---:|
| bedroom | [0.996833, 0.999028] | [0.000930, 0.002780] | [0.117874, 0.140710] |
| livingroom | [0.991977, 0.997086] | [0.002128, 0.005893] | [0.117038, 0.146406] |
| diningroom | [0.997836, 0.999543] | [0.000421, 0.001488] | [0.078378, 0.098258] |
| library | [0.993472, 0.998292] | [0.001199, 0.004583] | [0.109945, 0.156314] |

Interpretation: visual/geometric disturbance remains small under scene-level bootstrap. This supports a stability claim for rendered-image similarity and GLB-level geometry change. It does not estimate uncertainty for relation-score gains because relation-level per-scene rows are not yet exported.

## 6. Remaining Paper Experiments

Pending sequence:

1. Optional object-level Chamfer if the paper needs a stricter geometry-change audit.
2. Optional human/preference inspection if making visual-quality claims stronger than "low perturbation".
