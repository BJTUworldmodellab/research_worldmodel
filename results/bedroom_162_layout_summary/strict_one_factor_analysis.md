# Strict One-Factor Ablation Analysis

**Date**: 2026-07-18
**Scope**: Bedroom layout-only validation, 162 scenes, seed 42
**Method**: Repair v0 — overlap reduction with SG consistency guard

## Design

The strict single-variable sweep varies one parameter at a time while holding the other two at the original central values (step=0.075, disp=0.25, iter=50).

| Sweep | Varied Parameter | Fixed Parameters | Configs |
|-------|-----------------|-----------------|---------|
| Step size | 0.025, 0.050, 0.075 | disp=0.25, iter=50 | s0025, s0050, s0075 |
| Displacement cap | 0.15, 0.25, 0.35 | step=0.075, iter=50 | d015, d025, d035 |
| Iterations | 25, 50, 75 | step=0.075, disp=0.25 | i025, i050, i075 |

## Results

### Step Size Sweep (disp=0.25, iter=50)

| Step | Overlap IoU | SG-Consistency | Mean Move (m) | Max Move (m) |
|------|------------|---------------|---------------|-------------|
| 0.025 | 0.1347 | 0.9137 | 0.0698 | 0.2500 |
| 0.050 | 0.1287 | 0.9134 | 0.0753 | 0.2500 |
| 0.075 | 0.1309 | 0.9133 | 0.0772 | 0.2498 |

Observation: Step=0.050 achieves the most effective overlap reduction among the three, with higher SG consistency and lower mean movement than step=0.075. The relationship is non-monotonic — step=0.050 outperforms step=0.075 on all three objectives.

### Displacement Cap Sweep (step=0.075, iter=50)

| Max Disp | Overlap IoU | SG-Consistency | Mean Move (m) | Max Move (m) |
|----------|------------|---------------|---------------|-------------|
| 0.15 | 0.1507 | 0.9133 | 0.0566 | 0.1500 |
| 0.25 | 0.1309 | 0.9133 | 0.0772 | 0.2498 |
| 0.35 | 0.1216 | 0.9135 | 0.0885 | 0.3474 |

Observation: As the displacement cap increases, overlap decreases monotonically and mean movement increases monotonically. The 0.35 cap achieves the most overlap reduction (45.8%) but with the largest movement (0.0885 m mean, 0.3474 m max).

### Iteration Sweep (step=0.075, disp=0.25)

| Iter | Overlap IoU | SG-Consistency | Mean Move (m) | Max Move (m) |
|------|------------|---------------|---------------|-------------|
| 25 | 0.1309 | 0.9133 | 0.0772 | 0.2498 |
| 50 | 0.1309 | 0.9133 | 0.0772 | 0.2498 |
| 75 | 0.1309 | 0.9133 | 0.0772 | 0.2498 |

Observation: All three produce identical per-scene metrics (0/162 diffs) and identical repaired bbox arrays (0/1134 npz arrays differ). No per-scene or aggregate benefit is observed beyond 25 iterations.

## Pareto Front

**Objectives**: minimize overlap IoU (more reduction), maximize SG consistency, minimize mean movement.

### Among the 5 New Configs

| Config | Overlap | Consistency | Movement | Strength |
|--------|---------|-------------|----------|----------|
| s0050_d025_i050 | 0.1287 | 0.9134 | 0.0753 | Best balance |
| s0025_d025_i050 | 0.1347 | 0.9137 | 0.0698 | Best consistency |
| s0075_d015_i050 | 0.1507 | 0.9133 | 0.0566 | Best movement |

s0075_d025_i025 and s0075_d025_i075 are dominated by s0050_d025_i050.

### Full 7-Config Strict Set

| Config | Overlap | Consistency | Movement | Strength |
|--------|---------|-------------|----------|----------|
| s0075_d035_i050 | 0.1216 | 0.9135 | 0.0885 | Best overlap reduction |
| s0050_d025_i050 | 0.1287 | 0.9134 | 0.0753 | Best balance (recommended) |
| s0025_d025_i050 | 0.1347 | 0.9137 | 0.0698 | Best consistency |
| s0075_d015_i050 | 0.1507 | 0.9133 | 0.0566 | Best movement |

s0075_d025_i050, s0075_d025_i025, s0075_d025_i075 are all dominated.

## Dominance Proof: s0050 vs s0075_d025_i050

| Objective | s0050_d025_i050 | s0075_d025_i050 | Winner |
|-----------|----------------|----------------|--------|
| Overlap IoU (minimize) | 0.128667271135559 | 0.130902372984452 | s0050 ✓ |
| SG-Consistency (maximize) | 0.913443123661705 | 0.913266756818672 | s0050 ✓ |
| Mean Movement (minimize) | 0.075295194928199 | 0.077182711875235 | s0050 ✓ |

**All three objectives strictly favor s0050.** The original central configuration s0075_d025_i050 is dominated.

## No-Worse Guarantee

All 1,296 repairs (8 × 162, of which 810 are from the 5 new configs in this revision) across all evaluated configurations:

- **0 rollbacks**: SG consistency never drops below baseline for any scene in any config
- **0 worse-overlap scenes**: Overlap never increases after repair
- **0 failures**: No NaN/Inf in any metric
- **7 skips per config**: Exactly 7 scenes have zero baseline overlap (consistent across all configs)

## Supplementary Trade-Off

s0025_d015_i025 (step=0.025, disp=0.15, iter=25) is NOT part of the strict single-variable sweep (varies two parameters). It achieves the lowest mean movement (0.0508 m) and highest SG consistency (0.9139) among all evaluated configurations, at the cost of the least overlap reduction (32.7%).
