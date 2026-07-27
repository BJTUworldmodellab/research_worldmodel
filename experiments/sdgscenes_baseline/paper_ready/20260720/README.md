# SDGScenes defensive baseline paper-ready package

Updated: 2026-07-20, Asia/Shanghai

This folder turns the SDGScenes defensive-baseline run into paper-facing material. It does not modify the raw experiment archive. All numbers are copied or derived from the saved machine-readable package under:

`../sdgscenes_defensive_baseline/exports/20260720_h800_sdgscenes_results/machine/`

## Deliverables

- `paper_experiment_section.md`  
  English experiment-section draft, written with claim-safe wording for the paper.

- `paper_tables.md`  
  Three paper tables in Markdown: direct same-protocol results, SOTA protocol comparison, and SDGScenes defensive-baseline evidence.

- `paper_tables.tex`  
  LaTeX versions of the same three tables.

- `notion_update_draft.md`  
  Chinese Notion update draft that can be pasted into the cloud experiment page.

## Source files used

- `summary.csv`: H800 SDGScenes-inspired defensive smoke baseline summary.
- `per_scene.csv`: scene-level smoke-baseline records.
- `archived_floor_prior_results.csv`: archived same-protocol Floor-Prior results.
- `archived_collision_gated_results.csv`: archived collision-gated variant results.
- `sota_protocol_comparison.csv`: protocol comparability matrix.
- `protocol_boundary.md`: direct-comparison boundary and reviewer-facing policy.
- `official_feasibility.md`: official SDGScenes reproduction feasibility audit.
- `reported_results_context.md`: policy for using official reported results if found later.
- `related_work_wording.md`: claim-safe related-work and experiment wording.

## Claim policy encoded in this package

Allowed:

- Under the official InstructScene validation protocol, the final-layout verifier-repair improves realized relation grounding over the official InstructScene output.
- SDGScenes and ReSpace are strong related systems, but they are reported as non-direct references unless same-split, same-input, same-output, same-evaluator reproduction succeeds.
- The verifier-repair layer can potentially be plugged into other generators when their outputs expose object layouts.

Disallowed:

- Outperforming SDGScenes or ReSpace.
- State-of-the-art text-driven 3D scene generation.
- First relation-aware 3D scene generation.
- Universal visual-quality improvement.
- Complete commonsense, affordance, or reachability reasoning.

