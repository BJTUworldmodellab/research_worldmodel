# EG-04 Member Handoff

Date: 2026-08-05
Branch: `agent/eg01-eg02-eurographics2027`
Status: EG-04 accepted

## One-Sentence Version

EG-04 freezes `Collision-gated Floor-Prior` as the Eurographics 2027 main
method; EG-03 was skipped, so CW-GCP is not part of the main submission path.

## What Members Should Use

Use this file as the entry point:

`configs/eurographics2027/paper_main.yaml`

Main method:

`collision_gated_floor_prior`

Default config:

`floor_prior_max1.8_mesh_p2_close0.75_far1.6`

Config hash:

`052ACE5B295348483CE9B6110B5BD7933235424A55CC2108C966431E516829E2`

## What Members Should Not Do

- Do not switch the main method to CW-GCP.
- Do not switch the main method to Direct Repair.
- Do not tune thresholds after seeing EG-05/EG-06/EG-07/EG-08 results.
- Do not use `0.8449 / 0.6871 / 0.7212` as the Floor-Prior main result.
- Do not claim statistical significance before EG-08.

## Who Does What Next

| Member | Next task | Input file |
|---|---|---|
| A | EG-05 independent evaluator | `configs/eurographics2027/paper_main.yaml` |
| B | EG-06 movement-matched baselines and EG-08 statistics | `configs/eurographics2027/paper_main.yaml` |
| C | Keep paper text/tables aligned with frozen method | `docs/eurographics2027/eg04_method_variant_matrix_20260805.md` |
| D | Review claims against freeze boundaries | `docs/eurographics2027/eg04_freeze_decision_record_20260805.md` |

## How To Check The Freeze

Run:

```bash
python scripts/check_eg04_freeze.py
```

Expected output:

```text
EG-04 freeze check passed.
config_sha256=052ACE5B295348483CE9B6110B5BD7933235424A55CC2108C966431E516829E2
main_method=collision_gated_floor_prior
eg03_decision=skipped_no_go
```
