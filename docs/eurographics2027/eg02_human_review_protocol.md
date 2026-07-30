# EG-02 Human Review and Annotation Protocol

Version: `eg2027-eg02-human-v1`  
Date: 2026-07-30  
Status: protocol draft, pending A/D review  

## 1. Purpose

The human review subset is used to audit whether the independent evaluator is
reasonable. It is not a replacement for the full automatic evaluation.

The goal is to estimate agreement between:

1. two independent human annotators;
2. the frozen independent evaluator from EG-05 and the human majority label.

## 2. Minimum Sample Size

The annotation set must include at least 90 target relations:

| Room | Minimum relations |
|---|---:|
| Bedroom | 30 |
| Living room | 30 |
| Dining room | 30 |

Within each room, the sample should cover the main predicates whenever present:

```text
left, right, in front of, behind, close to, far from, above, below
```

If a room does not contain enough examples for a predicate, record the shortage
in the sampling plan rather than changing the threshold after seeing results.

## 3. Sampling Rule

The sampling plan must be generated before reviewing final method outputs.

Stratification priority:

1. room type;
2. predicate type;
3. expected baseline difficulty, using only baseline metadata where available;
4. success/failure diversity from old non-final evidence anchors, if needed.

The final sample must include:

- baseline-easy cases;
- baseline-hard cases;
- cases where repair changes the evaluated pair;
- cases with missing or duplicate object categories;
- at least five known or suspected failure cases per room when available.

## 4. Annotation Material

Each row shown to annotators must include:

- scene ID;
- room type;
- object labels;
- target relation text;
- rendered/top-down image or standardized geometry view;
- subject/object highlight colors;
- anonymized method variant labels when comparing layouts.

Annotators must not see:

- whether a layout is baseline or repaired;
- optimizer scores;
- automatic evaluator result;
- paper claim text.

## 5. Annotation Questions

For each relation row, each annotator answers:

| Field | Allowed values |
|---|---|
| `human_label` | `satisfied`, `not_satisfied`, `uncertain`, `not_judgable` |
| `missing_object` | `none`, `subject`, `object`, `both`, `uncertain` |
| `visibility_quality` | `good`, `partial`, `poor` |
| `notes` | free text |

Only `satisfied` and `not_satisfied` enter Cohen's kappa directly. Rows marked
`uncertain` or `not_judgable` are reported separately and adjudicated if they
exceed 10% of the sample.

## 6. Agreement Rule

Compute Cohen's kappa between the two annotators on binary rows:

```text
satisfied vs not_satisfied
```

Threshold:

```text
kappa >= 0.70
```

If kappa is below 0.70:

1. do not run final full evaluation;
2. review ambiguous definitions;
3. revise the protocol with a new version;
4. re-annotate the affected subset or collect a replacement sample.

## 7. Evaluator-vs-Human Audit

After EG-05 implementation, compare the independent evaluator against the
human majority label.

Report:

- accuracy;
- precision/recall for `satisfied`;
- disagreement count by predicate;
- disagreement count by room;
- examples of evaluator false positives and false negatives.

This audit does not allow tuning thresholds after seeing final method results.
Any threshold change requires a version bump and re-running the full protocol.

## 8. Files

Annotation template:

```text
annotations/eurographics2027/eg02_relation_annotation_template.csv
```

Sampling plan:

```text
annotations/eurographics2027/eg02_sampling_plan.csv
```

Future completed labels should be stored as:

```text
annotations/eurographics2027/eg02_annotator_a_completed.csv
annotations/eurographics2027/eg02_annotator_b_completed.csv
annotations/eurographics2027/eg02_adjudication.csv
```

Completed annotation files may contain human reviewer initials or notes. Before
anonymous artifact release, remove personal identifiers.

