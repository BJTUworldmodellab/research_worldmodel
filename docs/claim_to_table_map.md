# Claim-to-Table Map

Date: 2026-07-27  
Status: T05 draft freeze  
Purpose: map each paper claim to the exact method variant, evaluator, table,
and evidence boundary.

## Rule

No claim may enter the abstract, introduction, conclusion, or figure caption
unless it can be traced to:

1. a method variant in `docs/method_variant_matrix.md`;
2. a frozen config in `configs/paper_main.yaml`;
3. a final T03 rerun result directory;
4. a final T04 statistical summary when the claim is quantitative.

Existing numbers below are **current evidence anchors**, not final submission
numbers until T03/T04 reruns are complete.

## C1: InstructScene Explicit Relation Repair

| Field | Value |
|---|---|
| Claim ID | C1 |
| Claim status | Strong but must be rerun under T01 independent evaluator |
| Method variant | `collision_gated_floor_prior` |
| Dataset | InstructScene bedroom, livingroom, diningroom validation splits |
| Primary metric | selected-relation accuracy |
| Safety metric | mesh-collision pair rate |
| Current evidence source | `docs/relation_aware_claim_validation_matrix.md` |
| Final table target | Main Table 1 |
| Required final artifacts | `results/independent_eval/summary.csv`, T03 rerun manifest, T04 bootstrap statistics |

Current evidence anchor:

| Room | Baseline acc | Collision-gated acc | Gated gain | Baseline mesh pair rate | Gated mesh pair rate |
|---|---:|---:|---:|---:|---:|
| bedroom | 0.7388 | 0.8449 | +0.1061 | 0.070244 | 0.064878 |
| livingroom | 0.5510 | 0.6871 | +0.1361 | 0.031257 | 0.030540 |
| diningroom | 0.5948 | 0.7212 | +0.1264 | 0.034229 | 0.033154 |

Allowed wording:

> Collision-gated Floor-Prior improves selected-relation accuracy across the
> three InstructScene room splits while reducing mesh-collision pair rate.

Forbidden wording:

- The method solves all language constraints.
- The method handles implicit commonsense.
- Direct Repair numbers are the main-method numbers.

## C2: Cross-Generator Applicability

| Field | Value |
|---|---|
| Claim ID | C2 |
| Claim status | Moderate support; must remain separate from InstructScene main metric |
| Method variant | `commonscenes_generic_gate` |
| Dataset | CommonScenes bedroom, livingroom, diningroom, library |
| Primary metric | generic geometric relation total |
| Safety metrics | collision penalty, changed-box ratio, mean movement, SSIM, GLB Chamfer |
| Diagnostic metric | official CommonScenes Total |
| Current evidence source | `docs/commonscenes_experiment_pack_20260713/commonscenes_generic_repair_experiment_report.md` |
| Final table target | External Support Table / Supplementary Table |
| Required final artifacts | CommonScenes rerun manifest, no-official-search summaries, disclosure row for official score drop |

Current evidence anchor:

| Room | Scenes | Baseline generic total | Repaired generic total | Delta | Collision penalty change |
|---|---:|---:|---:|---:|---|
| bedroom | 162 | 0.981312 | 0.984370 | +0.003058 | 164.012 -> 161.487 |
| livingroom | 52 | 0.970915 | 0.973113 | +0.002198 | 54.798 -> 51.841 |
| diningroom | 69 | 0.968892 | 0.970467 | +0.001575 | 103.200 -> 99.130 |
| library | 56 | 0.958588 | 0.964019 | +0.005431 | 72.028 -> 68.498 |

Mandatory disclosure:

> In bedroom, the official CommonScenes Total decreases from 0.9732 to 0.9696.

Allowed wording:

> CommonScenes Generic-Gate shows small but consistent generic geometric
> relation gains and lower collision penalty across four room types.

Forbidden wording:

- The method improves the official CommonScenes metric.
- The method fully outperforms CommonScenes.
- The CommonScenes metric is the same as InstructScene selected-relation accuracy.

## C3: Safety Ablation

| Field | Value |
|---|---|
| Claim ID | C3 |
| Claim status | Safety ablation only |
| Method variant | `sg_guarded_overlap_repair` |
| Dataset | 162 bedroom layout-only scenes |
| Primary metric | oriented-box overlap reduction |
| Protected metric | SG-layout consistency |
| Current evidence source | uploaded bedroom layout ablation package and reports |
| Final table target | Ablation / Supplementary |

Allowed wording:

> SG-Guarded Overlap Repair reduces oriented-box overlap on 162 bedroom
> layout-only scenes while preserving protected SG-layout consistency.

Forbidden wording:

- This is ground-truth relation accuracy.
- This is 3D mesh collision.
- This proves human visual quality.

## C4: Visual Quality / Low-Disturbance Claim

| Field | Value |
|---|---|
| Claim ID | C4 |
| Claim status | Low-disturbance only until T06 is complete |
| Method variants | `collision_gated_floor_prior`, `commonscenes_generic_gate` |
| Metrics currently allowed | SSIM, PSNR, changed-pixel ratio, GLB Chamfer, movement |
| Missing evidence | human preference / failure-rate study |
| Final table target | Supplementary visual/geometric stability table |

Allowed wording before T06:

> Repairs produce small average rendered and geometric perturbations.

Forbidden wording before T06:

- Visual quality is better.
- Humans prefer repaired scenes.
- Repairs are perceptually superior.

## C5: External Strong Baselines

| Field | Value |
|---|---|
| Claim ID | C5 |
| Claim status | Not a main superiority claim yet |
| Candidate external baseline | ReSpace |
| Required task | T07 same-protocol baseline |
| Current status | partial / feasibility only |
| Final table target | Only if protocol alignment succeeds |

Allowed wording now:

> ReSpace is a relevant external method and has been partially investigated.

Forbidden wording now:

- We outperform ReSpace.
- The partial ReSpace run is a full fair baseline.

## Final Paper Table Plan

| Table | Purpose | Allowed Variants | Required Before Use |
|---|---|---|---|
| Main Table 1 | InstructScene main result | Baseline, Collision-gated Floor-Prior, T02 movement-matched baselines | T01, T02, T03, T04 |
| Table 2 | Main-method ablation | Direct Repair, Floor-Prior variants, collision gate variants | T03, T04 |
| Table 3 | External support | CommonScenes Generic-Gate; ReSpace only if T07 succeeds | T03 for CommonScenes, T07 for ReSpace |
| Table 4 | Low-disturbance / safety | movement, collision, SSIM, Chamfer | T03, T04; T06 if making preference claims |
| Supplementary Table S1 | Per-room and per-seed details | All clearly labeled variants | Full manifest and reproducible commands |

## Gate A Checklist for This Map

- [ ] `configs/paper_main.yaml` reviewed by A/B/C.
- [ ] Method labels in all existing drafts updated to match this file.
- [ ] T01 protocol points to the exact primary metrics above.
- [ ] T02 baselines are added to Main Table 1 plan.
- [ ] C and paper writer agree not to use visual-preference wording before T06.
