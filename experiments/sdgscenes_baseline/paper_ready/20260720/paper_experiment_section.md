# Experiment section draft: defensive SOTA comparison

## Defensive comparison with stronger relation-aware systems

Our main empirical claim is intentionally scoped to the existing InstructScene validation protocol. Given the official InstructScene output layouts, we evaluate whether a post-generation verifier-repair layer can improve final realized relation grounding without changing the pretrained generator, the validation split, the relation thresholds, or the layout evaluator. This setting differs from full text-driven scene synthesis systems such as ReSpace and SDGScenes, which target broader generation or user-intent constraint pipelines. Therefore, direct numerical comparisons are included only when a method can be run under the same input split, output representation, relation thresholds, and evaluator.

Under this same-protocol setting, the official InstructScene output is the primary baseline. Our main variant is `floor_prior_max1.8_mesh_p2_close0.75_far1.6`, which applies a floor-prior constrained final-layout repair. For mesh-validity claims, we additionally report a collision-gated repair variant that falls back to the original layout when the proposed repair would worsen mesh-collision behavior. Across 531 validation scenes and 808 evaluated relations in bedroom, living room, and dining room subsets, Floor-Prior improves relation accuracy from 62.3% to 75.0% (+12.7 percentage points). The collision-gated variant preserves most of the relation gain, reaching 74.6% (+12.4 percentage points), while reducing the aggregate mesh-pair collision rate from 4.4% to 4.2% and the mesh-scene collision rate from 71.9% to 70.8%. These results support the narrower claim that final-layout repair improves realized relation grounding under the fixed InstructScene protocol.

We treat SDGScenes as a strong related system rather than a direct baseline by default. SDGScenes addresses a broader user-intent and semantic-constraint-aware scene generation setting, with semantic dependency structure, visual-language constraints, and constrained optimization. In contrast, our method operates after a fixed pretrained generator has already produced a layout. A direct ranking against SDGScenes would require matching the official code or author-confirmed implementation, data split, input prompts or relation specifications, output layout representation, object taxonomy, relation thresholds, mesh evaluator, random seeds, and failure policy. Our local audit did not locate a no-friction official SDGScenes release at the time of packaging, so we do not claim an official reproduction and do not rank SDGScenes against our method.

To make the comparison defensive rather than evasive, we include a same-evaluator SDGScenes-inspired constrained-optimization smoke baseline. This baseline is not an official SDGScenes reproduction. It uses our relation specification and InstructScene output layouts, applies a transparent constrained layout optimizer, and evaluates the result with our saved relation and geometry checks. On the same 531 scenes, this smoke baseline improves simple all-relation satisfaction from 41.9% to 79.2% (+37.3 percentage points) and horizontal-relation satisfaction from 38.0% to 79.0% (+41.0 percentage points), while reducing logged overlap pairs from 894 to 833 and keeping out-of-bounds centers unchanged at zero. Because this baseline does not reproduce SDGScenes' official pipeline, it should be reported as a defensive control or feasibility-bounded baseline, not as SDGScenes official performance.

The resulting table structure separates evidence by comparability. Table 1 reports only same-split, same-evaluator numerical comparisons. Table 2 summarizes protocol comparability for InstructScene, our variants, SDGScenes, ReSpace, and relation-benchmark references. Table 3 reports the SDGScenes-inspired defensive smoke baseline and the official SDGScenes feasibility boundary. This separation prevents conflating full user-intent-driven scene synthesis with post-generation final-layout grounding repair.

### Reviewer-facing wording

We include the following explanation in the experiment section or appendix:

> Direct numerical comparisons use the same validation split, layout representation, relation thresholds, and mesh evaluator. Methods with different protocols or unreproduced official pipelines are shown in the protocol/reference table and are not ranked against our method. We treat SDGScenes as a strong related system, but not as a direct baseline by default, because its input protocol, constraint system, data handling, and output generation pipeline are not guaranteed to match the fixed-InstructScene final-layout repair setting.

### Limitations and robustness boundaries

The SDGScenes-inspired baseline is a same-evaluator control, not an official reproduction. Its purpose is to test whether a stronger constrained-optimization style baseline changes the interpretation of our repair results under our saved evaluator. It cannot support an `outperform SDGScenes` claim. If official SDGScenes code, data split, and output conversion become available later, SDGScenes should be moved from the protocol/reference table into a direct-comparison candidate only after a bedroom smoke test succeeds and the same split, thresholds, object taxonomy, and mesh evaluator are verified.

### Suggested placement

- Main paper: include Table 1 and a shortened version of Table 2.
- Appendix: include full Table 2, Table 3, feasibility notes, and links to the HTML and machine-readable result archive.
- Related work: describe SDGScenes and ReSpace as stronger related systems under different protocols; do not describe them as beaten baselines.

