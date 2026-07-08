# Visual Quality and Strong Baseline Update

Date: 2026-05-30

## New floor-prior real-mesh showcase

A new floor-prior rendering batch was generated from the `floor_prior_max1.8_mesh_p2_close0.75_far1.6` outputs. The selector keeps examples where explicit relation satisfaction improves and FCL mesh collision pairs do not increase.

Outputs:

- `visual/floor_prior_showcase/`
- `visual/floor_prior_showcase.html`
- `results/tables/visual_quality_real_mesh.csv`
- `results/tables/visual_quality_mesh_projection.csv`
- `visual/a_conf_visual_quality.html`

Summary:

| Showcase | Examples | Mean relation gain | Mean mesh-pair delta | Mean CLIP delta | Mean SSIM |
|---|---:|---:|---:|---:|---:|
| old direct y-fixed showcase | 3 | +1.333 | 0.000 | -0.0165 | 0.8358 |
| new floor-prior showcase | 15 | +1.400 | -0.267 | +0.0027 | 0.9065 |

Interpretation:

- The new showcase is better paper material than the old three-example direct showcase.
- It supports a conservative visual-consistency claim: the selected floor-prior examples improve explicit relations, do not increase mesh pairs, and retain high before/after structural similarity.
- It still should not be written as proof of universally better human-perceived visual quality. CLIP delta is small and the renders are diagnostic/cinematic real-mesh views, not a human preference study.

## Strong baseline status

The strong-baseline feasibility table is now written to:

- `results/tables/strong_baseline_feasibility.csv`
- `docs/relation_aware_strong_baseline_status.md`

Current safe baseline framing:

- Use InstructScene under the same validation prompts/checkpoints as the direct fair baseline.
- Use direct y-fixed repair, collision-gated repair, and floor-prior variants as internal baselines/ablations.
- Treat ReSpace, SDGScenes, and CommonScenes as close related work unless a shared protocol is actually executed.
- Do not claim superiority over ReSpace or SDGScenes from the current evidence.
