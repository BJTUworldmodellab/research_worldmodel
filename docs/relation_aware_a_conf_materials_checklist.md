# A-Conference Material Checklist

## Must-have experiment tables

- Main relation realization table: baseline vs direct y-fixed vs floor-prior.
- Mesh collision table: baseline vs direct y-fixed vs floor-prior.
- Movement / plausibility table: average repair movement, skipped repairs, overlap ratio.
- Room-wise breakdown: bedroom, living room, dining room.
- Claim validation matrix: what is supported, partially supported, and unsupported.

## Must-have qualitative assets

- Real 3D-FUTURE mesh before/after renders for each room.
- Height-fixed showcase page using v3 assets.
- At least one living-room example where relation improves and mesh collision does not increase.
- Diagnostic note explaining why the old living-room visual failed.

## Must-have method assets

- Algorithm description for direct y-fixed repair.
- Algorithm description for `floor_prior`.
- Pseudocode for candidate repair selection.
- Related-work-to-design mapping.

## Must-have honesty / reviewer-defense items

- Do not claim first relation-aware 3D scene generation.
- Do not claim universal visual-quality improvement.
- Do not claim implicit commonsense relation handling.
- Do not claim superiority over SDGScenes / ReSpace without a shared protocol.
- Explicitly state that current method targets horizontal spatial relations; support/contact/facing remain future work.

## Tonight handoff outputs

- `docs/relation_aware_related_work_to_algorithm.md`
- `docs/relation_aware_floor_plane_repair_fix.md`
- `docs/relation_aware_floor_prior_algorithm.md`
- `docs/relation_aware_a_conf_materials_checklist.md`
- `results/tables/floor_prior_results.csv`
- `results/tables/floor_prior_mesh_results.csv`
- `results/tables/floor_prior_gated_results.csv`
- `results/tables/floor_prior_per_relation_breakdown.csv`
- `results/tables/floor_prior_support_movement_diagnostics.csv`
- `results/tables/strong_baseline_feasibility.csv`
- `results/tables/visual_quality_real_mesh.csv`
- `results/tables/visual_quality_mesh_projection.csv`
- `visual/real_mesh_showcase.html`
- `visual/real_mesh_showcase_v3/`
- `visual/floor_prior_showcase.html`
- `visual/floor_prior_showcase/`
- `visual/a_conf_visual_quality.html`
- `visual/a_conf_floor_prior_results.html`
