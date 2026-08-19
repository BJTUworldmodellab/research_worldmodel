# EG-04 Freeze Decision Record

Date: 2026-08-05
Task: EG-04 freeze final method, configuration, and code version
Decision owner: A + C
Branch: `agent/eg01-eg02-eurographics2027`

## Decision

Freeze `Collision-gated Floor-Prior` as the only Eurographics 2027 main method.

Default configuration:

`floor_prior_max1.8_mesh_p2_close0.75_far1.6`

Method-code anchor:

`feb37414db42faec3d600b66d17186ed3da8a22e`

## Why This Decision Is Being Made Now

EG-01 closed the main-number identity problem, and EG-02 produced a usable
diagnostic human-review alignment result. The user explicitly instructed us to
skip EG-03, so CW-GCP does not have the required GO evidence to replace
Floor-Prior. To keep the submission path moving, EG-04 freezes the current
mainline and prevents further threshold or method drift before EG-05 to EG-08.

## What Is Frozen

| Item | Frozen value |
|---|---|
| Main method | Collision-gated Floor-Prior |
| Config ID | `floor_prior_max1.8_mesh_p2_close0.75_far1.6` |
| Generator | InstructScene |
| Edit space | bounded XZ floor-plane translation |
| Height policy | preserve object height |
| Safety gate | keep repair only when FCL mesh collision pairs do not increase |
| Current result anchor | 0.8163 / 0.6395 / 0.6729 |
| Current gain anchor | +7.76 / +8.84 / +7.81 pp |
| Weighted anchor | 70.4%, +8.2 pp |

## What Is Not Frozen As A Final Claim

The numbers above are current anchors, not final submission evidence. Before
final paper claims, the project still needs:

- EG-05 independent evaluator;
- EG-06 movement-matched baselines;
- EG-07 full frozen rerun;
- EG-08 paired scene-level confidence intervals.

## EG-03 Handling

EG-03 is recorded as `skipped_no_go` for this submission path.

Reason:

> The CW-GCP decision experiment was skipped, so there is no accepted evidence
> that CW-GCP should replace the default Floor-Prior method.

Consequence:

> CW-GCP may appear only as future work or a later ablation if someone runs a
> separately versioned protocol. It must not change the EG-04 main method.

## Change Control After EG-04

Allowed after this freeze:

- fix implementation bugs found by EG-05/EG-06/EG-07;
- rerun experiments from a new versioned config if a bug fix changes outputs;
- add independent evaluator, baselines, statistics, and reporting scripts.

Not allowed after this freeze:

- change relation thresholds to improve the table after seeing results;
- switch the main method to Direct Repair, CW-GCP, or CommonScenes;
- mix ungated, direct-repair, and gated numbers in the main result table;
- claim final statistical significance before EG-08.

## Handoff To Members

| Member | Next responsibility |
|---|---|
| A | Use this freeze as the input contract for EG-05 independent evaluator. |
| B | Use this freeze as the input contract for EG-06 baselines and EG-08 statistics. |
| C | Keep paper tables and wording tied to this freeze; update only via versioned replacement. |
| D | Review claims against this freeze and flag any method/metric mixing. |

## Evidence Files

- `configs/eurographics2027/paper_main.yaml`
- `docs/eurographics2027/eg04_method_variant_matrix_20260805.md`
- `manifests/eurographics2027/eg04_freeze_manifest.json`
- `docs/eurographics2027/claim_to_table_map_eg2027.md`
- `docs/eurographics2027/eg01_result_identity_closure_20260730.md`
- `docs/eurographics2027/eg02_auto_human_alignment_20260802.md`
