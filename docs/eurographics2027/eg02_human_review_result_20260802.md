# EG-02 Human Review Result

Date: 2026-08-02

Status: `FAILED_KAPPA_GATE`

## Input Files

Human annotation workbooks:

```text
annotations/eurographics2027/eg02_human_review_rendered_20260730_complete/eg02_human_review_sample_A.xlsx
annotations/eurographics2027/eg02_human_review_rendered_20260730_complete/eg02_human_review_sample_D.xlsx
```

Reference visualization table:

```text
annotations/eurographics2027/eg02_human_review_rendered_20260730_complete/eg02_human_review_sample_with_images.csv
```

## Executed Command

```text
python scripts/summarize_eg02_human_review.py --annotator-a annotations/eurographics2027/eg02_human_review_rendered_20260730_complete/eg02_human_review_sample_A.xlsx --annotator-d annotations/eurographics2027/eg02_human_review_rendered_20260730_complete/eg02_human_review_sample_D.xlsx --reference-csv annotations/eurographics2027/eg02_human_review_rendered_20260730_complete/eg02_human_review_sample_with_images.csv --output-dir results/eurographics2027/eg02_human_review
```

## Key Result

The current A/D human review does not pass the EG-02 agreement gate.

| Metric | Value |
|---|---:|
| Relations | 90 |
| Exact agreement across all labels | 0.6333 |
| Cohen's kappa across all labels | 0.4046 |
| Binary satisfied/not_satisfied relations | 64 |
| Binary exact agreement | 0.7344 |
| Binary Cohen's kappa | 0.3414 |
| Required kappa threshold | 0.7000 |
| A/D disagreements | 33 |

## Label Distribution

| Label | Annotator A | Annotator D |
|---|---:|---:|
| satisfied | 57 | 44 |
| not_satisfied | 20 | 23 |
| uncertain | 1 | 12 |
| not_judgable | 12 | 11 |

## Room-Level Pattern

| Room | All-label agreement | Binary agreement |
|---|---:|---:|
| bedroom | 0.5667 | 0.6667 |
| livingroom | 0.5000 | 0.6667 |
| diningroom | 0.8333 | 0.8636 |

The main disagreement pressure is in bedroom and livingroom. Diningroom is
comparatively stable.

## Interpretation

EG-02 cannot currently be used as positive evidence that the automatic spatial
relation metric is human-aligned. The result should instead be treated as a
diagnostic failure: the current top-down SVG review interface and/or annotation
rules are not clear enough for two independent annotators to reach the required
agreement.

This does not invalidate the model experiments directly, because EG-02 is an
evaluation-validity check rather than a model-training or model-output step.
However, it means the paper should not yet claim that human review validates the
automatic relation metric.

## Produced Files

```text
results/eurographics2027/eg02_human_review/summary.json
results/eurographics2027/eg02_human_review/summary.csv
results/eurographics2027/eg02_human_review/disagreements.csv
results/eurographics2027/eg02_human_review/adjudication_template.csv
results/eurographics2027/eg02_human_review/eg02_human_review_sample_A.csv
results/eurographics2027/eg02_human_review/eg02_human_review_sample_D.csv
```

## Required Next Step

Do not mark EG-02 as done.

A/D should jointly review only the 33 rows in:

```text
results/eurographics2027/eg02_human_review/adjudication_template.csv
```

For each disagreement, fill:

```text
final_label
adjudicator_id
adjudication_notes
```

If many disagreements are due to ambiguous top-down views, EG-02 should be
upgraded to multi-view or real mesh rendering before repeating the human review.
