# Anonymous EG2027 reproducibility package

This package rebuilds the three quantitative paper tables from the frozen 531-scene evidence and runs a minimal independent-evaluator smoke test. It requires Python 3.9 or later and no third-party packages.

## One-command table reproduction

```bash
python scripts/reproduce_main_table.py
```

Expected terminal status: `PASS`. Generated machine- and human-readable outputs are written under `output/reproduction/`.

## Minimal evaluator smoke test

```bash
python scripts/smoke_test.py
```

Expected terminal status: `PASS` with four evaluated relation rows.

## Scope and claim boundary

- Population: the frozen existing-protocol validation set (162 bedrooms, 192 living rooms, 177 dining rooms; 531 scenes total).
- Primary denominator: 808 explicit target relations. Missing targets remain in the denominator; unsupported targets are counted and expected to be zero.
- Main method: collision-gated Floor-Prior applied after a fixed pretrained InstructScene generator.
- Supported comparison: the main method exceeds the mean of three per-object movement-matched random controls under the frozen paired scene-level relation-weighted bootstrap protocol.
- Unsupported comparisons: the confidence intervals versus the original generator and the generic optimizer include zero. This package does not establish superiority to ReSpace, SDGScenes, or any cross-protocol method.

## Anonymous sanitization

Machine-specific paths, repository identity, user identifiers, e-mail addresses, cloud-host identifiers, credentials, and public commit anchors are removed or withheld. For JSON layout containers, `MANIFEST.json` records a semantic hash over the `layouts` array before and after sanitization; those hashes must remain identical. Container file hashes differ when provenance metadata is sanitized.

Third-party datasets, pretrained checkpoints, and the original room-level generator output JSON files are not redistributed. Consequently, this package supports layout-to-statistics reconstruction and evaluator smoke testing, not a fresh end-to-end generator run.
