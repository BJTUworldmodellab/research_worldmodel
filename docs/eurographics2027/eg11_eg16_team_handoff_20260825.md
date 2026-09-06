# EG11–EG16 team handoff (updated 2026-09-01)

## Executive status

The article-development phase now has a fresh six-page anonymous Eurographics manuscript, frozen scientific evidence, a citation audit, an anonymous reproduction package, and complete TeX/PDF QA. Per the author's 2026-09-01 decision, author information and submission are intentionally deferred. The earlier independent human review is complete for the five-page snapshot it reviewed; the expanded six-page manuscript would need a short delta review only if it is later promoted to submission candidate.

| Task | State | Outcome |
|---|---|---|
| EG11 | `EG11_FRESH_PDF_PASS` | The official source compiled with full TeX Live 2026 to a six-page A4 PDF; all-page visual QA passed. |
| EG12 | `EG12_CITATIONS_VERIFIED` | Primary-source citation and related-work claim audit passed. |
| EG13 | `EG13_ANONYMOUS_REPRO_PASS` | Dependency-free table reproduction, evaluator smoke test, anonymized package, and HTML validation report passed. |
| EG14 | `EG14_DONE_FOR_REVIEWED_SNAPSHOT` | Two machine audit rounds and the independent human ACCEPT receipt are recorded for the reviewed five-page snapshot. |
| EG15 | `EG15_DEFERRED_BY_AUTHOR` | Do not add identity-bearing author fields while article content is still being developed. |
| EG16 | `EG16_DEFERRED_BY_AUTHOR` | Do not register or submit in SRMv2 during the current article-development phase. |

The machine-readable source of truth is `results/independent_eval/eg2027/eg11_eg16_readiness_20260825/status.json`.

## Frozen evidence and allowed claims

- Evaluation population: 531 scenes and 808 target relations.
- Official InstructScene final-layout relation accuracy: 0.634901.
- Collision-gated Floor-Prior accuracy: 0.639851.
- Movement-matched random control mean: 0.625413.
- Main-minus-random gain: +1.4439 percentage points; canonical paired 95% CI [+0.7453, +2.2005] percentage points.
- Generic constrained optimizer: 0.6411. The main method does not establish superiority over this control.
- Collision-gate decisions: 492 repaired outputs and 39 baseline fallbacks.
- Selected mesh collision pairs: 1,061, versus 1,075 for the official baseline.

The supported comparative claim is limited to improvement over movement-matched random controls under the frozen InstructScene validation protocol. The +0.50 percentage-point point gain over the official baseline is not statistically conclusive under the paired interval. No claim of outperforming ReSpace, SDGScenes, generic optimization, or text-to-3D scene-generation SOTA is supported. No universal visual-quality, commonsense, affordance, reachability, or multi-seed generalization claim is supported.

## Completed deliverables

### EG11: source and formal qualitative evidence

- `paper/eurographics2027_submission/EGauthorGuidelines-conf-sub.tex`
- `paper/eurographics2027_submission/references.bib`
- `paper/eurographics2027_submission/figures/eg11_formal_qualitative.pdf`
- `paper/eurographics2027_submission/figures/eg11_formal_qualitative.png`
- `paper/eurographics2027_submission/figures/eg11_formal_qualitative_selection.json`
- `scripts/render_eg11_formal_qualitative.py`
- `docs/eurographics2027/eg11_template_anonymity_report_20260825.md`
- `docs/eurographics2027/eg11_fresh_pdf_qa_20260825.md`
- `paper/eurographics2027_submission/build/EGauthorGuidelines-conf-sub.pdf` (6 pages; SHA-256 `f418b82977664d40f786b8788e541b895effcfd8bcb58de89456fc91fb01157d`)

The deterministic panel contains one success case from each of bedroom, living room, and dining room, plus one remaining failure. Its caption explicitly prevents the layout visualization from being interpreted as photorealistic rendering or universal visual improvement.

### EG12: citation and claim audit

- `docs/eurographics2027/eg12_related_work_citation_audit_20260825.md`

The audit verifies InstructScene, ATISS, SceneFormer, DiffuScene, 3D-FRONT, 3D-FUTURE, CommonScenes, LayoutGPT, Holodeck, RelScene, ReSpace, and SDGScenes against primary publication records or official preprints. Cross-protocol systems remain contextual references rather than entries in the direct numerical ranking.

### EG13: anonymous reproduction and durable report

- `artifacts/eurographics2027/eg13_anonymous_repro.zip`
- ZIP bytes: 1,699,708
- ZIP SHA-256: `9315e98e2dd4d7035097e91561aaf1469f71da1960eb07bc3f8ebb68c1d41002`
- `artifacts/eurographics2027/eg13_anonymous_repro/MANIFEST.json`
- `docs/eurographics2027/eg13_anonymous_repro_report_20260825.md`
- `artifacts/eurographics2027/eg13_validation_report/report.html`
- `artifacts/eurographics2027/eg13_validation_report/artifact.json`
- `artifacts/eurographics2027/eg13_validation_report/report_queries.sql`
- `artifacts/eurographics2027/eg13_validation_report/report_source.sqlite`
- `artifacts/eurographics2027/eg13_validation_report/query_results.json`
- `artifacts/eurographics2027/eg13_validation_report/qa_receipt.json`

The anonymous package contains 28 manifested files. It has no detected author, repository, local-path, credential, cloud-host, commit, or branch disclosures. The layout-array semantic hashes are unchanged by sanitization. The report was checked at desktop and 390-pixel viewport widths; a small shared-reader chrome overflow is recorded as a non-content caveat.

### EG14–EG16: review and submission worksheets

- `docs/eurographics2027/eg14_internal_review_round1_20260825.md`
- `docs/eurographics2027/eg14_internal_review_round2_20260825.md`
- `docs/eurographics2027/eg14_uninvolved_human_review_form_20260825.md`
- `docs/eurographics2027/eg14_uninvolved_human_review_receipt_20260826.json`
- `docs/eurographics2027/ai_use_disclosure_author_input_20260825.md`
- `submission/eurographics2027/eg15_metadata_draft_20260825.json`
- `submission/eurographics2027/eg15_metadata_author_confirmation_20260825.md`
- `submission/eurographics2027/eg16_srmv2_abstract_registration_20260825.md`

## Verification receipt

The original review checks passed on 2026-08-25/26. The expanded paper was rebuilt and visually checked on 2026-09-01:

- Full TeX Live 2026 build through latexmk/pdfLaTeX/BibTeX: `PASS`; current PDF is 6-page A4.
- All-page rendered PDF visual QA: `PASS`; no clipping, missing content, black boxes, unresolved references, or visible font substitution.
- Independent uninvolved human review: `ACCEPT`, recorded 2026-08-26 for the five-page reviewed snapshot; not silently transferred to later content edits.
- Python syntax compilation for all new EG11–EG16 scripts.
- Repository unit tests: 20 tests, 0 failures, 0 errors.
- Main-table reproduction: `PASS`.
- Independent evaluator smoke test: 4 relations checked, `PASS`.
- Anonymous package build and validation: `PASS` with zero anonymity findings.
- HTML report SQLite source rematerialization and snapshot comparison: `PASS`.
- ZIP deterministic rebuild: SHA-256 unchanged.
- Git whitespace check: no errors.

The exact data checks include 1,062 EG05 rows, 3,186 EG06 rows, zero duplicate composite keys, zero coverage errors, 16,599 movement-matched random comparisons with maximum numerical difference `4.44e-16` m, and 5,533 generic-budget comparisons with zero excess.

## Deferred submission inputs

No action is requested now. When the author later restarts submission preparation, the required order is: confirm author metadata and AI disclosure; perform a delta review of the then-current PDF; resolve repository anonymity; register the abstract in SRMv2; then insert the system-generated submission ID.

Official timing recorded in the EG16 worksheet:

- Abstract registration: 2026-09-25 23:59 UTC (2026-09-26 07:59 China Standard Time).
- Full paper: 2026-10-01 23:59 UTC (2026-10-02 07:59 China Standard Time).

## Compute decision

No AutoDL GPU rental is required to finish the currently defined EG11–EG16 tasks. The remaining work is author metadata, disclosure, registration, and repository-anonymity governance. Rent GPU compute only if the team expands the scope to new scene generation, additional seeds, new baselines, or fresh mesh-render experiments.

## Do-not-submit / do-not-publish boundary

- Do not submit the old NeurIPS `main.pdf`.
- Do not treat a failed or partial TeX build as the fresh Eurographics PDF.
- Do not place confirmed author metadata, correspondence email, SRMv2 ID, or identity-bearing AI-use records on a public anonymous branch.
- Do not rank ReSpace or SDGScenes in the direct-comparison table unless input, output, split, seed, threshold, and evaluator are aligned.
- Do not claim SOTA, superiority over the generic optimizer, universal visual improvement, or broader reasoning abilities.

