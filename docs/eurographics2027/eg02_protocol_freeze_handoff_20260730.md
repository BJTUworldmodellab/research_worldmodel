# EG-02 Protocol Freeze Handoff

Date: 2026-07-30  
Status: IN PROGRESS; A/D review failed kappa gate on 2026-08-02
Branch target: `agent/eg01-eg02-eurographics2027`

## What EG-02 Adds

EG-02 freezes the independent evaluation and human-review protocol before the
full experiments are rerun.

New files:

```text
evaluation/independent_protocol.md
docs/eurographics2027/eg02_human_review_protocol.md
annotations/eurographics2027/eg02_relation_annotation_template.csv
annotations/eurographics2027/eg02_sampling_plan.csv
annotations/eurographics2027/eg02_human_review_sample.csv
docs/eurographics2027/eg02_protocol_freeze_handoff_20260730.md
scripts/build_eg02_human_review_sample.py
scripts/check_eg02_protocol_files.py
scripts/compute_eg02_kappa.py
scripts/validate_eg02_human_review_sample.py
scripts/validate_eg02_sampling_plan.py
scripts/write_eg02_protocol_manifest.py
manifests/eurographics2027/eg02_protocol_manifest.json
```

## Frozen EG-02 Decisions

1. The independent evaluator must not import repair optimizer relation logic.
2. Object-instance matching is frozen from the baseline layout and reused for
   all compared variants.
3. Missing objects remain in the denominator for the primary end-to-end metric.
4. The primary metric is relation accuracy over all target relations.
5. The conditional metric over evaluated-only triples is diagnostic.
6. Human review requires at least 90 relations: 30 per room.
7. Cohen's kappa must be at least 0.70 before final automatic numbers are used.
8. The frozen human sample excludes unmapped predicate id `8` and does not
   include `far from`, because the current main Floor-Prior JSONs do not expose
   data-supported `far from` target triples.

## Status Against EG-02 Acceptance Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Independent evaluator must not import optimizer relation functions | Protocol frozen | `evaluation/independent_protocol.md` |
| Relation definitions, matching, thresholds, conflicts, missing objects | Protocol frozen | `evaluation/independent_protocol.md` |
| Human set at least 90 relations across three rooms | Frozen sample created | `annotations/eurographics2027/eg02_human_review_sample.csv` |
| Cohen's kappa threshold at least 0.70 | Protocol and checker frozen | `docs/eurographics2027/eg02_human_review_protocol.md`, `scripts/compute_eg02_kappa.py` |
| Protocol version, data hash, evaluator commit hash frozen | Partial | protocol version and protocol-file hashes frozen; data/evaluator hash pending EG-05 implementation |

EG-02 should remain `IN PROGRESS` until A and D review the protocol and the
actual sampled relation rows are filled.

2026-08-02 update: A/D labeled the 90-row sample, but agreement did not pass
the frozen kappa gate. See:

```text
docs/eurographics2027/eg02_human_review_result_20260802.md
results/eurographics2027/eg02_human_review/summary.json
```

## Hand-off to EG-05

EG-05 implementers should build the independent evaluator to this protocol.
Implementation must output:

```text
per_relation.csv
per_scene.csv
summary.csv
audit.json
```

Do not tune relation thresholds after seeing final method results. Any change
requires a new protocol version and rerun.
