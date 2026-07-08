# Mesh Collision and Visual Quality Experiments

Date: 2026-05-29

## Setup

The mesh-collision run re-executed the main parsed Relation-Aware InstructScene setting on bedroom, living-room, and dining-room validation splits. The script now saves retrieved `object_model_jids`, reloads 3D-FUTURE meshes, and evaluates mesh intersections using `trimesh.collision.CollisionManager` backed by `python-fcl`. It also exports top-down mesh-projection PNGs for improved before/after examples.

Command family: `relation_aware_generate_sg.py ... --relation_source parsed --repair_passes 2 --close_distance 0.75 --far_distance 1.6 --mesh_collision --render_examples 8`.

## Direct Repair Mesh Collision

| Room | Scenes | Relation acc base | Relation acc repair | Mesh pair rate base | Mesh pair rate repair | Delta | Mesh scene rate base | Mesh scene rate repair |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bedroom | 162 | 0.7388 | 0.8735 | 0.070244 | 0.070244 | 0.000000 | 0.5494 | 0.5494 |
| livingroom | 192 | 0.5510 | 0.7415 | 0.031257 | 0.031616 | 0.000359 | 0.8385 | 0.8490 |
| diningroom | 177 | 0.5948 | 0.7844 | 0.034229 | 0.034766 | 0.000537 | 0.7458 | 0.7627 |

Interpretation: direct relation repair does not prove mesh-level collision reduction. Bedroom is exactly tied under pair rate; living room and dining room show very small increases. This blocks the unsafe claim "mesh-level collision is lower" for the direct variant.

## Collision-Gated Variant

The collision-gated variant keeps the repaired scene only when FCL mesh collision pairs do not increase; otherwise it falls back to the baseline layout for that scene. This is a conservative verifier-selection layer, not a new benchmark.

| Room | Baseline acc | Direct repair acc | Collision-gated acc | Gated gain | Baseline mesh pair rate | Gated mesh pair rate | Fallback scenes |
|---|---:|---:|---:|---:|---:|---:|---:|
| bedroom | 0.7388 | 0.8735 | 0.8449 | +0.1061 | 0.070244 | 0.064878 | 9 |
| livingroom | 0.5510 | 0.7415 | 0.6871 | +0.1361 | 0.031257 | 0.030540 | 14 |
| diningroom | 0.5948 | 0.7844 | 0.7212 | +0.1264 | 0.034229 | 0.033154 | 13 |

Interpretation: the gated variant supports a safer paper claim: relation satisfaction still improves substantially while mesh collision pair rate does not increase and in fact decreases under the FCL pair-rate metric. This is the right variant to use if the paper wants a mesh-validity claim.

## Visual Quality Materials

Generated mesh-projection before/after images are stored under `visual/mesh_renders/`. These are real mesh top-down projections, not photorealistic renders. They support qualitative inspection of geometric movement and relation correction, but they still do not prove human-perceived visual quality is better.

Gallery: `visual/mesh_renders_gallery.html`.

Paper-facing oriented-footprint figures were also generated under `visual/paper_figures/`, with a compact gallery at `visual/paper_figures_gallery.html`. These are cleaner than the raw mesh-projection diagnostics: they use generated oriented boxes, relation arrows, prompt text, relation score, and mesh-collision pair counts. They are better suited for paper figures, while the raw mesh projections remain useful as evidence that the selected examples correspond to retrieved 3D-FUTURE meshes.

Recommended paper use:

- Use `visual/paper_figures/*.svg` for the main qualitative figure grid.
- Keep `visual/mesh_renders_gallery.html` as supplementary/debug evidence.
- Do not describe either figure set as photorealistic rendering or as proof of better visual quality.

## Strong Baseline Status

ReSpace was cloned and inspected on the remote server at `/root/RelationAwareInstructScene/repos/respace` (commit `1eccb69`). It is a strong related baseline, but the official protocol is SSR-3DFRONT and requires a separate environment plus gated `Meta-Llama-3.1-8B-Instruct` access. The remote machine is not logged into HuggingFace, so a fair ReSpace run was not completed in this pass. SDGScenes remains a close related method without a verified same-split runnable path on this server.

Safe conclusion: current experiments strengthen mesh-validity evidence for our own method, but they still do not establish superiority over ReSpace or SDGScenes.
