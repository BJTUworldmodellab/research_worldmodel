# EG13 anonymous reproducibility report

Date: 2026-08-25  
State: `EG13_ANONYMOUS_REPRO_PASS`

## Technical summary

The anonymous package independently rebuilds the paper's three quantitative tables from frozen artifacts using Python's standard library only. It passes grain, coverage, denominator, numerical-reconciliation, per-object movement-fairness, generic-budget, evaluator-smoke, manifest, semantic-layout-integrity, and anonymity checks. This is sufficient for layout-to-statistics reproduction. It is not a fresh end-to-end generator reproduction because third-party datasets, checkpoints, environments, and the original room-level generator JSON files are not redistributed.

## Package

- Directory: `artifacts/eurographics2027/eg13_anonymous_repro/`
- ZIP: `artifacts/eurographics2027/eg13_anonymous_repro.zip`
- ZIP SHA-256: `9315e98e2dd4d7035097e91561aaf1469f71da1960eb07bc3f8ebb68c1d41002`
- ZIP size: 1,699,708 bytes
- Manifested files excluding `MANIFEST.json`: 28

## One-command checks

```bash
python scripts/reproduce_main_table.py
python scripts/smoke_test.py
```

Both commands were executed from the packaged directory with the bundled Python runtime and returned `PASS`. Neither command imports project packages or third-party libraries.

## Data grain and completeness

| Check | Result |
|---|---:|
| EG05 per-scene rows | 1,062 |
| EG06 per-scene rows | 3,186 |
| Unique scenes | 531 |
| Target relations | 808 |
| Missing targets retained in denominator | 93 |
| Unsupported targets | 0 |
| Duplicate scene/variant keys | 0 |
| EG05 variant-coverage errors | 0 |
| EG06 variant-coverage errors | 0 |

Expected grain is one row per `(scene_id, layout_variant)`: two variants in EG05 and six variants in EG06. All 162 bedroom, 192 living-room, and 177 dining-room scenes have full expected coverage.

## Calculation reconciliation

| Metric | Recomputed value | Frozen paper value | Result |
|---|---:|---:|---|
| Original baseline relation accuracy | 0.6349009901 | 0.6349009901 | PASS |
| Collision-gated Floor-Prior accuracy | 0.6398514851 | 0.6398514851 | PASS |
| Three-seed random mean | 0.6254125413 | 0.6254125413 | PASS |
| Main minus random mean | 1.443894 pp | 1.443894 pp | PASS |
| Canonical paired 95% CI | [0.745342, 2.200538] pp | [0.745342, 2.200538] pp | PASS |
| Original mesh collision pairs | 1,075 | 1,075 | PASS |
| Selected-main mesh collision pairs | 1,061 | 1,061 | PASS |
| Gate repair/fallback | 492 / 39 | 492 / 39 | PASS |

The original-baseline and generic-optimizer intervals still include zero. The reproducibility pass does not widen the paper claim.

## Movement fairness and budget checks

The package reconstructs horizontal displacement from the augmented layouts relative to the per-scene baseline, matched by stable object index.

| Check | Comparisons | Failures | Maximum discrepancy |
|---|---:|---:|---:|
| Each random object's movement magnitude equals the main object's magnitude | 16,599 | 0 | 4.44e-16 m |
| Each generic-optimizer object's movement stays within the main object's movement budget | 5,533 | 0 | 0 m excess |

This directly verifies the per-object fairness claim rather than relying only on per-scene total or maximum movement summaries.

## Anonymous-package integrity

- Machine-specific Windows and `/root` paths: 0 findings.
- Cloud host names and public repository identity: 0 findings.
- E-mail addresses, PAT/API-key patterns, and private-key markers: 0 findings.
- Public commit and branch anchors: withheld for double-blind review.
- The semantic SHA-256 of the `layouts` arrays is identical before and after provenance sanitization.
- Container hashes may differ because metadata paths and repository anchors are sanitized; the package manifest records the hashes actually distributed.

## Overall assessment

`Ready to share` as an anonymous layout-to-statistics artifact, subject to the submission system's supplemental-material size and file-type checks. `Share with caveats` for any claim of full generator reproduction because the original generator inputs and third-party assets remain unavailable in the lightweight package.

## Recommended next steps

1. After a fresh paper PDF is compiled, rerun the table script and compare the generated CSVs with every numeric table cell.
2. Give the ZIP to an uninvolved human reviewer and record the interpreter version, OS, commands, runtime, and any ambiguity.
3. Do not publish the package in the identity-bearing public repository until the double-blind anonymity decision is resolved.
