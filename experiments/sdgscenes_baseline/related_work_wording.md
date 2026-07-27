# Claim-safe Related Work / Experiment Wording

## Related work wording

SDGScenes studies a broader user-intent and constraint-aware scene generation setting, combining semantic dependency structure, visual-language constraints, and constrained optimization. This makes it a strong related system, but not automatically a direct baseline for our setting. Our work instead focuses on a narrower post-generation problem: given fixed pretrained InstructScene outputs, we repair final-layout relation grounding under the existing InstructScene validation protocol.

## Experiment wording

We include SDGScenes in the protocol comparison table rather than the direct numerical ranking table unless its official code, data split, input protocol, output representation, and evaluator can be aligned with ours. This avoids conflating different tasks: full user-intent-driven scene synthesis versus final-layout grounding repair for fixed InstructScene generations.

## Allowed claims

- Compared with official InstructScene output under the same validation protocol, our method improves final realized relation accuracy.
- SDGScenes and ReSpace are strong related systems under different protocols; we report them as non-direct references unless same-protocol reproduction succeeds.
- Our verifier-repair can serve as a final-layout grounding layer for generators that expose object layouts.

## Disallowed claims

- We outperform SDGScenes.
- We outperform ReSpace.
- We are SOTA on text-driven 3D scene generation.
- We are the first relation-aware 3D scene generation method.
- We universally improve visual quality.
- We solve complete commonsense / affordance / reachability reasoning.

## Results-table footnote

Suggested footnote:

> Direct numerical comparisons use the same validation split, layout representation, relation thresholds, and mesh evaluator. Methods with different protocols or unreproduced official pipelines are shown in the protocol/reference table and are not ranked against our method.

