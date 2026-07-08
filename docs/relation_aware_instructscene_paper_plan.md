# Relation-Aware InstructScene: Paper Plan

Date: 2026-05-29

## One-sentence idea

Relation-Aware InstructScene turns explicit spatial relations in a natural-language instruction into a lightweight verification-and-repair signal, improving whether the final 3D indoor layout actually realizes the requested relations without retraining the original InstructScene models or constructing a new benchmark.

## Core novelty

The baseline InstructScene pipeline can generate a plausible scene graph and a plausible layout, but the requested relation can be lost when the graph is decoded into object positions. Our method inserts a relation-aware layer between instruction-conditioned generation and final evaluation:

1. Parse explicit relations from the instruction, such as left of, right of, in front of, behind, close left, close right.
2. Match parsed relation triples to generated object classes.
3. Verify whether the generated layout realizes those triples under the same relation evaluator.
4. Apply a bounded geometric repair to object translations.
5. Re-evaluate the layout and preserve per-scene evidence.

This is intentionally simple and strong as a first paper story: the contribution is not a bigger generator, but a relation-consistency layer that exposes and fixes a real failure mode in instruction-to-scene generation.

## Novelty audit and claim boundaries

The work is innovative, but only under a precise framing. It should not be claimed as the first relation-constrained 3D indoor scene generation method. Prior and concurrent work already studies scene graphs, semantic dependencies, LLM/VLM spatial constraints, and optimization-based object placement.

Safe claim:

> We identify and quantify a graph-to-layout grounding gap in InstructScene, then introduce a training-free relation verifier-repair layer that improves realized spatial relation satisfaction on the original InstructScene validation benchmarks without new annotations or new benchmark construction.

Unsafe claims to avoid:

- "First relation-aware 3D indoor scene generation method."
- "First spatial-constraint optimization for indoor scene synthesis."
- "First language-guided relation parser for 3D scene generation."
- "Solves text-to-3D spatial reasoning."

Closest threat:

- SDGScenes already uses a Semantic Dependency Graph, VLM-derived commonsense constraints, and nonlinear constrained optimization for object placement. This overlaps with the broad idea of satisfying user intent through constraints.

How we remain distinct:

- We target an existing pretrained InstructScene pipeline rather than proposing a new full generator.
- We evaluate the final realized relations after graph-to-layout decoding, not only graph-level consistency or user-perceived intent.
- We use the original InstructScene benchmark splits and labels, avoiding new annotation or new benchmark construction.
- We provide oracle-vs-parsed decomposition, parser precision/recall, graph accuracy, baseline layout accuracy, repaired layout accuracy, and per-scene improved/degraded/same counts.
- We frame the method as a plug-in verifier-repair module, not as a replacement scene generator.

## Five publishable innovation points

### 1. Relation-aware layout realization instead of relation-aware graph generation only

Many text-to-scene pipelines optimize or evaluate the generated symbolic graph. Our result shows that graph-level relation correctness is not enough: the final continuous layout can still violate the requested relation. The paper can frame this as a graph-to-layout grounding gap.

Claim to test:

> Explicitly verifying and repairing relations after layout decoding improves realized spatial consistency across room types.

Current evidence:

| Room | Baseline realized relation acc | Relation-aware acc | Gain |
|---|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | +0.1347 |
| Living room | 0.5510 | 0.7415 | +0.1905 |
| Dining room | 0.5948 | 0.7844 | +0.1896 |

Quality evidence from the geometry-aware rerun:

| Room | Baseline overlap ratio | Repaired overlap ratio | Baseline OOB center rate | Repaired OOB center rate |
|---|---:|---:|---:|---:|
| Bedroom | 0.086977 | 0.083586 | 0.000000 | 0.000000 |
| Living room | 0.139931 | 0.134841 | 0.000000 | 0.000000 |
| Dining room | 0.155403 | 0.154162 | 0.000000 | 0.000000 |

This does not fully prove visual naturalness, but it directly addresses the most obvious reviewer concern: the relation repair is not merely increasing relation accuracy by pushing objects out of bounds or increasing coarse footprint overlap. Under the current AABB-footprint proxy, overlap slightly decreases in all three room categories.

### 2. No-new-benchmark, no-new-annotation relation supervision

The method uses existing InstructScene validation instructions and existing relation labels/evaluator. It does not require collecting new relation annotations. This directly matches the constraint of using existing benchmarks.

Paper angle:

> A relation-aware controller can be evaluated on the original InstructScene bedroom, living room, and dining room splits, making the comparison reproducible and inexpensive.

### 3. Plug-in relation repair for pretrained scene generators

The current implementation works as a plug-in script over pretrained InstructScene checkpoints. This is useful because it separates relation grounding from expensive model retraining.

Paper angle:

> Relation grounding can be improved by a modular verifier-repair layer that can sit on top of existing scene generators.

Required follow-up:

- Show runtime overhead.
- Show that collision/naturalness does not collapse.
- Add ablations over repair passes and distance thresholds.

### 4. Text parser as a weak relation interface

The parser is deliberately imperfect, yet still improves all three room categories. This is a useful result: the system does not require perfect language understanding to improve relation satisfaction.

Current parser quality:

| Room | Parser recall | Parser precision |
|---|---:|---:|
| Bedroom | 0.5265 | 0.5309 |
| Living room | 0.4320 | 0.5546 |
| Dining room | 0.4833 | 0.5508 |

Story:

> Even weak explicit-relation extraction provides enough structure for a downstream verifier to repair many layout failures.

Do not overclaim:

- This is not yet a general natural-language spatial reasoner.
- It currently targets explicit relation phrases, not implicit affordances or commonsense constraints.

### 5. Metric decomposition: graph correctness vs realized layout correctness

The experiments report graph relation accuracy, baseline layout relation accuracy, repaired layout relation accuracy, parser recall, parser precision, and per-scene improved/degraded/same counts. This decomposition is stronger than reporting a single metric.

Paper angle:

> Relation-aware scene generation should be evaluated at multiple stages: instruction-to-graph, graph-to-layout, and final realized relations.

This also gives a clean ablation table:

- Generated graph relation accuracy.
- Baseline decoded layout relation accuracy.
- Oracle relation-aware repair upper bound.
- Parsed relation-aware repair.
- Parsed relation-aware repair with different thresholds.

## Baselines

### Primary baseline

Official InstructScene SG diffusion VQ object-feature model, evaluated on existing validation splits:

- `bedroom_sgdiffusion_vq_objfeat`, checkpoint epoch 1999.
- `livingroom_sgdiffusion_vq_objfeat`, checkpoint epoch 1459.
- `diningroom_sgdiffusion_vq_objfeat`, checkpoint epoch 1239.

This is the main comparison because our method reuses the same generated scenes and changes only relation-aware post-processing.

### Auxiliary baseline

Official graph relation accuracy from the generated scene graph. This is not the same as final layout success, but it helps diagnose whether the failure comes from graph generation or layout realization.

### Upper bound

Oracle relation-aware repair uses the benchmark-provided selected relations rather than parsed relations. It should be presented as an upper-bound diagnostic, not as the deployable method.

Current bedroom oracle result:

- Baseline: 0.7388.
- Oracle repair: 0.8857.
- Parsed repair: 0.8735.

Full parsed-vs-oracle results:

| Room | Baseline | Parsed repair | Oracle repair | Oracle gap | Parsed gain captured |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | 0.8857 | +0.0122 | 91.7% |
| Living room | 0.5510 | 0.7415 | 0.7755 | +0.0340 | 84.8% |
| Dining room | 0.5948 | 0.7844 | 0.8141 | +0.0297 | 86.4% |

This suggests most of the benefit comes from geometric relation realization, while parser quality is a remaining but not fatal bottleneck.

## Related work map

### Indoor scene datasets

- 3D-FRONT provides professionally designed furnished rooms with layouts and semantics, and is the underlying indoor-scene resource used by many 3D scene synthesis works: [3D-FRONT paper/project](https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset).
- 3D-FUTURE provides furniture assets that pair naturally with 3D-FRONT-style layout generation: [3D-FUTURE dataset](https://tianchi.aliyun.com/specials/promotion/alibaba-3d-scene-dataset).

### Layout and indoor scene synthesis

- ATISS uses autoregressive transformers for indoor scene synthesis and is an important baseline family for 3D-FRONT layout generation: [ATISS project](https://nv-tlabs.github.io/ATISS/).
- SceneFormer models indoor scene generation as a transformer-based scene synthesis problem: [SceneFormer arXiv](https://arxiv.org/abs/2012.09793).
- DiffuScene applies denoising diffusion models to generative indoor scene synthesis: [DiffuScene arXiv](https://arxiv.org/abs/2303.14207).

### Text, scene graph, and relation-conditioned generation

- InstructScene is the direct baseline: instruction-driven 3D indoor scene synthesis with scene-graph and layout generation components: [InstructScene arXiv](https://arxiv.org/abs/2402.04717).
- CommonScenes focuses on commonsense 3D indoor scene generation with scene-graph diffusion, close to the scene-graph side of this work: [CommonScenes arXiv](https://arxiv.org/abs/2305.16283).
- LayoutGPT studies compositional visual planning with language models and is related to LLM-driven layout planning: [LayoutGPT arXiv](https://arxiv.org/abs/2305.15393).
- Holodeck explores language-guided generation of 3D embodied AI environments, related to text-conditioned environment synthesis at a broader scale: [Holodeck arXiv](https://arxiv.org/abs/2312.09067).
- ReSpace is a close text-driven indoor scene synthesis/editing system with a structured scene representation, specialized spatial reasoning model, and geometry-violation metric: [ReSpace project](https://respace.mnbucher.com/).
- SDGScenes is a particularly close concurrent/very recent work: it encodes user intent with a Semantic Dependency Graph, uses a VLM to infer constraints, and solves object placement with nonlinear constrained optimization. Our claims must be differentiated from this broad constraint-optimization direction: [SDGScenes ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0031320326006394).

## Proposed storyline

### Title candidate

Relation-Aware InstructScene: Verifying and Repairing Spatial Relations in Instruction-Guided 3D Indoor Scene Generation

### Abstract skeleton

Instruction-guided 3D indoor scene generation requires not only plausible object selection but also faithful realization of spatial relations. Existing scene-graph-based pipelines can generate reasonable graphs while still failing to realize requested relations in the final continuous layout. We propose Relation-Aware InstructScene, a lightweight verifier-repair layer that parses explicit spatial relations from language, checks whether generated layouts satisfy them, and applies bounded geometric repairs. Without retraining or constructing a new benchmark, our method improves realized relation accuracy on existing InstructScene bedroom, living-room, and dining-room validation splits by 13.5 to 19.1 absolute points. The results reveal a graph-to-layout grounding gap and show that relation-aware post-generation control is an effective, low-cost path toward more instruction-faithful 3D scene synthesis.

### Introduction flow

1. Text-to-3D indoor scene generation is becoming useful for games, embodied AI, simulation, and content creation.
2. In these applications, spatial relations are not decorative: "chair left of table" is a hard semantic constraint.
3. Scene-graph pipelines help structure generation, but relation satisfaction must survive final layout decoding.
4. We show a measurable gap between generated relation intent and realized layout relations.
5. We introduce a verifier-repair layer that reuses existing checkpoints and existing benchmarks.
6. Results show large gains across three room categories.

### Method section flow

1. Baseline InstructScene generation.
2. Relation extraction from instruction text.
3. Relation verifier using generated layout geometry.
4. Bounded multi-pass repair.
5. Evaluation protocol on existing benchmark splits.

### Experiment section flow

1. Benchmark setup: InstructScene bedroom, living room, dining room.
2. Main relation accuracy table.
3. Oracle vs parsed relation source.
4. Parser quality analysis.
5. Ablation over repair passes and thresholds.
6. Layout-quality safeguards: collision, out-of-bound, distribution metrics.
7. Qualitative before/after examples.

## What is strong enough now

- The effect size is large.
- Results are consistent across three room types.
- No degraded scenes under the measured selected-relation metric.
- The method is reproducible from existing checkpoints and existing data.
- A first geometry sanity check is positive: footprint overlap ratio decreases slightly after repair in all three room categories, and repaired center out-of-bounds rate remains zero.
- Parsed relations capture most of the oracle-repair gain, so the deployable version is close to the upper-bound version.
- Repair-pass ablations show the effect is not a one-off hyperparameter artifact: p1 already gives large gains, p2 improves further, and p3 mostly saturates.
- Distance-threshold ablations show the method is robust around close distances 0.50 to 0.75, while close distance 1.00 weakens exact relation accuracy.
- Three-seed results show stable gains across bedroom, living room, and dining room.

## What is not yet strong enough

- We have measured a coarse AABB-footprint overlap and center out-of-bound proxy, but not full 3D mesh collision, physical support, realism, diversity, or distribution drift.
- We have not yet produced qualitative rendered figures.
- We have not yet compared against a stronger relation-aware baseline from related work.
- The parser is rule-based; it should be framed as a deliberately simple interface, or replaced with a stronger parser in an ablation.
- Tiny center-boundary artifacts appear in a few non-main-seed repaired layouts, so final code should use stricter clipping or report the OOB proxy honestly.

## Recommended next experiments before submission

1. Quality metrics: collision rate, out-of-room/object bounds, object overlap, KL/FID-style distribution distance if available in the repo.
2. Ablation: repair passes 0/1/2/3, close distance 0.5/0.75/1.0, far distance 1.3/1.6/2.0.
3. Oracle gap: run oracle on all three room types.
4. Parser replacement: compare rule parser vs LLM parser or dependency-parser extraction, still using the same benchmark labels for evaluation only.
5. Qualitative renders: at least 5 examples per room, before/after, with relation text overlay.
