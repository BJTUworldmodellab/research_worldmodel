# Final Results — Bedroom 162-Scene Layout-Only Validation (Corrected)

**Generated**: 2026-07-18 (corrected from 2026-07-08)

## One-Line Conclusion

Repair v0 (overlap reduction with SG consistency guard) reduces layout overlap by **32.7%–45.8%** across 162 bedroom validation scenes while **improving** SG-layout consistency from 0.9095 to 0.9133–0.9139, with **zero worse-overlap or worse-consistency scenes** across all 1,296 repairs (8 configs × 162 scenes).

The strict single-variable sweep (7 configs, 1,134 repairs) identifies **s0050_d025_i050** as the new recommended primary configuration — it strictly dominates the original central config s0075_d025_i050 on all three objectives (overlap reduction, SG consistency, and mean movement).

## What's New (2026-07-18 Correction)

- **5 new configurations** added: s0025_d025_i050, s0050_d025_i050, s0075_d015_i050, s0075_d025_i025, s0075_d025_i075 (810 new repair runs)
- **Strict single-variable sweep** completed: 7 configs systematically varying step size, displacement cap, and iteration count independently
- **s0050_d025_i050 dominates s0075_d025_i050** on all three Pareto objectives (lower overlap, higher consistency, lower movement)
- **Iteration convergence confirmed**: i=25, i=50, i=75 produce identical per-scene metrics and repaired bbox arrays. No benefit observed beyond 25 iterations.
- **Displacement cap monotonic**: overlap decreases and movement increases monotonically with cap from 0.15 to 0.35
- **Pareto front** (full 7-config strict set): s0075_d035_i050, s0050_d025_i050, s0025_d025_i050, s0075_d015_i050

## File Index

| File | Description |
|------|-------------|
| [main_results_table.csv](main_results_table.csv) | Paper-ready results table — 9 rows (baseline + 8 configs) |
| [main_results_table.md](main_results_table.md) | Paper-ready results with strict sweep + supplementary tables |
| [per_scene_audit_summary.csv](per_scene_audit_summary.csv) | Per-scene deltas for all 8 repair configs (162 rows × 36 columns) |
| [claim_boundaries.md](claim_boundaries.md) | Scope, limitations, and metric naming conventions |
| [reproducibility.md](reproducibility.md) | Commands, environment, git, and data paths |
| [strict_one_factor_metrics_aggregate.csv](strict_one_factor_metrics_aggregate.csv) | Exact unrounded aggregate metrics for all 9 rows |
| [strict_one_factor_leaderboard.csv](strict_one_factor_leaderboard.csv) | Ranked leaderboard by overlap reduction |
| [strict_one_factor_pareto.csv](strict_one_factor_pareto.csv) | Pareto front members (new_5 and full_7_configs) |
| [strict_one_factor_analysis.md](strict_one_factor_analysis.md) | Detailed single-variable sweep analysis and dominance proof |

## Configs

| Config ID | Role | Step | MaxDisp | Iter | Analysis Group | Pareto Status |
|-----------|------|------|---------|------|---------------|---------------|
| `baseline` | Reference (no repair) | — | — | — | reference | reference |
| `s0075_d035_i050` | Max reduction | 0.075 | 0.35 | 50 | strict_one_factor | frontier |
| **`s0050_d025_i050`** ★ | **Recommended primary** | **0.050** | **0.25** | **50** | **strict_one_factor** | **frontier** |
| `s0025_d025_i050` | Best consistency | 0.025 | 0.25 | 50 | strict_one_factor | frontier |
| `s0075_d015_i050` | Best movement | 0.075 | 0.15 | 50 | strict_one_factor | frontier |
| `s0075_d025_i050` | Original central (dominated) | 0.075 | 0.25 | 50 | strict_one_factor | dominated |
| `s0075_d025_i025` | Iteration sweep | 0.075 | 0.25 | 25 | strict_one_factor | dominated |
| `s0075_d025_i075` | Iteration sweep | 0.075 | 0.25 | 75 | strict_one_factor | dominated |
| `s0025_d015_i025` | Minimal movement | 0.025 | 0.15 | 25 | supplementary_tradeoff | not_in_strict_sweep |

## Key Metrics

| Metric | Baseline | s0050_d025_i050 ★ | s0075_d035_i050 | s0025_d025_i050 | s0075_d015_i050 |
|--------|----------|-------------------|----------------|----------------|----------------|
| SG-Layout Consistency | 0.9095 | 0.9134 | 0.9135 | 0.9137 | 0.9133 |
| Layout Overlap IoU Sum | 0.2245 | 0.1287 | 0.1216 | 0.1347 | 0.1507 |
| Overlap Reduction % | — | 42.7 | 45.8 | 40.0 | 32.9 |
| Mean Movement (m) | 0.000 | 0.075 | 0.089 | 0.070 | 0.057 |

## Claim Boundaries (Summary)

- **This is layout-only / bbox-level validation** — no 3D collision detection, no rendering.
- **SG-layout consistency is NOT official relation accuracy** — no GT relations in export; self-consistency against generated scene graph edges.
- **Not a SOTA comparison** — not directly comparable to ReSpace, SDGScenes, or other methods without equivalent bbox-level baselines.
- **Bedroom only** — dining room and living room not yet evaluated.
- **Room OOB = NA** — no room geometry in export.

See [claim_boundaries.md](claim_boundaries.md) for full details.

## Data Paths

| Artifact | Path (relative to InstructScene repo) |
|----------|--------------------------------------|
| Baseline export (162 scenes) | `outputs/official_baseline/bedroom_export_162scene_seed42/` |
| Repair output (new 5 configs) | `outputs/ablations/strict_one_factor_20260718_seed42/` |
| Repair output (historical 3 configs) | `outputs/ablations/repair_v0_validation_162scene_seed42_noworse/` |

## Git

- **Branch**: `param-ablation-layout-repair` (InstructScene upstream)
- **HEAD**: `70be515`
- **Repository**: InstructScene (Chenguo Lin, ICLR 2024 spotlight)

## Scale

- **Strict one-factor sweep**: 7 configs × 162 scenes = 1,134 repairs
- **Supplementary trade-off**: 1 config × 162 scenes = 162 repairs
- **Total verified**: 8 configs × 162 scenes = 1,296 repairs
- **New in this revision**: 5 configs × 162 scenes = 810 repairs
- **0 failures, 0 rollbacks, 0 worse-overlap scenes** across all 1,296 repairs
