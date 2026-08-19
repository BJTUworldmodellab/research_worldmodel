# EG-02 Automatic-Human Alignment

Date: 2026-08-02

Status: `DIAGNOSTIC_ALIGNMENT_READY`

## Input

```text
results/eurographics2027/eg02_human_review_v2_final/final_labels.csv
```

This file contains the adjudicated final human labels from EG-02.

## Command

```text
python scripts/analyze_eg02_auto_human_alignment.py --final-labels results/eurographics2027/eg02_human_review_v2_final/final_labels.csv --output-dir results/eurographics2027/eg02_auto_human_alignment
```

## Main Result

Among 90 reviewed relations, 79 are binary-evaluable after excluding
`not_judgable` cases.

| Metric | Value |
|---|---:|
| Binary evaluable relations | 79 |
| Repair automatic vs final human accuracy | 0.8481 |
| Baseline automatic vs final human accuracy | 0.7215 |
| Coordinate-rule vs final human accuracy | 0.8228 |
| Repair automatic disagreements | 12 |
| Coordinate-rule disagreements | 14 |

The repair automatic label agrees with the adjudicated final human label on
84.8% of binary-evaluable sampled relations.

## Confusion Pattern

For repair automatic labels against final human labels:

| Quantity | Count |
|---|---:|
| True positive | 57 |
| True negative | 10 |
| False positive | 9 |
| False negative | 3 |
| Precision for satisfied | 0.8636 |
| Recall for satisfied | 0.9500 |
| Specificity for not_satisfied | 0.5263 |

The automatic repair label is strong at finding satisfied relations, but it is
too optimistic on some unsatisfied cases.

## Room Breakdown

| Room | Binary n | Repair-human accuracy |
|---|---:|---:|
| bedroom | 28 | 0.7857 |
| diningroom | 25 | 0.8800 |
| livingroom | 26 | 0.8846 |

Bedroom remains the weakest room subset.

## Predicate Breakdown

| Predicate | Binary n | Repair-human accuracy |
|---|---:|---:|
| above | 2 | 0.5000 |
| behind | 15 | 0.7333 |
| below | 8 | 1.0000 |
| close to | 12 | 0.9167 |
| in front of | 12 | 0.6667 |
| left | 14 | 0.9286 |
| right | 16 | 0.9375 |

The remaining risk is concentrated in front/behind-style relations.

## Interpretation for Paper

This result supports a cautious claim:

```text
On the adjudicated EG-02 human subset, the automatic repair relation label
matches final human judgment on 84.8% of binary-evaluable relations.
```

It should not be written as:

```text
Independent annotator agreement passed kappa >= 0.70.
```

That remains false. EG-02 is best reported as an adjudicated diagnostic human
review, not a clean independent IAA success.

## Produced Files

```text
results/eurographics2027/eg02_auto_human_alignment/summary.json
results/eurographics2027/eg02_auto_human_alignment/summary.csv
results/eurographics2027/eg02_auto_human_alignment/repair_auto_disagreements.csv
results/eurographics2027/eg02_auto_human_alignment/coord_rule_disagreements.csv
results/eurographics2027/eg02_auto_human_alignment/repair_by_room.csv
results/eurographics2027/eg02_auto_human_alignment/repair_by_predicate.csv
```

