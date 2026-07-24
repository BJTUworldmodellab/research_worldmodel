# Project and Paper Review — 2026-07-24

## Executive Decision

The repository now contains a coherent research direction and substantially more evidence than the original snapshot, but the current paper is **not yet submission-ready for a top main track**. My calibrated recommendation is **Weak Reject / Major Revision**.

The best framing is:

> A training-free final-layout constraint-projection layer that improves explicit spatial-relation realization in frozen 3D indoor scene generators while limiting geometric side effects.

The best venue family remains **Eurographics / Computer Graphics Forum**, with **3DV** as a plausible alternative after stronger independent evaluation. The work should not be framed as a generic world model, a new state-of-the-art generator, or proof that one particular internal decoder causes all final-layout violations.

## What Is Actually Supported

### 1. InstructScene relation repair

The strongest in-domain evidence is the three-room InstructScene evaluation. The paper-facing Floor-Prior variant improves final-layout selected-relation accuracy in bedrooms, living rooms, and dining rooms. Collision gating retains positive gains and reduces mesh-collision pair rates below the corresponding baselines.

The direct repair variant has larger relation gains, but it moves objects much farther and is therefore an aggressive internal ablation rather than the main method.

### 2. CommonScenes cross-generator evidence

Across 339 CommonScenes outputs from four room types, generic relation satisfaction improves by 0.0016--0.0054 and collision penalties decrease in every room type. Only 1.38--4.05% of boxes change.

This is supporting generalization evidence, not a headline benchmark win. On the bedroom split, the independent CommonScenes official score decreases from 0.9732 to 0.9696. The paper must retain this negative result and must not claim improvement on the official CommonScenes metric.

### 3. Strict safety ablation

The strict one-factor bedroom experiment evaluates layout-only overlap repair with a scene-graph consistency guard:

- 162 scenes, seed 42.
- Recommended configuration: step 0.05 m, displacement cap 0.25 m, 50 iterations.
- Aggregate oriented-footprint IoU sum: 0.2245 to 0.1287, a 42.7% reduction.
- Scene-graph/layout consistency: 0.9095 to 0.9134.
- Mean object movement: 0.0753 m.
- Across 1,296 evaluated repairs: zero failures, zero worse-overlap scenes, and zero worse-consistency scenes.

This is a self-consistency and 2D overlap result. It is not ground-truth relation accuracy, 3D mesh collision, or perceptual quality.

## Adapted Epistemic Review

This is an adaptation of the six ARA Level-2 review dimensions to the paper and repository. It is **not a formal ARA Seal review** because the repository does not provide the required Level-1-validated ARA structure (`PAPER.md`, `logic/claims.md`, `logic/experiments.md`, and exploration tree).

| Dimension | Score | Assessment |
|---|---:|---|
| D1 Evidence relevance | 3/5 | The main InstructScene evidence is relevant, but part of the repair and evaluation logic is shared; CommonScenes generic and official metrics disagree. |
| D2 Falsifiability | 2/5 | Claim boundaries exist, but the paper does not yet state executable failure thresholds for every major claim. |
| D3 Scope calibration | 4/5 | The revised draft explicitly avoids SOTA, causal decoder, official CommonScenes, and universal visual-quality claims. |
| D4 Argument coherence | 3/5 | Constraint projection unifies the story, but text-relation repair and graph-guarded overlap repair remain two technically different instantiations. |
| D5 Exploration integrity | 3/5 | Reports preserve partial ReSpace attempts, missing baselines, and the CommonScenes official-score decrease; there is no formal exploration trace. |
| D6 Methodological rigor | 2/5 | Strong internal ablations exist, but independent evaluation, same-budget controls, human assessment, and uncertainty for relation gains remain missing. |

**Mean: 2.83/5 — Weak Reject / Major Revision.**

## Major Review Findings

### F01 — Independent evaluation is still insufficient

**Severity:** Major
**Why it matters:** A verifier-repair method can overfit its own relation definition. The CommonScenes official-score decrease is direct evidence that improvement under one verifier does not guarantee improvement under another.
**Required fix:** Add an independent relation evaluator or human-annotated relation subset that is not used to accept repair moves.

### F02 — The main method must remain unambiguous

**Severity:** Major
**Why it matters:** Direct repair produces the largest accuracy gains, Floor-Prior provides the better movement story, collision gating provides the mesh-validity story, and graph-guarded repair provides the no-worse overlap story. Mixing their best numbers would overstate one method.
**Required fix:** Make collision-gated Floor-Prior the main method. Label direct repair as an aggressive upper-effect ablation, CommonScenes generic-gate as cross-generator evidence, and graph-guarded overlap repair as a safety ablation.

### F03 — Same-budget baselines are missing

**Severity:** Major
**Why it matters:** The frozen generator is a necessary baseline but does not show whether the proposed selection logic is better than generic movement or optimization.
**Required fix:** Add:

1. random/local displacement under the same movement budget;
2. a generic constrained optimizer under the same constraints and budget;
3. an oracle-parser upper bound under the final collision-gated Floor-Prior protocol.

### F04 — Statistical evidence is incomplete

**Severity:** Major
**Why it matters:** Three-seed summaries exist for InstructScene, but there are no confidence intervals or paired tests for the main relation gains. CommonScenes bootstrap intervals cover disturbance metrics, not relation-score changes.
**Required fix:** Export per-scene relation rows, then report paired bootstrap confidence intervals and a paired significance test for each room type.

### F05 — Perceptual claims require human evidence

**Severity:** Minor
**Why it matters:** SSIM, PSNR, CLIP, and selected render panels quantify change but not whether users prefer the repaired layout.
**Required fix:** If the paper claims perceptual improvement, add a blinded preference study. Otherwise retain the narrower claim that average visual disturbance is small.

## Code Review Outcome

The merged code initially received **REQUEST CHANGES** because:

- committed shell scripts used CRLF and failed Bash parsing;
- `python src/ablation_runner.py` failed despite being the documented command;
- the ReSpace close-front/close-behind/close-right predicate mapping was wrong;
- per-scene grid deltas used an aggregate baseline;
- the bounds proxy hard-coded the bedroom class dimension;
- zero repair iterations could raise an unbound-local error;
- the repair seed did not control tied-center randomness.

These issues were corrected in the post-merge working tree. The GPU experiment suite still needs remote rerun before regenerated result files can be called independently verified.

## Paper Changes Made

The revised LaTeX draft:

- changes the title and abstract from a causal “graph-to-layout gap” story to final-layout constraint projection;
- makes collision-gated Floor-Prior the paper-facing method;
- adds the four-room CommonScenes table and retains the official-score decrease;
- adds the strict one-factor overlap/consistency/movement ablation;
- separates direct repair, cross-generator repair, and graph-guarded repair;
- expands limitations and submission blockers;
- removes the stale checklist placeholder;
- corrects the ReSpace metadata and malformed 3D-FRONT author entry.

## Recommended Experiment Order

1. **Independent evaluator** on all existing scenes or a statistically powered annotated subset.
2. **Same-budget random and generic optimization controls.**
3. **Final-protocol oracle parser upper bound.**
4. **Per-scene bootstrap confidence intervals for relation gains.**
5. **Shared-protocol ReSpace comparison** if the environment can be made reproducible.
6. **Small blinded human preference study** covering both low-change and high-change cases.
7. Optional object-level Chamfer or IoU audit for changed objects.

## Release Readiness

- **Repository integration:** ready after the post-merge fixes pass local verification.
- **Paper draft:** complete as a research draft.
- **Top-venue submission:** not ready.
- **Workshop or internal circulation:** ready with the explicit caveats above.
- **Full GPU reproduction:** not verified in this local pass.
