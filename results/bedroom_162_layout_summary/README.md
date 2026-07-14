# Final Results — Bedroom 162-Scene Layout-Only Validation

**Generated**: 2026-07-08

## One-Line Conclusion

Repair v0 (overlap reduction with SG consistency guard) reduces layout overlap by **32.7%–45.8%** across 162 bedroom validation scenes while **improving** SG-layout consistency from 0.9095 to 0.9133–0.9139, with **zero worse-overlap or worse-consistency scenes** across all 486 repairs (3 configs × 162 scenes).

## File Index

| File | Description |
|------|-------------|
| [main_results_table.csv](main_results_table.csv) | Paper-ready results table (CSV) |
| [main_results_table.md](main_results_table.md) | Paper-ready results table (Markdown) |
| [per_scene_audit_summary.csv](per_scene_audit_summary.csv) | Per-scene deltas for all 3 repair configs |
| [claim_boundaries.md](claim_boundaries.md) | Scope, limitations, and metric naming conventions |
| [reproducibility.md](reproducibility.md) | Commands, environment, git, and data paths |

## Data Paths

| Artifact | Path |
|----------|------|
| Baseline export (162 scenes) | `outputs/official_baseline/bedroom_export_162scene_seed42/` |
| Repair validation | `outputs/ablations/repair_v0_validation_162scene_seed42_noworse/` |
| Final summary | `outputs/ablations/final_bedroom_162_summary/` |

## Git

- **Branch**: `param-ablation-layout-repair`
- **HEAD**: `70be515`
- **Working tree**: clean
- **Repository**: `/path/to/InstructScene`

## Configs

| Config ID | Role | Step | MaxDisp | Iter |
|-----------|------|------|---------|------|
| `baseline` | Reference (no repair) | — | — | — |
| `s0075_d025_i050` | **Primary** | 0.075 | 0.25 | 50 |
| `s0075_d035_i050` | Aggressive (max reduction) | 0.075 | 0.35 | 50 |
| `s0025_d015_i025` | Minimal movement | 0.025 | 0.15 | 25 |

## Key Metrics

| Metric | Baseline | Primary | Aggressive | Minimal |
|--------|----------|---------|------------|---------|
| SG-Layout Consistency | 0.9095 | 0.9133 | 0.9135 | 0.9139 |
| Layout Overlap IoU Sum | 0.2245 | 0.1309 | 0.1216 | 0.1511 |
| Overlap Reduction % | — | -41.7% | -45.8% | -32.7% |
| Mean Movement (m) | 0.000 | 0.077 | 0.089 | 0.051 |

## Claim Boundaries (Summary)

- **This is layout-only / bbox-level validation** — no mesh collision, no rendering.
- **SG-layout consistency is NOT official relation accuracy** — no GT relations in export; this is self-consistency against generated scene graph edges.
- **Not a SOTA comparison** — not directly comparable to ReSpace, SDGScenes, or other methods without equivalent bbox-level baselines.
- **Bedroom only** — dining room and living room not yet evaluated.
- **Room OOB = NA** — no room geometry in export.

See [claim_boundaries.md](claim_boundaries.md) for full details.
