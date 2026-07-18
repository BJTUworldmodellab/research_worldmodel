# Main Results — Bedroom 162-Scene Layout-Only Validation

| Metric | Baseline | Primary | Aggressive | Minimal Move |
|--------|----------|---------|------------|-------------|
| SG-Layout Consistency | 0.9095 | 0.9133 | 0.9135 | 0.9139 |
| Layout Overlap IoU Sum | 0.2245 | 0.1309 | 0.1216 | 0.1511 |
| Overlap Reduction % | — | -41.7 | -45.8 | -32.7 |
| Mean Movement (m) | 0.0000 | 0.0772 | 0.0885 | 0.0508 |
| Max Movement (m) | 0.0000 | 0.2498 | 0.3474 | 0.1500 |
| Worse-Overlap Scenes (/162) | 0 | 0 | 0 | 0 |
| Worse-Consistency Scenes (/162) | 0 | 0 | 0 | 0 |
| Failures | 0 | 0 | 0 | 0 |
| Skips (no baseline overlap) | 0 | 7 | 7 | 7 |
| Rollbacks | 0 | 0 | 0 | 0 |

## Configs
- **baseline**: Baseline (eval-only, no repair)
- **s0075_d025_i050**: Primary (step=0.075, max_disp=0.25, iter=50)
- **s0075_d035_i050**: Aggressive (step=0.075, max_disp=0.35, iter=50)
- **s0025_d015_i025**: Minimal movement (step=0.025, max_disp=0.15, iter=25)