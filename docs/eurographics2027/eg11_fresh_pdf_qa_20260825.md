# EG11 fresh Eurographics PDF QA

Date: 2026-09-01 (updated after the paper-content extension)  
State: `EG11_FRESH_PDF_PASS`

## Outcome

The official Eurographics 2027 conference-submission source compiled successfully with the Codex-managed full TeX Live 2026 toolchain. The resulting six-page A4 PDF passed an all-page visual inspection. It supersedes the old NeurIPS PDF for review, but it is intentionally not being prepared for submission: author information and SRMv2 registration are deferred by the author.

## Build receipt

- Source: `paper/eurographics2027_submission/EGauthorGuidelines-conf-sub.tex`
- Output: `paper/eurographics2027_submission/build/EGauthorGuidelines-conf-sub.pdf`
- Engine: pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026)
- Driver: latexmk 4.87 with BibTeX
- Pages: 6
- Page size: A4
- Bytes: 196,198
- PDF SHA-256: `f418b82977664d40f786b8788e541b895effcfd8bcb58de89456fc91fb01157d`
- TeX SHA-256: `14a6d19ae5f148c8763bae742c6b9723fea9a8e4028353078139a6e448c9d0ac`
- Bibliography SHA-256: `055be9a570443fc4e8cd5326ec59c9c70045796a0eb8f3e7d0ecd86ba438542d`
- Current TeX build log: `paper/eurographics2027_submission/build/EGauthorGuidelines-conf-sub.log`
- Earlier `compile-final.*.log` files describe the prior five-page build and remain local historical logs.

## Visual inspection

Every page was rendered to PNG at 160 dpi and inspected. The title block, abstract, two-column flow, equations, algorithm, protocol-comparability table, formal before/after figure, three formal result/accounting tables, discussion, limitations, reproducibility notes, and references are present and readable. No clipping, missing pages, black boxes, unresolved references, missing citations, or visible font substitution was found. The deterministic qualitative panel is intentionally a compact floor-plane diagnostic rather than a photorealistic render.

The final build log contains only non-fatal underfull-box diagnostics in narrow table cells; the previous two overfull boxes were removed by tightening local table-column spacing. Hyperref also reports an invalid intermediate page-height value before the class establishes the final A4 page; the emitted PDF is A4.

## Remaining submission blockers

- `SUBMISSION ID` is still a deliberate anonymous placeholder.
- The completed independent human receipt covers the previous five-page snapshot; a new human pass is required only when this revised six-page snapshot is later prepared for submission.
- Authors must confirm metadata and the exact AI-use disclosure.
- An authorized SRMv2 account holder must register the abstract and record the submission ID.
- The public-repository anonymity risk must be resolved before public release or submission.

