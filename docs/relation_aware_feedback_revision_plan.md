# Relation-Aware InstructScene Feedback Revision Plan

Date: 2026-05-30

## Feedback verdict

The feedback is directionally correct. The current project should not be framed as a small "repair module" paper. The stronger and safer framing is:

> Instruction-guided 3D scene generation has a graph-to-layout relation grounding gap. We provide a reproducible, training-free, safety-aware relation verification and repair framework for final layouts.

This framing keeps the contribution defensible because it does not claim to replace ReSpace, SDGScenes, CommonScenes, Holodeck, or other relation-aware generators. It instead studies a narrower failure mode under the existing InstructScene protocol.

## Immediate paper changes applied

- Retitled the draft from a method-name title to:
  - `Repairing Graph-to-Layout Relation Grounding in Instruction-Guided 3D Indoor Scene Generation`
- Reframed the method name from `Relation-Aware InstructScene` to:
  - `Relation-Grounded Floor Repair`
- Rewrote the abstract wording toward:
  - graph-to-layout grounding gap
  - relation parsing, object matching, verification, bounded floor-plane repair, collision-gated validation
  - final-layout relation grounding rather than a new full generator
- Strengthened the related-work boundary:
  - We do not claim to outperform or replace ReSpace / SDGScenes.
  - We study a plug-in final-layout relation grounding layer for an existing instruction-guided generator.
- Added a paper subsection note that main-conference readiness still needs missing reviewer-facing controls.

## Reviewer risks identified by the feedback

### Risk 1: "This is just post-processing"

Defense:

- The paper should foreground the graph-to-layout grounding gap.
- The repair should be described as a complete closed loop:
  - relation extraction
  - object matching
  - geometric verification
  - bounded floor-plane repair
  - collision-gated validation
- The safety constraints are part of the method, not an afterthought.

### Risk 2: Baselines are not hard enough

Must add before a serious conference submission:

- Random / local move control under the same movement budget.
- Constraint optimization baseline:
  - relation loss
  - collision loss
  - movement loss
  - boundary loss
  - solved with coordinate search, scipy optimize, CMA-ES, or another gradient-free optimizer.
- Oracle parser upper bound under the final Floor-Prior protocol, not only older direct-repair diagnostics.

Purpose:

- Random/local move proves the gain is not from arbitrary perturbation.
- Constraint optimization tests whether Floor-Prior is stronger than a generic geometric optimizer.
- Oracle parser upper bound separates parser limitation from geometric repair limitation.

### Risk 3: Parser and matching are under-diagnosed

Add a table named:

`Relation Extraction and Matching Statistics`

Columns to include:

- room type
- number of instructions
- average parsed relations per instruction
- relation predicate counts
- object category matching success rate
- multi-instance scene rate
- nearest-pair matching failure cases
- parser precision / recall from a small manually checked sample if full annotation is not available

Purpose:

- Makes the relation-evaluation protocol less black-box.
- Helps reviewers trust that the metric is not inflated by parser quirks.

### Risk 4: Visual quality evidence is selected

Current selected showcase is useful but not enough as main evidence.

Need add:

- 50 or 100 random before-after renders.
- Average CLIP delta.
- SSIM.
- collision-pair delta.
- out-of-bound rate.
- object overlap rate.
- 6 to 8 success cases.
- 4 honest failure cases.

Interpretation boundary:

- We can claim selected and random visual diagnostics show no obvious degradation if numbers support it.
- We should not claim universal visual improvement without a human preference study or stronger perceptual protocol.

### Risk 5: Ablation needs to look complete

Already available:

- Direct repair.
- Floor-Prior repair.
- collision gate.
- max movement radius.
- multi-pass variants.
- overlap-weight variants.
- height preservation diagnostics.

Still useful to package clearly:

- without overlap penalty
- without movement bound
- without multi-pass repair
- without collision gate
- height-changing repair vs height-preserving repair
- different relation thresholds
- movement/relation/collision trade-off scatter plot

## Claim boundaries

Safe claims:

- Existing instruction-guided scene generators can exhibit final-layout relation grounding failures.
- A training-free, safety-aware verifier-repair framework improves explicit relation realization on the original InstructScene validation protocol.
- Height-preserving Floor-Prior repair avoids the floating-furniture failure observed in earlier direct repair.
- Collision-gated repair retains positive relation gains while controlling mesh collision pair rate.

Unsafe claims:

- first relation-aware 3D scene generation
- better than ReSpace or SDGScenes
- visual quality is universally better
- mesh collision always decreases for ungated repair
- handles all implicit commonsense relations
- solves affordance, support, reachability, or human usability

## Recommended submission route

The feedback suggests 3DV / WACV / SIGGRAPH Asia Technical Communications / Pacific Graphics style targets. Do not rely on the pasted deadline dates without rechecking official pages before planning, because conference dates can change.

Practical strategy:

- Main target: 3DV-style paper if the missing baselines and visual diagnostics are completed.
- Backup target: WACV-style vision/application framing.
- Short-form target: SIGGRAPH Asia Technical Communications-style contribution if strong-baseline reproduction remains incomplete.

## Next experiments to run

Priority order:

1. Random/local move control.
2. Constraint optimization baseline.
3. Oracle parser upper bound for final Floor-Prior.
4. Parser and matching statistics table.
5. Random visual-quality render/eval set.
6. Failure-case gallery.
7. Trade-off plot: movement vs relation accuracy, color or size by collision rate.

## Bottom line

The work is not dead. It becomes much more publishable if the story is shifted from "we moved furniture and the metric improved" to:

> We expose a graph-to-layout relation grounding gap in instruction-guided 3D indoor scene generation, then show that a reproducible safety-aware verifier-repair framework improves explicit relation realization while preserving height and controlling mesh collision.

