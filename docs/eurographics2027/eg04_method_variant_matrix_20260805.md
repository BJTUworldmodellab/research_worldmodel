# EG-04 Method Variant Matrix

Date: 2026-08-05
Task: EG-04 freeze final method, configuration, and code version
Branch: `agent/eg01-eg02-eurographics2027`
Method-code anchor: `feb37414db42faec3d600b66d17186ed3da8a22e`

## Freeze Decision

EG-03 is skipped for the current Eurographics path, so CW-GCP is **not**
promoted. The only main method for the next experimental gate is:

`Collision-gated Floor-Prior`

Config ID:

`floor_prior_max1.8_mesh_p2_close0.75_far1.6`

The practical meaning is simple: after this point, EG-05 to EG-08 should test
this method instead of continuing to search for better thresholds.

## Variant Roles

| Variant | Role in paper | Can be main result? | Reason |
|---|---|---:|---|
| Collision-gated Floor-Prior | Main method | Yes | Positive relation gains and mesh-collision non-worsening gate. |
| Ungated Floor-Prior | Diagnostic ablation | No | Useful for showing effect before the safety gate, but mesh delta is slightly positive. |
| Direct Repair | Aggressive ablation | No | Larger relation gains but much larger moves; not the safety-facing method. |
| CommonScenes Generic-Gate | Cross-generator diagnostic support | No | Different generator and metric; official CommonScenes score remains diagnostic. |
| SG-Guarded Overlap Repair | Layout-only safety ablation | No | Measures overlap/SG consistency, not ground-truth relation accuracy. |
| CW-GCP | Skipped / future work | No | EG-03 was skipped, so there is no accepted decision evidence to replace Floor-Prior. |

## Main Result Anchor

These are not final statistical claims. They are the EG-01 identity anchor that
EG-07 must regenerate from the frozen configuration.

| Room | Baseline relation acc | Ungated Floor-Prior acc | Gated Floor-Prior acc | Gated gain | Baseline mesh pair | Gated mesh pair | Fallback |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8408 | 0.8163 | +0.0776 | 0.0702 | 0.068293 | 6 |
| Living room | 0.5510 | 0.6939 | 0.6395 | +0.0884 | 0.0313 | 0.030959 | 14 |
| Dining room | 0.5948 | 0.7286 | 0.6729 | +0.0781 | 0.0342 | 0.033615 | 15 |
| Weighted | — | — | 0.7040 | +0.0820 | — | — | — |

## Allowed Wording

> Collision-gated Floor-Prior is the frozen Eurographics 2027 main method. It
> improves realized explicit spatial-relation accuracy on the existing
> InstructScene bedroom, living-room, and dining-room validation splits while
> applying a mesh-collision non-worsening gate.

## Forbidden Wording

- Do not say CW-GCP is the main method.
- Do not use `0.8449 / 0.6871 / 0.7212` as Floor-Prior main results.
- Do not use `10.2 / 14.3 / 13.4 pp` as the main collision-gated gains.
- Do not claim superiority over ReSpace, SDGScenes, or CommonScenes official
  metrics without same-protocol evidence.
- Do not claim human visual quality improvement before a proper human study.

## Downstream Rule

Every EG-05, EG-06, EG-07, and EG-08 output should record:

| Required field | Why it matters |
|---|---|
| `code_commit` | Shows which frozen code produced the output. |
| `config_path` and `config_sha256` | Prevents silent threshold drift. |
| data source paths and scene counts | Prevents missing or duplicate scene claims. |
| seed or seed policy | Makes reruns comparable. |
| command, log path, and output path | Lets another member reproduce the run. |
| environment summary | Makes server/GPU/library differences visible. |

## EG-04 Status

EG-04 is complete only when the following files are committed together:

- `configs/eurographics2027/paper_main.yaml`
- `docs/eurographics2027/eg04_method_variant_matrix_20260805.md`
- `docs/eurographics2027/eg04_freeze_decision_record_20260805.md`
- `manifests/eurographics2027/eg04_freeze_manifest.json`
