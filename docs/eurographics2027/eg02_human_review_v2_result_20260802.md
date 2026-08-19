# EG-02 Human Review V2 Result

Date: 2026-08-02

Status: `FAILED_KAPPA_GATE`

## Inputs

```text
annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802_v2/eg02_human_review_sample_real_mesh_images_v2_A.csv
annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802_v2/eg02_human_review_sample_real_mesh_images_v2_D.csv
```

V2 changes compared with the first review:

```text
real 3D-FUTURE mesh images
explicit dx/dy/dz coordinate columns
explicit coord_rule_label
front/behind rule aligned to observed project convention
```

## Command

```text
python scripts/summarize_eg02_human_review_v2.py --annotator-a annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802_v2/eg02_human_review_sample_real_mesh_images_v2_A.csv --annotator-d annotations/eurographics2027/eg02_human_review_real_mesh_jpg_20260802_v2/eg02_human_review_sample_real_mesh_images_v2_D.csv --output-dir results/eurographics2027/eg02_human_review_v2
```

## Result

| Metric | V1 | V2 |
|---|---:|---:|
| Relations | 90 | 90 |
| All-label exact agreement | 0.6333 | 0.7222 |
| All-label Cohen's kappa | 0.4046 | 0.5068 |
| Binary relations | 64 | 78 |
| Binary exact agreement | 0.7344 | 0.6923 |
| Binary Cohen's kappa | 0.3414 | 0.3046 |
| A/D disagreements | 33 | 25 |
| Required kappa | 0.7000 | 0.7000 |

V2 improves all-label agreement and reduces disagreements, but it still does
not pass the EG-02 gate.

## Label Distribution

| Label | A | D |
|---|---:|---:|
| satisfied | 64 | 46 |
| not_satisfied | 14 | 33 |
| not_judgable | 12 | 11 |

The main remaining issue is that D marks many more relations as
`not_satisfied`, while A follows the coordinate rule more often.

## Coordinate Rule Agreement

| Annotator | Eligible Rows | Agreement with `coord_rule_label` |
|---|---:|---:|
| A | 78 | 0.8718 |
| D | 79 | 0.7468 |

This suggests that the remaining disagreement is largely annotation-rule
interpretation, not missing image data.

## Room-Level Agreement

| Room | All-label agreement | Binary agreement |
|---|---:|---:|
| bedroom | 0.7333 | 0.7407 |
| diningroom | 0.6333 | 0.5600 |
| livingroom | 0.8000 | 0.7692 |

Diningroom remains the weakest subset.

## Produced Files

```text
results/eurographics2027/eg02_human_review_v2/summary.json
results/eurographics2027/eg02_human_review_v2/summary.csv
results/eurographics2027/eg02_human_review_v2/disagreements.csv
results/eurographics2027/eg02_human_review_v2/adjudication_template.csv
results/eurographics2027/eg02_human_review_v2/eg02_human_review_v2_A.csv
results/eurographics2027/eg02_human_review_v2/eg02_human_review_v2_D.csv
```

## Required Next Step

Do not mark EG-02 as done.

A/D should adjudicate only the 25 rows in:

```text
results/eurographics2027/eg02_human_review_v2/adjudication_template.csv
```

For adjudication, use:

```text
real mesh image
coord_rule_label
pair_alignment_status
dx/dy/dz
distance_xz
```

If a row has `pair_alignment_status=ok`, the coordinate rule should be treated
as the primary spatial definition. If the visual image seems inconsistent with
the coordinate rule, record that in `adjudication_notes` rather than silently
changing the rule.

