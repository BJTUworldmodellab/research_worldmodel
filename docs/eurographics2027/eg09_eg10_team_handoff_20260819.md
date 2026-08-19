# Eurographics 2027 EG09–EG10 Team Handoff

Date: 2026-08-19

Branch: `agent/eg01-eg02-eurographics2027`

Scope decision: EG11 will not be performed by the current owner.

## Executive status

| Work package | Status | Meaning |
|---|---|---|
| EG09 | `EG09_CLAIMS_FROZEN` | Formal EG07 results and EG08 paired statistics have been transferred into the active manuscript and claim map. The supported and unsupported claims are frozen and machine checked. |
| EG10 | `EG10_PRECHECK_BLOCKED` with integrity `PASS` | The submission-readiness audit is complete and the official EG2027 template has been verified and migrated into a separate submission source. The paper is not yet submission-ready because five author/build decisions remain. |
| EG11 | Out of scope | No EG11 work is included or promised in this handoff. |

The handoff is therefore ready for a teammate to continue. EG10 must not be reported as a final submission `PASS`.

## EG09 completed work

EG09 freezes the paper-facing result identity to the formal EG07/EG08 evidence:

- 531 scenes, 1,062 layouts, and 808 explicit target relations.
- Collision-gated Floor-Prior relation accuracy: `0.639851`.
- Original-layout baseline: `0.634901`.
- Three-seed exact movement-matched random mean: `0.625413`.
- Primary supported gain: `+1.4439` percentage points.
- Frozen paired scene-level bootstrap 95% CI: `[+0.7453, +2.2005]` percentage points.
- Gate accounting: 492 repaired layouts selected and 39 baseline fallbacks.
- Mesh evidence: 1,061 selected-layout collision pairs versus 1,075 in the original layouts.

Allowed claim: the main method outperforms the three-seed mean of exact movement-matched random controls under the frozen paired protocol.

Claims that remain unsupported:

- superiority over the original baseline;
- superiority over the generic relation optimizer;
- statistically positive improvement in every room;
- collision-free or globally plausible generation;
- superiority over external methods without a shared protocol.

EG09 evidence:

- `docs/eurographics2027/eg09_paper_claim_freeze_report_20260817.md`
- `docs/eurographics2027/claim_to_table_map_eg2027.md`
- `manifests/eurographics2027/eg09_paper_claim_freeze_manifest.json`
- `results/independent_eval/eg2027/eg09_paper_claim_freeze_20260817/`
- `scripts/check_eg09_paper_claim_consistency.py`
- `tests/test_eg09_paper_claim_consistency.py`

Local EG09 commit: `d491c1971dcb86ff8d724b7b30e300323a388791` (`Complete EG09 paper claim freeze`).

## EG10 completed work

The following EG10 work is complete:

- Three-reviewer submission-readiness audit and cross-review synthesis.
- Citation-key, cross-reference, identity-string, stale-number, and claim-boundary checks.
- Removal or narrowing of unsupported wording in the manuscript.
- Verification of the official SRMv2 archive
  `egPublStyle-EG-full-short-star-tut-poster-edu-dc-2027.zip`:
  - bytes: `2902816`;
  - SHA-256: `68212ff42cee3681c8b7aa620e6c55529153cbb3001039cdb8f8256429c949b2`;
  - required entry confirmed: `EGauthorGuidelines-conf-sub.tex`;
  - conference style confirmed: `eg2027.sty`.
- Separate EG2027 submission source created at
  `paper/eurographics2027_submission/EGauthorGuidelines-conf-sub.tex`.
- The migrated source uses `egpubl`, `eg2027`, `\ConferenceSubmission`, and
  `eg-alpha-doi`.
- Machine preflight integrity status: `PASS`.
- Relevant regression tests: 16 passed.

EG10 evidence:

- `docs/eurographics2027/eg10_submission_readiness_review_20260817.md`
- `manifests/eurographics2027/eg10_submission_readiness_manifest.json`
- `results/independent_eval/eg2027/eg10_submission_readiness_20260817/preflight.json`
- `scripts/check_eg10_submission_readiness.py`
- `tests/test_eg10_submission_readiness.py`
- `paper/eurographics2027_submission/`

The first EG10 audit commit is
`e0f89c167aece750424ba7e0885243b4aa5eaee5` (`Add EG10 submission readiness audit`).
The official-template verification and migration performed on 2026-08-19 are
currently working-tree changes and require a new reviewed commit before sharing
through Git.

## EG10 remaining blockers and ownership

| Blocker | Required action | Owner |
|---|---|---|
| `PUBLIC_REPOSITORY_ANONYMITY_RISK` | Make the identified repository private or move submission artifacts to an identity-safe anonymous repository; audit public traces before submission. | Authors / repository owner |
| `CCS_CATEGORIES_MISSING` | Select verified ACM CCS 2012 categories and add them to the submission source. Also add at least one keyword in SRMv2. | Authors |
| `SUBMISSION_ID_PENDING` | Register the abstract and replace the `SUBMISSION ID` placeholder with the assigned SRMv2 ID. | Authors |
| `PDF_STALE` | Compile the migrated EG2027 source, inspect every page, verify fonts/images/page count, and create a new submission PDF. | Build owner |
| `AI_DISCLOSURE_AUTHOR_INPUT_NEEDED` | Confirm the exact AI tools, models/versions, purposes, and human verification, then add an accurate disclosure. Do not invent missing details. | Authors |

Scientific risks to keep visible:

- no formal before/after qualitative result figure;
- generic optimizer comparison is inconclusive and has a slightly higher point estimate;
- original-baseline comparison is inconclusive;
- one generator seed and one generator pipeline;
- no human visual study.

## Important file and delivery warnings

- Do **not** submit `paper/neurips_ra_instructscene/main.pdf`. It predates EG09 and contains stale development-era content.
- Treat `paper/eurographics2027_submission/EGauthorGuidelines-conf-sub.tex` as the active submission source after the pending migration changes are committed.
- Keep the original template package and its checksum as provenance; do not replace the 2027 package with the generic public CGF template.
- The extracted official package is archived at `paper/eg2027_official_style/`.
- Keep all author names, affiliations, repository links, supplementary materials, and acknowledgements anonymous during review.
- Do not publish or push additional submission artifacts to the currently public identity-bearing repository until the anonymity decision is resolved.

## Git synchronization state at handoff

- Local branch HEAD: `e0f89c167aece750424ba7e0885243b4aa5eaee5`.
- Locally recorded remote-tracking branch:
  `cee93138027e7fec2a2162034164c2dcc2e90a16`.
- Consequently, the recorded remote does not yet contain the EG09 and EG10 commits.
- The 2026-08-19 official-template migration also has uncommitted working-tree changes.

Before any push, the teammate should first resolve the public-repository
anonymity decision, review the pending diff, rerun EG09/EG10 checks, and create
one atomic migration commit.

## Recommended continuation order

1. Resolve private-versus-anonymous repository handling.
2. Review and commit the current official-template migration.
3. Register the abstract and obtain the SRMv2 submission ID.
4. Supply verified CCS categories, SRMv2 keyword, and exact AI disclosure.
5. Add the formal qualitative result figure if the author team accepts that scope.
6. Compile the new EG2027 PDF and perform visual/submission checks.
7. Rerun `check_eg09_paper_claim_consistency.py` and
   `check_eg10_submission_readiness.py`; only report submission readiness when
   EG10 has no hard blockers.

## Handoff acceptance statement

The receiving teammate can accept EG09 as completed and claim-frozen. The
receiving teammate should accept EG10 as an integrity-clean, partially completed
submission-preparation package with the five blockers above, not as a finished
submission. No EG11 responsibility transfers from the current owner.
