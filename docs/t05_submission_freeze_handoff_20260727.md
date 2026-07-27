# T05 Handoff: Main Method and Configuration Freeze

Date: 2026-07-27  
Owner track: A - method and evaluation  
GitHub target: `BJTUworldmodellab/research_worldmodel`

## What Was Started

T05 has been started by adding a submission-facing method/configuration freeze.
The purpose is to let A/B/C work in parallel without mixing method variants or
metrics.

New files:

```text
configs/paper_main.yaml
docs/method_variant_matrix.md
docs/claim_to_table_map.md
docs/t05_submission_freeze_handoff_20260727.md
```

## Core Decision

The paper main method is frozen as:

```text
Collision-gated Floor-Prior
```

It should be the only method named in the abstract-level quantitative claim
unless a future T05 revision explicitly changes the freeze.

## Variant Roles

| Variant | Role |
|---|---|
| Collision-gated Floor-Prior | Main InstructScene method |
| Direct Repair | Aggressive ablation / upper-bound style comparison |
| CommonScenes Generic-Gate | Cross-generator external-support experiment |
| SG-Guarded Overlap Repair | Layout-only safety ablation |

## What Other People Should Read First

For B, experiment execution:

1. `configs/paper_main.yaml`
2. `docs/method_variant_matrix.md`
3. `docs/claim_to_table_map.md`

For C, paper writing and figure planning:

1. `docs/claim_to_table_map.md`
2. `docs/method_variant_matrix.md`
3. `configs/paper_main.yaml`

For T01/T02 implementers:

1. `configs/paper_main.yaml`
2. `docs/method_variant_matrix.md`
3. `docs/claim_to_table_map.md`

## Current Evidence Anchors

These are useful for orientation, but they are not final submission numbers
until T03/T04 reruns are complete.

| Evidence Area | Current Source |
|---|---|
| InstructScene relation and mesh-collision claims | `docs/relation_aware_claim_validation_matrix.md` |
| Floor-prior algorithm | `docs/relation_aware_floor_prior_algorithm.md` |
| CommonScenes generic-gate results | `docs/commonscenes_experiment_pack_20260713/commonscenes_generic_repair_experiment_report.md` |
| Repository/data gap audit | `docs/research_worldmodel_repo_gap_report_20260717.md` |

## Immediate Next Steps for A

1. Review `configs/paper_main.yaml` and confirm the main method name.
2. Decide whether `max_repair_move=1.8` remains the only main-method setting.
3. Draft `evaluation/independent_protocol.md` for T01.
4. Draft `docs/baseline_protocol.md` for T02.
5. Mark the T05 files as reviewed once A/B/C agree on labels.

## Immediate Next Steps for B

1. Build the T03 run manifest around `configs/paper_main.yaml`.
2. Ensure every run writes method variant, room, scene count, seed, evaluator,
   command, log path, and commit hash.
3. Do not generate final paper tables from old result folders unless they are
   clearly labeled as current evidence anchors.

## Immediate Next Steps for C

1. Use `docs/claim_to_table_map.md` to update paper claim wording.
2. Remove or soften visual-preference wording until T06 is complete.
3. Keep CommonScenes official score as diagnostic only.
4. Make every table caption state method variant and evaluator.

## Open Risks

- The independent evaluator from T01 is not implemented yet.
- Same-budget control baselines from T02 are not implemented yet.
- Final T03 rerun has not happened from this freeze.
- T04 confidence intervals for the final rerun are not available yet.
- Visual quality claims remain low-disturbance only until T06.

## Gate A Checklist

- [ ] A/B/C agree on the method variant names.
- [ ] `configs/paper_main.yaml` is reviewed.
- [ ] `docs/method_variant_matrix.md` is reviewed.
- [ ] `docs/claim_to_table_map.md` is reviewed.
- [ ] T01 independent evaluator protocol is frozen.
- [ ] T02 movement-matched baseline protocol is frozen.
- [ ] Main method, data split, seeds, and metrics are no longer changed without a versioned T05 update.
