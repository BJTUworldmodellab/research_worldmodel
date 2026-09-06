# Paper content extension validation

Date: 2026-09-01  
Assessment: `READY_TO_SHARE_WITH_EXPLICIT_PROTOCOL_BOUNDARIES`

## Scope

This validation determines which existing ReSpace, SDGScenes, and RelScene materials can safely enter the anonymous Eurographics manuscript. It compares the frozen EG09 evidence with the archived H800 SDGScenes defensive-baseline package.

## Verified formal evidence

- Frozen formal protocol: 531 scenes, 808 target relations, 1,062 baseline/main layouts.
- Main method: collision-gated Floor-Prior, relation accuracy 0.639851.
- Original layout accuracy: 0.634901; paired interval includes zero.
- Three-seed exact movement-matched random mean: 0.625413; main-minus-control 95% CI is [0.7453, 2.2005] percentage points.
- Generic budget-matched optimizer: 0.6411; main-minus-control interval includes zero.
- Selected mesh collision-pair total: 1,061 versus 1,075 for the original layouts.

## Defensive-baseline data-quality check

The H800 SDGScenes-inspired archive contains three room summaries totaling 531 scenes, 708 targets, 641 horizontal targets, and 92 missing object-pair cases. Logged overlap pairs decrease from 894 to 833 and out-of-bounds centers remain zero. The weighted simple satisfaction values recompute to 0.41949 before and 0.79237 after; horizontal values recompute to 0.37598 and 0.78783.

These calculations are internally consistent, but the experiment is not an official SDGScenes reproduction. It uses archived relation inputs with 708 targets and a simple satisfaction metric, not the frozen 808-target independent evaluator. Mixing its numbers into the formal comparison table would create a denominator, metric, and method-identity mismatch.

## Manuscript decision

- Include a protocol-comparability table covering InstructScene, our method, same-protocol controls, ReSpace, SDGScenes, and RelScene.
- Keep ReSpace and SDGScenes as strong cross-protocol related systems with no superiority claim.
- Mention the SDGScenes-inspired H800 run only as a feasibility archive excluded from formal numerical ranking.
- Use the frozen generic optimizer as the same-protocol strong optimization control.
- Add exact evaluator thresholds, frozen-pair matching, control construction, and human-label alignment to make the paper more reproducible.

## Sources

- `docs/eurographics2027/claim_to_table_map_eg2027.md`
- `evaluation/independent_relation_evaluator.py`
- `scripts/run_eg06_movement_baselines.py`
- `docs/eurographics2027/eg05_independent_evaluator_report_20260805.md`
- `experiments/sdgscenes_baseline/exports/20260720_h800_sdgscenes_results/machine/summary.csv`
- `experiments/sdgscenes_baseline/exports/20260720_h800_sdgscenes_results/machine/run_metadata.json`
- InstructScene ICLR 2024 paper, ReSpace arXiv:2506.02459, SDGScenes Pattern Recognition 179:113674, and RelScene ACM MM 2024.
