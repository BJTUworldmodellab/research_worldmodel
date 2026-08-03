# EG-01 Result Identity and Number Consistency Closure

Date: 2026-07-30  
Status: RESULT IDENTITY FROZEN; final submission gates pending
Owner: A + C  
Base branch observed: `master` at `66b844d027ee0475e19434b121b684a025dd17a1`

## What EG-01 Fixes

EG-01 exists because the project has multiple similar-sounding variants whose
numbers are easy to mix:

- Floor-Prior
- Collision-gated Floor-Prior
- Direct Repair
- Collision-gated Direct Repair
- CommonScenes Generic-Gate
- SG-Guarded Overlap Repair

The Eurographics 2027 checklist states that the paper main method should be:

```text
Collision-gated Floor-Prior
floor_prior_max1.8_mesh_p2_close0.75_far1.6
```

This is not the same as the older Collision-gated Direct Repair identity.

## Main Result Identity

| Room | Gated relation accuracy | Relative gain | Gated mesh pair collision | Fallback |
|---|---:|---:|---:|---:|
| Bedroom | 81.63% | +7.76 pp | 0.068293 | 6 |
| Living room | 63.95% | +8.84 pp | 0.030959 | 14 |
| Dining room | 67.29% | +7.81 pp | 0.033615 | 15 |
| Weighted summary | 70.4% | +8.2 pp | — | — |

Machine-readable manifest:

```text
manifests/eurographics2027/eg01_main_method_manifest.json
```

## Important Correction

The values below must not be used as the Eurographics 2027 main Floor-Prior
result:

```text
0.8449 / 0.6871 / 0.7212
```

They belong to the aggressive Collision-gated Direct Repair ablation.

The older abstract wording:

```text
10.2, 14.3, and 13.4 absolute points
```

also does not match the current EG-01 gated Floor-Prior identity. The intended
abstract-level deltas are:

```text
7.8, 8.8, and 7.8 absolute points; weighted gain 8.2 points
```

## New EG-01 Files

```text
configs/eurographics2027/paper_main_eg2027.yaml
docs/eurographics2027/claim_to_table_map_eg2027.md
docs/eurographics2027/eg01_result_identity_closure_20260730.md
manifests/eurographics2027/eg01_main_method_manifest.json
scripts/check_eg01_result_identity.py
```

## Automatic Check

Run:

```bash
python scripts/check_eg01_result_identity.py --root .
```

The script checks that the EG-01 manifest, Eurographics claim map, and paper
draft agree on the current main-method identity. It also reports SHA256 hashes
for tracked files.

## Remaining EG-01 Work

- [ ] B/C should review paper tables and appendices after this branch lands.
- [ ] If SDGScenes defensive baseline data is uploaded, add it as a separate
      external-baseline audit item, not as a main Floor-Prior result.
- [ ] Once EG-07 produces final rerun outputs, replace current anchors with
      regenerated values and update manifest hashes.
- [ ] `git diff --check` must pass before merging.

