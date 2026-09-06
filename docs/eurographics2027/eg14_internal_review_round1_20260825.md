# EG14 internal review — round 1 technical audit

Date: 2026-08-25  
Reviewer role: machine-assisted technical reviewer, not a substitute for the required uninvolved human reviewer  
Decision: `REVISION_COMPLETED_WITH_COMPILE_BLOCKER`

## Overall assessment

The scientific claim is appropriately narrow and the frozen numbers reconcile with saved evidence. The draft does not claim superiority over the original baseline, generic optimizer, ReSpace, or SDGScenes. The most material gaps were submission presentation and citation context rather than experimental calculation.

## Findings and disposition

| Priority | Finding | Evidence/risk | Disposition |
|---|---|---|---|
| High | No fresh EG2027 PDF after source migration | Old PDF could be submitted accidentally; no final page/layout inspection | BLOCKED until full TeX Live compile and PDF QA |
| Medium | No deterministic formal success/failure figure | Text-only evidence is harder to audit and invites cherry-picking concerns | FIXED with frozen-layout selection rule, vector PDF, RGB PNG, selection manifest |
| Medium | RelScene missing from relation-evaluation context | Reviewers could reasonably ask why a relation benchmark is absent | FIXED in Related Work and bibliography |
| Medium | ReSpace citation title had drifted from current arXiv v6 | Bibliographic mismatch weakens citation audit | FIXED to current title and arXiv DOI |
| Medium | CCS categories and keywords absent | Explicit EG10 blocker | FIXED in official template source |
| Medium | Lightweight evidence package was described but not independently runnable | Reproducibility claim lacked one-command proof | FIXED by EG13 package, main-table rebuild, and evaluator smoke test |
| Low | Qualitative evidence could be misread as visual-quality proof | Top-down rectangles do not show mesh appearance | FIXED by caption and discussion boundary |

## Claim audit

### Supported

- Collision-gated Floor-Prior reaches 0.639851 relation accuracy on the frozen 531-scene, 808-relation protocol.
- It exceeds the three-seed movement-matched random mean by 1.443894 percentage points with a positive frozen paired CI.
- Every random-control object's XZ movement magnitude matches the main variant's corresponding object magnitude within numerical tolerance.
- Selected layouts have 1,061 aggregate FCL collision pairs versus 1,075 for original layouts.

### Not supported and not claimed

- statistical superiority to original InstructScene;
- superiority to the generic budget-matched optimizer;
- superiority to ReSpace, SDGScenes, or RelScene;
- universal mesh or perceptual quality improvement;
- complete commonsense, affordance, reachability, or support reasoning;
- end-to-end generator reproducibility from the lightweight supplement alone.

## Required before round-1 closure

- [x] citations and current publication titles verified;
- [x] deterministic formal figure generated and hashed;
- [x] CCS and keywords added;
- [x] anonymous one-command reproduction passes;
- [ ] fresh official-template PDF compiles;
- [ ] PDF page count, floats, tables, references, and overfull boxes inspected.

Round 1 remains formally open only on the fresh-PDF toolchain gate.
