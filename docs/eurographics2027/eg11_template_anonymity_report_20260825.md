# EG11 Eurographics template and anonymity report

Date: 2026-09-01 (updated after the paper-content extension)  
State: `EG11_FRESH_PDF_PASS`

## Outcome first

The paper source uses the archived official Eurographics 2027 conference-submission template and contains submission-safe author placeholders, three ACM CCS categories, keywords, a protocol-comparability table, and a deterministic formal before/after layout figure generated from frozen EG07 evidence. Source-level anonymity checks pass. The official source compiled to a fresh six-page A4 PDF and passed all-page visual QA. The older NeurIPS `main.pdf` remains explicitly prohibited for submission.

## Template and paper changes

- Root source: `paper/eurographics2027_submission/EGauthorGuidelines-conf-sub.tex`
- Official template archive: `paper/eg2027_official_style/`
- Anonymous author field: `SUBMISSION ID`
- CCS categories:
  - Computing methodologies → Computer graphics
  - Computing methodologies → Spatial and physical reasoning
  - Computing methodologies → Scene understanding
- Keywords: 3D indoor scene generation; spatial relations; layout repair; geometric verification
- Formal figure: `paper/eurographics2027_submission/figures/eg11_formal_qualitative.pdf`
- Figure selection record: `paper/eurographics2027_submission/figures/eg11_formal_qualitative_selection.json`

## Deterministic figure rule

For each of bedroom, living room, and dining room, select the lexicographically first evaluated baseline-fail/main-pass relation whose layout has nonzero XZ movement. Add the lexicographically first evaluated baseline-fail/main-fail relation for which the collision gate selected a nonzero-movement repair. This yields three successes and one remaining failure without manual visual cherry-picking.

The figure is a floor-plane diagnostic, not a photorealistic mesh render. Its caption explicitly rejects universal visual-quality interpretation.

## Anonymity and submission checks

| Check | Result | Notes |
|---|---|---|
| Author names/affiliations removed | PASS | `SUBMISSION ID` placeholder only |
| Public repository URL absent from manuscript | PASS | No repository link in TeX/BibTeX/figure selection record |
| Local/cloud paths absent from manuscript assets | PASS | Figure manifest stores repository-relative paths |
| Credentials or private keys absent | PASS | No PAT/API/private-key patterns |
| Raster transparency | PASS | Formal PNG is RGB; PDF is vector |
| Official template selected | PASS | `egpubl` + `eg2027` + `\ConferenceSubmission` |
| Fresh PDF compile | PASS | TeX Live 2026, latexmk, pdfLaTeX, and BibTeX completed successfully |
| Page-count and visual PDF QA | PASS | Six pages inspected; no clipping, missing pages, black boxes, unresolved references, or visible font substitution |

## Compile and QA evidence

The fresh output is `paper/eurographics2027_submission/build/EGauthorGuidelines-conf-sub.pdf` (6 A4 pages, 196,198 bytes, SHA-256 `f418b82977664d40f786b8788e541b895effcfd8bcb58de89456fc91fb01157d`). TeX Live 2026, latexmk 4.87, pdfLaTeX, and BibTeX completed successfully.

Every page was rendered at 160 dpi and inspected. Non-fatal box warnings in the log do not produce visible clipping or margin escape. The detailed receipt is `docs/eurographics2027/eg11_fresh_pdf_qa_20260825.md`.

EG11 is therefore marked `EG11_FRESH_PDF_PASS`. Author metadata and SRMv2 submission are intentionally deferred. The independent human ACCEPT receipt remains valid for its reviewed five-page snapshot; the revised six-page snapshot should receive another human pass only if it later becomes the submission candidate.
