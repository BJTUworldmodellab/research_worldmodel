# Relation-Aware InstructScene Experiment Archive

Created: 2026-05-30T14:49:40

This folder gathers the experiment evidence needed for the Relation-Aware InstructScene paper draft. It contains raw remote eval outputs, local summary tables, visual assets, docs, and analysis/rendering scripts.

## Top-level contents

| Folder | Files | Size MB | Purpose |
|---|---:|---:|---|
| `docs` | 13 | 0.07 | Paper-facing experiment notes, claim boundaries, and baseline status. |
| `local_results` | 187 | 316.67 | Local processed result tables and synced JSON outputs. |
| `local_visuals` | 165 | 34.40 | HTML galleries, rendered figures, mesh diagnostics, and visual assets. |
| `remote_eval_outputs` | 170 | 318.50 | Raw eval JSON/TXT copied from the remote InstructScene output tree. |
| `remote_floor_prior_showcase` | 46 | 18.02 | Remote-rendered real 3D-FUTURE floor-prior showcase files. |
| `scripts` | 11 | 0.07 | Analysis, sync, rendering, and table-generation scripts. |

## Most useful entry points

- `local_results/tables/floor_prior_results.csv`: main floor-prior relation and mesh table.
- `local_results/tables/floor_prior_gated_results.csv`: collision-gated relation/mesh results.
- `local_results/tables/floor_prior_mesh_results.csv`: mesh-focused table for paper claims.
- `local_results/tables/visual_quality_real_mesh.csv`: real-mesh visual diagnostics.
- `local_results/tables/strong_baseline_feasibility.csv`: fair baseline status table.
- `local_visuals/floor_prior_showcase.html`: 15-example floor-prior real mesh showcase.
- `local_visuals/a_conf_visual_quality.html`: visual diagnostics dashboard.
- `docs/relation_aware_visual_quality_and_baseline_update.md`: concise update on visual quality and baseline evidence.

## Claim boundary

The archive supports the conservative claim that floor-prior relation repair improves explicit spatial relation satisfaction while preserving object height and controlling mesh collision under the FCL pair-rate metric. It does not prove superiority over ReSpace/SDGScenes or universal human-perceived visual quality improvement.

## Excluded intentionally

Raw datasets, checkpoints, and environments are not copied here because they are large third-party assets rather than experiment outputs.

## Integrity

Use `checksums_sha256.txt` to verify copied files.
