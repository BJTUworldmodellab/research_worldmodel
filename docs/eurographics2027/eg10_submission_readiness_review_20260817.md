# EG-10 Eurographics 2027 Submission-Readiness Review

Date: 2026-08-17

Branch: `agent/eg01-eg02-eurographics2027`

Input commit: `d491c1971dcb86ff8d724b7b30e300323a388791`

## Review setup

- **Input scope:** complete current manuscript source, bibliography, stale
  compiled PDF, EG07 formal evidence, EG08 paired statistics, and EG09 claim
  freeze. The GitHub repository visibility was checked read-only and is PUBLIC.
- **Assessment boundary:** this is a pre-submission stress test, not an
  editorial decision. The official EG2027 template package is available only
  after SRMv2 login and was not accessible in this workspace. The public CGF
  template was inspected only as a structural reference and was not substituted
  for the conference-specific package.
- **Shared manuscript claim summary:** Collision-gated Floor-Prior is a
  training-free final-layout relation-control layer. On 531 InstructScene
  validation scenes, it improves realized relation accuracy over the mean of
  three exact movement-matched random controls by 1.44 percentage points (95%
  paired bootstrap CI, 0.75 to 2.20 points), while the selected layouts have
  1,061 aggregate FCL collision pairs versus 1,075 for the original layouts.
- **Visible evidence base:** 531 scenes, 808 target relations, independent
  evaluator, complete EG05/EG06 per-scene tables, matched-movement audit,
  paired bootstrap uncertainty, gate accounting, and collision totals.
- **Missing materials affecting confidence:** no formal before/after rendered
  result figure, no human visual study, one generator seed and one generator
  pipeline, no original room-level generator JSON archive, no migrated EG2027
  source, and no fresh compiled PDF.

### Official EG2027 constraints checked

| Requirement | Official rule | Current state |
|---|---|---|
| Submission source | Use `EGauthorGuidelines-conf-sub.tex` from the EG2027 package | BLOCKED: package requires SRMv2 login |
| Review mode | Double-blind main paper and supplements | PARTIAL: author block is anonymous, but official submission-ID form is not used |
| Public trace | Public code/data repositories must not reveal author identity | BLOCKED: the project repository is PUBLIC under an identifiable organization |
| Length | Research papers recommended up to 10 CGF-style pages, excluding references | UNKNOWN until EG template compilation |
| PDF | Main submission must be PDF | BLOCKED: tracked PDF is pre-EG09 and stale |
| Categories | At least one keyword in SRMv2; template expects ACM CCS categories | BLOCKED: author choice and submission record pending |
| Images | Embedded images must not contain transparent pixels | NOT YET APPLICABLE: no result images are included |
| Upload | Maximum 500 MB for all submission files | LIKELY PASS, but final package not assembled |
| AI use | Authors retain responsibility; generative-AI use requires transparent disclosure | AUTHOR_INPUT_NEEDED for exact tools, models, versions, and uses |

Official sources:

- [EG2027 Full Papers instructions](https://srmv2.eg.org/COMFy/Conference/EG_2027/Instruction)
- [EG2027 submission deadlines](https://srmv2.eg.org/COMFy/Conference/EG_2027)
- [EG2027 Call for Full Papers and anonymity policy](https://eg2027.isti.cnr.it/call-for-papers/)
- [Eurographics publication guidelines](https://www.eg.org/wp/eurographics-publications/guidelines/)

## Reviewer 1

- **Overall assessment:** The evidentiary chain is considerably stronger after
  EG07--EG09, and the statistical claim is now correctly bounded. However, the
  paper does not yet establish that the method yields a practically meaningful
  improvement over the generator or a generic budgeted optimizer.
- **Who would be interested in the results, and why:** Researchers building
  text- or graph-conditioned 3D scene generators may value the separation
  between symbolic relation correctness and final geometric realization, and
  the independent evaluator may be reusable for diagnosing this gap.
- **Major strengths:** frozen 531-scene scope; independent evaluator; explicit
  missing-target accounting; exact movement-matched controls; paired scene-level
  intervals; complete gate accounting; honest non-superiority boundaries.
- **Major concerns:** the +0.50-point difference from the original baseline is
  inconclusive; the generic optimizer has a slightly higher point estimate;
  the principal positive comparison is against randomized directions; the run
  uses one generator seed and one generator; aggregate collision pairs do not
  establish visual or functional quality.
- **Technical failings that need to be addressed before the case is
  established:** provide formal-scene qualitative examples tied to the frozen
  layouts; explain the candidate score and parser rules precisely enough for
  reimplementation; justify why the movement-matched random mean is the primary
  inferential comparator; add robustness across generator seeds or another
  pipeline if the claim is intended to generalize; preserve the raw generator
  provenance where possible.
- **Assessment against Nature-style criteria:** originality is plausible as a
  focused diagnostic-and-control contribution, but not yet distinguished as a
  strong algorithmic advance; scientific importance is field-local; technical
  soundness of the reported statistic is good, while practical validity remains
  incomplete; interdisciplinary reach is limited; specialist readability is
  good, but reproducibility details remain compressed.
- **Recommendation posture:** promising evidence package, but major technical
  revision is needed before a strong full-paper case is established.

## Reviewer 2

- **Overall assessment:** The most defensible contribution is the formalization
  and measurement of a graph-to-layout grounding gap, not a claim that the
  proposed optimizer is broadly superior. The manuscript should foreground this
  diagnostic insight and treat Floor-Prior as one controlled intervention.
- **Who would be interested in the results, and why:** Computer-graphics and
  embodied-AI researchers working on controllable scene generation may care
  because intermediate symbolic compliance can overstate final-layout
  instruction fidelity.
- **Major strengths:** the paper explicitly avoids first-method and external
  superiority claims; it distinguishes target satisfaction from geometric side
  effects; the independent relation tables enable further paired analysis.
- **Major concerns:** bounded geometric post-processing is not obviously novel
  relative to generic constrained optimization; the generic comparator is not
  beaten; the effect over the original generator is small; evaluation on a
  single pretrained system limits scientific importance; related-work
  positioning is descriptive rather than a sharp novelty contrast.
- **Technical failings that need to be addressed before the case is
  established:** articulate which component is non-obvious beyond generic
  constraint projection; add an ablation that isolates the Floor-Prior design
  using the formal evaluator; show whether the diagnostic conclusion holds on
  another generator or checkpoint seed; include formal failure-case analysis.
- **Assessment against Nature-style criteria:** originality is currently
  moderate and narrow; outstanding importance is not established;
  interdisciplinary reach is possible through instruction-following evaluation
  but not demonstrated; the formal statistics are technically careful;
  nonspecialist framing is understandable but the significance remains modest.
- **Recommendation posture:** technically interesting as a diagnostic study,
  but the full-paper significance case remains underdeveloped.

## Reviewer 3

- **Overall assessment:** The argument is more honest and readable than the
  earlier draft, but the submission is visually and procedurally incomplete for
  a computer-graphics venue.
- **Who would be interested in the results, and why:** Readers interested in
  instruction faithfulness, scene-graph decoding, and evaluation methodology
  can understand the problem quickly and may reuse the claim boundaries.
- **Major strengths:** the abstract states the comparator, sample size, effect,
  interval, safety count, and limitation; terminology is mostly stable; the
  Discussion does not conceal the generic-optimizer result.
- **Major concerns:** the only figure is a pipeline schematic; there is no
  before/after 3D result, failure case, or visual explanation of a repaired
  relation; `Floor-Prior` remains abstract without a concrete scene example;
  the current source and PDF visibly belong to another venue; the public
  identity-bearing repository conflicts with the stated double-blind policy;
  CCS categories, submission ID, keyword selection, and AI disclosure are
  unresolved.
- **Technical failings that need to be addressed before the case is
  established:** add a formal qualitative figure with scene IDs and auditable
  selection criteria; provide a compact relation-verification illustration;
  migrate to the official two-column template; compile and inspect every page;
  check fonts, transparency, table width, references, anonymity, and page count.
- **Assessment against Nature-style criteria:** originality and technical
  soundness are legible to specialists; broad scientific importance is not
  established; the prose is accessible, but the absence of result visuals is a
  major barrier for nonspecialists and graphics reviewers.
- **Recommendation posture:** not submission-ready; presentation and visual
  evidence require substantial completion even if no new metric is added.

## Cross-review synthesis

- **Consensus strengths:** the formal evidence identity is stable; paired
  statistics and movement matching are auditable; claims are now appropriately
  bounded; collision-gate accounting is complete.
- **Consensus technical risks:** no formal qualitative result figure; single
  generator seed/pipeline; inconclusive original-baseline and generic-optimizer
  comparisons; incomplete raw provenance; method details are not yet sufficient
  to make the practical case self-evident.
- **Where emphasis differs across reviewers:** Reviewer 1 gives greatest weight
  to inferential and validation depth; Reviewer 2 to novelty and significance;
  Reviewer 3 to graphics-specific visual communication and submission format.
- **Broad-interest / significance readout:** the graph-to-layout diagnostic is
  potentially useful beyond this method, but the current evidence supports a
  narrow field-specific conclusion rather than a far-reaching advance.
- **Most important issues to resolve before a strong case is established:**
  close the public-repository anonymity risk; obtain the official EG2027
  template; produce a fresh compliant PDF; add formal qualitative evidence;
  settle the exact AI disclosure; sharpen the contribution around diagnostic
  insight rather than optimizer superiority; decide whether additional seed or
  cross-generator evidence is feasible before the deadline.

### EG10 decision

**EG10_PRECHECK_BLOCKED**

Evidence integrity is PASS. Submission readiness is blocked by seven mechanical
items and one author-input item:

1. the GitHub repository is public and identity-bearing, conflicting with the
   EG2027 anonymity rule for submission-related code/data repositories;
2. official EG2027 template package unavailable without SRMv2 login;
3. source not migrated to `EGauthorGuidelines-conf-sub.tex`;
4. bibliography style not migrated;
5. CCS categories not selected;
6. SRMv2 submission ID not yet available;
7. PDF is stale and cannot be delivered;
8. exact generative-AI disclosure requires author confirmation.

The abstract deadline is 2026-09-25 23:59 UTC and the full-paper deadline is
2026-10-01 23:59 UTC. Abstract registration should therefore happen before the
format migration is finalized so that the real submission ID can be inserted.

## Risk / unsupported claims

- Do not claim statistically established improvement over the original
  InstructScene baseline.
- Do not claim superiority over the budget-matched generic optimizer.
- Do not present aggregate collision-pair non-worsening as visual quality,
  functional plausibility, or collision-free generation.
- Do not reuse historical qualitative examples unless their layouts and metrics
  are tied to the formal EG07 artifact identity.
- Do not distribute the tracked `main.pdf`; it contains pre-EG09 tables.
- Do not submit while the identity-bearing project repository remains public;
  audit branch names, repository ownership, commit metadata, links, and cached
  public traces before claiming double-blind compliance.
- Do not use the public generic CGF template as if it were the EG2027-specific
  package.
- `AUTHOR_INPUT_NEEDED`: confirm the exact generative-AI tools, model names or
  versions, purposes, and human-review process before adding the disclosure.
