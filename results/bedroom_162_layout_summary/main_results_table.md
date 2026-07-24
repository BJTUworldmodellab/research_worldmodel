# Main Results — Bedroom 162-Scene Layout-Only Validation (Corrected)

**Generated**: 2026-07-18

## A. Strict One-Factor Ablation

Baseline + 7 configs in the strict single-variable sweep.

| Metric | Baseline | s0075_d035_i050 | **s0050_d025_i050** ★ | s0025_d025_i050 | s0075_d015_i050 | s0075_d025_i050 | s0075_d025_i025 | s0075_d025_i075 |
|--------|----------|----------------|----------------------|----------------|----------------|----------------|----------------|----------------|
| SG-Layout Consistency | 0.9095 | 0.9135 | **0.9134** | 0.9137 | 0.9133 | 0.9133 | 0.9133 | 0.9133 |
| Layout Overlap IoU Sum | 0.2245 | 0.1216 | **0.1287** | 0.1347 | 0.1507 | 0.1309 | 0.1309 | 0.1309 |
| Overlap Reduction % | — | 45.8 | **42.7** | 40.0 | 32.9 | 41.7 | 41.7 | 41.7 |
| Mean Movement (m) | 0.0000 | 0.0885 | **0.0753** | 0.0698 | 0.0566 | 0.0772 | 0.0772 | 0.0772 |
| Max Movement (m) | 0.0000 | 0.3474 | **0.2500** | 0.2500 | 0.1500 | 0.2498 | 0.2498 | 0.2498 |
| Worse-Overlap Scenes (/162) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Worse-Consistency Scenes (/162) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Failures | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Skips (no baseline overlap) | 7 | 7 | 7 | 7 | 7 | 7 | 7 | 7 |
| Rollbacks | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Strict Pareto Status | reference | frontier | **frontier** | frontier | frontier | dominated | dominated | dominated |

**★ s0050_d025_i050 is the recommended primary configuration.** It strictly dominates the original central config s0075_d025_i050 on all three objectives: lower overlap IoU (0.1287 < 0.1309), higher SG-layout consistency (0.9134 > 0.9133), lower mean movement (0.0753 < 0.0772).

### Strict Pareto Front (minimize overlap, maximize consistency, minimize movement)

| Config | Overlap IoU | SG-Consistency | Mean Movement | Strength |
|--------|------------|---------------|---------------|----------|
| s0075_d035_i050 | 0.1216 | 0.9135 | 0.0885 | Best overlap reduction |
| s0050_d025_i050 | 0.1287 | 0.9134 | 0.0753 | Best balance (recommended) |
| s0025_d025_i050 | 0.1347 | 0.9137 | 0.0698 | Best consistency |
| s0075_d015_i050 | 0.1507 | 0.9133 | 0.0566 | Best movement preservation |

### Iteration Convergence

i=25, i=50, i=75 produce identical per-scene metrics (0/162 diffs) and identical repaired bbox arrays (0/1134 arrays differ) across all scenes. No per-scene or aggregate benefit is observed beyond 25 iterations.

### Single-Variable Sweeps

**Step size** (disp=0.25, iter=50): 0.025 → 0.050 → 0.075. Step=0.050 is the most effective: more overlap reduction and higher consistency than step=0.075, with less movement.

**Displacement cap** (step=0.075, iter=50): 0.15 → 0.25 → 0.35. Overlap decreases monotonically; movement increases monotonically.

**Iterations** (step=0.075, disp=0.25): 25 → 50 → 75. All three produce identical results.

## B. Supplementary Trade-Off Configuration

| Metric | s0025_d015_i025 |
|--------|----------------|
| SG-Layout Consistency | 0.9139 |
| Layout Overlap IoU Sum | 0.1511 |
| Overlap Reduction % | 32.7 |
| Mean Movement (m) | 0.0508 |
| Max Movement (m) | 0.1500 |
| Worse-Overlap Scenes | 0 |
| Worse-Consistency Scenes | 0 |
| Failures | 0 |
| Skips | 7 |
| Rollbacks | 0 |

s0025_d015_i025 is a supplementary trade-off configuration (step=0.025, disp=0.15, iter=25). It is NOT part of the strict single-variable sweep because it varies two parameters simultaneously. It achieves the lowest mean movement (0.0508 m) and the highest SG-layout consistency (0.9139) across all evaluated configurations.

## Configs Reference

| Config ID | Step | Max Disp | Iter | Analysis Group | Role |
|-----------|------|----------|------|---------------|------|
| baseline | — | — | — | reference | Reference (eval-only, no repair) |
| s0075_d035_i050 | 0.075 | 0.35 | 50 | strict_one_factor | Max overlap reduction |
| **s0050_d025_i050** ★ | **0.050** | **0.25** | **50** | **strict_one_factor** | **Recommended primary** |
| s0025_d025_i050 | 0.025 | 0.25 | 50 | strict_one_factor | Best consistency |
| s0075_d015_i050 | 0.075 | 0.15 | 50 | strict_one_factor | Best movement |
| s0075_d025_i050 | 0.075 | 0.25 | 50 | strict_one_factor | Original central (dominated) |
| s0075_d025_i025 | 0.075 | 0.25 | 25 | strict_one_factor | Iteration sweep (dominated) |
| s0075_d025_i075 | 0.075 | 0.25 | 75 | strict_one_factor | Iteration sweep (dominated) |
| s0025_d015_i025 | 0.025 | 0.15 | 25 | supplementary_tradeoff | Minimal movement |

## Data Scale

- **New runs** (this revision): 5 configs × 162 scenes = 810 repairs
- **Strict one-factor sweep**: 7 configs × 162 scenes = 1,134 repairs
- **Total verified**: 8 configs × 162 scenes = 1,296 repairs
- **0 failures, 0 rollbacks, 0 worse-overlap scenes** across all 1,296 repairs
