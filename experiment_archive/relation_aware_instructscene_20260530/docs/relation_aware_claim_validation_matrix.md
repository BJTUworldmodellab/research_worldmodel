# Relation-Aware InstructScene Claim Validation Matrix

Date: 2026-05-29

This note converts the current experiment package into paper-safe claims. The goal is to maximize what the data can say while avoiding claims that the current experiments cannot support.

## Supported Main Claim

Relation-Aware InstructScene improves explicit spatial-relation realization for InstructScene-generated indoor layouts on the existing InstructScene validation splits, without retraining the base model.

Evidence:

| Room | Baseline relation acc | Ours relation acc | Gain | Multi-seed gain mean |
|---|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | +0.1347 | +0.1374 |
| Living room | 0.5510 | 0.7415 | +0.1905 | +0.2063 |
| Dining room | 0.5948 | 0.7844 | +0.1896 | +0.2069 |

The result is supported by:

- Main seed full validation runs on bedroom, living room, and dining room.
- Multi-seed validation with seeds 0, 1, and 2.
- Repair-pass ablation showing most benefit appears after one pass and saturates around two passes.
- Distance-threshold ablation showing the default is not a one-room accident.
- Oracle-source upper bound showing the parsed method captures most of the available repair gain.

## Geometry Validity Claim

Safe wording:

The relation-aware repair does not obviously degrade coarse box-level layout validity under AABB and oriented-footprint overlap proxies; overlap slightly decreases in the evaluated splits.

Evidence:

| Room | AABB base | AABB ours | OBB base | OBB ours |
|---|---:|---:|---:|---:|
| Bedroom | 0.086977 | 0.083586 | 0.046569 | 0.041681 |
| Living room | 0.139931 | 0.134841 | 0.054337 | 0.050177 |
| Dining room | 0.155403 | 0.154162 | 0.057112 | 0.055276 |

Unsafe wording:

- Mesh collision is lower.
- Physical plausibility is improved.
- Visual quality is better.

Reason: exact 3D mesh intersections, support/contact, object accessibility, and rendered-perception metrics were not evaluated.

Update after mesh-collision run:

Direct repair was evaluated with retrieved 3D-FUTURE meshes and FCL collision checks. Direct repair does not support a lower-mesh-collision claim because living room and dining room show very small increases in mesh collision pair rate. A collision-gated variant, however, preserves relation gains while reducing mesh collision pair rate below baseline.

| Room | Direct repair acc | Collision-gated acc | Baseline mesh pair rate | Direct repair mesh pair rate | Collision-gated mesh pair rate |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.8735 | 0.8449 | 0.070244 | 0.070244 | 0.064878 |
| Living room | 0.7415 | 0.6871 | 0.031257 | 0.031616 | 0.030540 |
| Dining room | 0.7844 | 0.7212 | 0.034229 | 0.034766 | 0.033154 |

Revised safe wording:

The direct repair improves relation satisfaction but does not guarantee lower mesh collision. A conservative collision-gated variant retains substantial relation gains and reduces FCL mesh collision pair rate below the baseline.

## Visual Quality Claim

Current evidence:

- Top-down before/after SVG diagnostics exist under `visual/qualitative/`.
- Mesh-projection before/after PNG diagnostics exist under `visual/mesh_renders/`.
- They are useful for checking whether relation repair moves retrieved 3D-FUTURE meshes plausibly.

Safe wording:

Qualitative top-down and mesh-projection diagnostics illustrate relation corrections.

Unsafe wording:

Visual quality is better.

Required experiment to support stronger wording:

- Render mesh-level scenes from identical camera presets.
- Run a human preference study or a rendered-image metric such as top-down FID/KID if a compatible official renderer and real-reference set are available.

## Implicit Commonsense Claim

Audit result:

| Room | Explicit scenes | Implicit scenes |
|---|---:|---:|
| Bedroom | 162 | 0 |
| Living room | 192 | 0 |
| Dining room | 177 | 0 |

Safe wording:

The current benchmark evaluates explicit spatial relation following.

Unsafe wording:

- The method handles all implicit commonsense relations.
- The method infers unstated affordance relations.

Reason: no implicit commonsense scenes were found in the current InstructScene relation subset under the audit.

## Strong Related-Work Boundary

ReSpace is a strong related method because it is a text-driven 3D indoor scene synthesis/editing system with structured scene representation, spatial reasoning, preference alignment, and a fine-grained geometric violation metric.

SDGScenes is a strong related method because it targets implicit user intent, uses a Semantic Dependency Graph, uses VLM-derived commonsense constraints, and optimizes placement with physical constraints.

Sources checked:

- ReSpace arXiv: https://arxiv.org/abs/2506.02459
- ReSpace model/repository pointer: https://huggingface.co/gradient-spaces/respace-sg-llm-1.5b
- SDGScenes ScienceDirect: https://www.sciencedirect.com/science/article/pii/S0031320326006394

Safe wording:

Our current experiments are a direct plug-in evaluation on InstructScene, not a shared-protocol comparison against ReSpace or SDGScenes.

Unsafe wording:

- We outperform ReSpace.
- We outperform SDGScenes.
- We are the first relation-aware 3D scene generation method.

Required experiment to support stronger comparison:

- Run ReSpace and SDGScenes, or faithfully reimplement their public protocol, on a shared set of prompts/assets.
- Normalize scene representation and metrics before comparing relation satisfaction, collision, boundary compliance, and visual quality.
- Report implementation gaps if either method has unavailable code, private data, or incompatible assets.

## Recommended Paper Storyline

The safest and still publishable storyline is:

1. InstructScene often captures relation intent at the semantic-graph level but does not always realize it geometrically.
2. Relation-Aware InstructScene adds a lightweight verifier-repair stage that directly targets this graph-to-layout grounding gap.
3. On existing InstructScene relation benchmarks, relation satisfaction improves consistently across bedroom, living-room, and dining-room splits.
4. Box-level overlap proxies do not increase, suggesting the repair is not simply trading relation accuracy for obvious layout invalidity.
5. The method is deliberately scoped to explicit spatial relations; implicit commonsense and SOTA method comparison require additional shared-protocol experiments.
