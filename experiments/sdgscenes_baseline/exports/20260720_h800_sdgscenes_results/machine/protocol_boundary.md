# SDGScenes Protocol Boundary

## Defensive position

SDGScenes should be described as a broader system for user-intent / semantic-constraint-aware 3D scene generation. It is not the same protocol as our main experiment unless we can fully align input, output, data split, and evaluator.

Our paper’s main claim remains narrower:

> Under the official InstructScene validation protocol, our final-layout verifier-repair improves realized relation grounding compared with official InstructScene output.

## Direct-comparison requirements

SDGScenes can be included in a direct numerical comparison only if all requirements below are met.

| Requirement | Needed for direct table? | Current status |
|---|---:|---|
| Official code or author-confirmed implementation | yes | not located |
| Official data preprocessing and split | yes | not verified |
| Same input prompts / relation specs | yes | not verified |
| Same output layout representation | yes | not verified |
| Same object taxonomy mapping | yes | not verified |
| Same relation thresholds | yes | not verified |
| Same mesh collision / overlap / OOB evaluator | yes | not verified |
| Same random seeds and failure policy | yes | not verified |

## Table placement policy

- Same-protocol and same-evaluator methods go into the direct numeric table.
- SDGScenes official numbers, if found, go into a reported-results context table only.
- SDGScenes-inspired constrained optimization can go into a control/baseline table only if it uses our exact input/output/evaluator and is clearly labeled non-official.

## Reviewer-facing explanation

Use this concise explanation in the experiment section:

> We treat SDGScenes as a strong related system but not as a direct baseline by default because its input protocol, constraint system, data handling, and output generation pipeline are not guaranteed to match the fixed-InstructScene final-layout repair setting. When a method can be run under the same split, layout representation, thresholds, and evaluator, we report direct numbers. Otherwise, we report protocol analysis and reproduction boundaries.

