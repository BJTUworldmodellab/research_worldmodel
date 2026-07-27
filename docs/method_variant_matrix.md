# Method Variant Matrix for Submission Freeze

Date: 2026-07-27  
Status: T05 draft freeze  
Config source: `configs/paper_main.yaml`

## Why This File Exists

The project currently has several related but different repair variants. They
answer different questions and use different metrics. This file freezes their
roles so later experiments, figures, and paper claims do not mix numbers across
variants.

Short version:

- **Main method**: Collision-gated Floor-Prior.
- **Aggressive ablation**: Direct Repair.
- **Cross-generator support**: CommonScenes Generic-Gate.
- **Safety ablation**: SG-Guarded Overlap Repair.

## Variant Matrix

| Variant ID | Paper Name | Role | Generator | Main Metric | Safety / Diagnostic Metrics | Can Appear In Main Table? |
|---|---|---|---|---|---|---|
| `collision_gated_floor_prior` | Collision-gated Floor-Prior | Main method | InstructScene | selected-relation accuracy | mesh-collision pair rate, movement, overlap | Yes |
| `direct_repair` | Direct Repair | Aggressive ablation / upper-bound style comparison | InstructScene | selected-relation accuracy | movement, overlap, mesh collision as warning | No, ablation only |
| `commonscenes_generic_gate` | CommonScenes Generic-Gate | Cross-generator external-support experiment | CommonScenes | generic geometric relation total | collision penalty, changed-box ratio, SSIM, GLB Chamfer, official CommonScenes score as diagnostic only | Separate external table only |
| `sg_guarded_overlap_repair` | SG-Guarded Overlap Repair | Layout-only safety ablation | InstructScene | SG-layout consistency and oriented-box overlap | movement | No, safety ablation only |

## Frozen Definitions

### Main Method: Collision-gated Floor-Prior

This is the paper's main method for the original InstructScene setting.

It uses explicit relation triples parsed from instructions and repairs the
generated layout by bounded XZ floor-plane candidate selection. It keeps the
repair conservative through a collision gate.

Default hyperparameters:

| Hyperparameter | Value |
|---|---:|
| repair passes | 2 |
| close distance | 0.75 |
| far distance | 1.6 |
| max repair move | 1.8 |
| repair overlap weight | 1.0 |

Allowed paper wording:

> Collision-gated Floor-Prior improves selected-relation accuracy on bedroom,
> livingroom, and diningroom InstructScene validation splits while reducing
> mesh-collision pair rate relative to the baseline.

Forbidden paper wording:

- All gains come from the graph-to-layout decoder.
- The method solves all language constraints or implicit commonsense.
- Direct Repair's larger gains are the main-method gains.

### Aggressive Ablation: Direct Repair

Direct Repair optimizes relation satisfaction more aggressively and does not
serve as the paper main method.

Allowed role:

- Show how much relation gain is possible without the collision-gated safety
  restriction.
- Serve as an ablation or upper-bound style diagnostic.

Forbidden role:

- It must not be reported as the main method.
- It must not be used for mesh-collision reduction claims.

### Cross-Generator Experiment: CommonScenes Generic-Gate

CommonScenes Generic-Gate is external-support evidence showing that the repair
idea can transfer to another generator in a limited, carefully stated way.

Allowed paper wording:

> CommonScenes Generic-Gate gives small but consistent generic geometric
> relation gains across bedroom, livingroom, diningroom, and library under a
> no-official-search setting, while lowering collision penalty.

Mandatory disclosure:

> Bedroom official CommonScenes Total decreases from 0.9732 to 0.9696.

Forbidden paper wording:

- The method improves the official CommonScenes metric.
- The method is fully better than CommonScenes.
- CommonScenes Generic-Gate uses the same metric as InstructScene
  selected-relation accuracy.

### Safety Ablation: SG-Guarded Overlap Repair

SG-Guarded Overlap Repair is a layout-only safety ablation. It is not a
ground-truth relation accuracy experiment.

Allowed paper wording:

> SG-Guarded Overlap Repair reduces oriented-box overlap on 162 bedroom
> layout-only scenes while preserving protected SG-layout consistency.

Forbidden paper wording:

- This is ground-truth relation accuracy.
- This is 3D mesh collision.
- This proves human visual quality.

## Table Placement Rules

| Paper Location | Allowed Variants | Notes |
|---|---|---|
| Abstract | Collision-gated Floor-Prior only | Use final T03/T04 rerun numbers only. |
| Main InstructScene table | Baseline, Collision-gated Floor-Prior, controlled baselines from T02 | Direct Repair may appear only if clearly labeled as ablation. |
| Ablation table | Direct Repair, Floor-Prior variants, SG-Guarded Overlap Repair | Do not mix CommonScenes metrics into this table. |
| External baseline/support table | CommonScenes Generic-Gate, ReSpace if T07 succeeds | Must disclose metric/protocol differences. |
| Supplementary | All variants allowed if labels are explicit | Include command, seed, evaluator, and data split. |

## Required Caption Fields

Every final table or figure must state:

1. Method variant.
2. Dataset and room split.
3. Scene count.
4. Seed or seed policy.
5. Evaluator.
6. Whether the metric is primary, safety, or diagnostic.
7. Whether the result is from final T03 rerun.

## Open Items Before Gate A

- [ ] Freeze independent evaluator protocol for T01.
- [ ] Freeze movement-matched baseline protocol for T02.
- [ ] Decide whether `max_repair_move=1.8` remains the only main-method value.
- [ ] Record the final commit hash used for T03 rerun.
- [ ] Confirm table names and locations in `docs/claim_to_table_map.md`.
