# EG-09 Formal Paper Result and Claim Freeze

Date: 2026-08-17

Branch: `agent/eg01-eg02-eurographics2027`

Input commit: `cee93138027e7fec2a2162034164c2dcc2e90a16`

## Verdict

**EG09_CLAIMS_FROZEN**

The active manuscript and Eurographics 2027 claim map now use the formal EG07
results and the accepted EG08 paired statistical protocol. Development anchors
from EG01 and EG04 remain in their historical audit files but are excluded from
the current paper-facing claims.

## One-sentence paper argument

In instruction-guided 3D indoor scene generation, a training-free
collision-gated Floor-Prior uses relation-aware repair directions that improve
realized relation accuracy over exact movement-matched random controls on a
frozen 531-scene evaluation, while aggregate mesh-collision pairs do not exceed
the original layouts; superiority over the original baseline and a generic
optimizer remains unresolved.

## Terminology ledger

| Canonical term | Definition / use | Rejected drift |
|---|---|---|
| Collision-gated Floor-Prior | paper-facing main method | Direct Repair as main method |
| realized relation accuracy | satisfied targets divided by all explicit targets, including missing targets in the denominator | conditional-only accuracy |
| exact movement-matched random controls | random directions with each object's XZ movement magnitude preserved | generic random baseline |
| generic relation optimizer | budget-matched EG06 optimizer | strong-baseline superiority shorthand |
| paired scene-level percentile bootstrap | frozen EG08 uncertainty protocol | unpaired or relation-row resampling |
| FCL mesh-collision pairs | aggregate mesh safety count | collision-free rate |

## Formal result now in the paper

- Scope: 531 scenes, 1,062 layouts, and 808 explicit target relations.
- Main accuracy: 0.639851; original baseline: 0.634901.
- Three-seed movement-matched random mean: 0.625413.
- Primary gain: +1.4439 percentage points.
- Frozen paired 95% CI: [+0.7453, +2.2005] percentage points.
- Gate accounting: 492 repairs selected and 39 baseline fallbacks.
- Mesh safety: chosen main 1,061 collision pairs versus baseline 1,075.

## Claim-evidence map

| Claim | Evidence | Status |
|---|---|---|
| Main exceeds exact movement-matched random mean | EG06 per-scene table + EG08 canonical paired CI | supported |
| Gate does not worsen aggregate collision pairs | EG07 final metrics, 1,061 <= 1,075 | supported |
| Main exceeds original baseline | point gain +0.495 pp, CI includes zero | not established |
| Main exceeds generic optimizer | point gain -0.124 pp, CI includes zero | not established |
| Every room improves significantly | living-room sensitivity lower bound equals zero | not established |
| Full generator-to-statistics reproduction from lightweight package | original three room JSON files absent | incomplete provenance |

## Active changes

- Replaced stale EG01 result claims and tables in
  `paper/neurips_ra_instructscene/main.tex` with formal EG07/EG08 results.
- Rebuilt `docs/eurographics2027/claim_to_table_map_eg2027.md` as the formal
  claim-to-evidence map.
- Added `manifests/eurographics2027/eg09_paper_claim_freeze_manifest.json`.
- Added a machine check and regression tests for result identity, claim
  boundaries, and stale-number leakage.

## Historical preservation policy

EG01 through EG04 files, frozen configurations, archived visual reports, and
development diagnostics were not rewritten. They document how the method and
numbers evolved. The EG09 checker limits its no-stale-number rule to the active
paper and the pre-boundary part of the formal claim map.

## Verification

- EG09 machine consistency status: `EG09_CLAIMS_FROZEN`, zero errors.
- Relevant regression suite: 12 tests passed (independent evaluator, EG08
  paired statistics, and EG09 paper-claim consistency).
- Git whitespace/error check: passed.
- LaTeX source structure: four table environments and all checked
  `begin`/`end` pairs are balanced; removed table labels have no remaining
  references.
- PDF compilation: not run because no TeX engine is installed in the current
  workspace. The existing PDF was inspected and explicitly excluded as stale.

## Reviewer-facing boundaries

- The primary supported superiority claim is only against the three-seed mean
  of exact movement-matched random controls.
- Comparisons with the original baseline and the generic optimizer are
  inconclusive.
- Collision evidence supports aggregate non-worsening, not collision-free
  generation.
- Room-level intervals are sensitivity analyses, not separate acceptance gates.
- No superiority claim is made against ReSpace, SDGScenes, or another external
  system without a shared protocol.

## Remaining work outside EG09

- Recompile `paper/neurips_ra_instructscene/main.tex`. The tracked `main.pdf` is
  a pre-EG09 binary whose pages 6 and 8 still contain development-anchor tables;
  it is explicitly excluded from EG09 delivery.
- Select and apply the final Eurographics submission template; the current
  source still uses its earlier NeurIPS-style wrapper.
- Decide whether the three original room-level generator JSON files can be
  archived for complete end-to-end provenance.
- Perform the final figure, reference, page-limit, and venue-checklist pass.
