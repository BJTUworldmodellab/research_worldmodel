# EG-02 Adjudicated Final Result

Date: 2026-08-02

Status: `ADJUDICATED_FINAL_LABELS_READY`

## Inputs

Independent v2 labels:

```text
results/eurographics2027/eg02_human_review_v2/eg02_human_review_v2_A.csv
results/eurographics2027/eg02_human_review_v2/eg02_human_review_v2_D.csv
```

Adjudication file:

```text
results/eurographics2027/eg02_human_review_v2/adjudication_template.csv
```

## Command

```text
python scripts/finalize_eg02_adjudicated_labels.py --annotator-a results/eurographics2027/eg02_human_review_v2/eg02_human_review_v2_A.csv --annotator-d results/eurographics2027/eg02_human_review_v2/eg02_human_review_v2_D.csv --adjudication results/eurographics2027/eg02_human_review_v2/adjudication_template.csv --output-dir results/eurographics2027/eg02_human_review_v2_final
```

## Final Label Set

| Metric | Value |
|---|---:|
| Total relations | 90 |
| A/D agreed labels reused | 65 |
| Adjudicated disagreement labels | 25 |
| Final satisfied | 60 |
| Final not_satisfied | 19 |
| Final not_judgable | 11 |
| Binary evaluable relations | 79 |
| Binary satisfied rate | 0.7595 |
| Final labels agreeing with coord rule | 71 / 90 |
| Final-vs-coordinate agreement | 0.7889 |

## Room Breakdown

| Room | Total | Satisfied | Not Satisfied | Not Judgable | Coord Rule Agreement |
|---|---:|---:|---:|---:|---:|
| bedroom | 30 | 19 | 9 | 2 | 0.7333 |
| diningroom | 30 | 20 | 5 | 5 | 0.7333 |
| livingroom | 30 | 21 | 5 | 4 | 0.9000 |

## Interpretation

The independent A/D kappa gate was not passed, so EG-02 should not be described
as an independent inter-annotator agreement success.

However, after targeted adjudication of the 25 disagreement rows, EG-02 now has
a complete final human label set. This final label set is suitable for:

```text
post-hoc diagnostic comparison with the automatic relation metric
appendix/table reporting as adjudicated human review
identifying cases where coordinate-rule labels and human visual judgment diverge
```

It should not be used to claim that the original independent review reached
`kappa >= 0.70`.

## Produced Files

```text
results/eurographics2027/eg02_human_review_v2_final/final_labels.csv
results/eurographics2027/eg02_human_review_v2_final/summary.csv
results/eurographics2027/eg02_human_review_v2_final/summary.json
```

