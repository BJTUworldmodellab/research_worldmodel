# EG-02 Independent Relation Evaluation Protocol

Version: `eg2027-eg05-v1`
Date: 2026-08-05
Track: Eurographics 2027
Status: EG-05 implementation protocol with coordinate-convention addendum
Depends on: EG-01 result identity branch

## EG-05 Coordinate Addendum

During EG-05 implementation, the original EG-02 draft text was found to
contradict the coordinate rule actually used in the adjudicated EG-02 human
review table. The adjudicated table records:

```text
left dx<0; right dx>0; in_front_of dz>0; behind dz<0;
above dy>0; below dy<0; close_to distance_xz<=0.75
```

EG-05 therefore freezes the evaluator to the human-review coordinate convention
above. This is a protocol consistency fix, not threshold tuning: thresholds
remain unchanged.

## 1. Purpose

This protocol freezes the independent relation evaluation rules before EG-05
implements the evaluator and before EG-07 reruns the main experiments.

The goal is to prevent the core paper claim from depending on the repair
optimizer's own surrogate verifier.

## 2. Non-Negotiable Independence Rule

The independent evaluator must not import or call relation-decision, candidate
scoring, acceptance, or fallback logic from the optimizer or repair modules.

Forbidden imports include, but are not limited to:

```text
scripts/compute_gated_floorprior.py
scripts/summarize_floorprior_results.py
scripts/sync_parallel_floorprior_results.py
results/relation_aware_generate_sg.py
src/ablation/repairers.py
```

The evaluator may share only data formats and generic geometry utilities that
do not encode repair acceptance decisions. If a utility is reused, it must be
listed in the evaluator audit report with an explanation of why it is not a
repair/verifier dependency.

## 3. Inputs

Each evaluated scene must provide:

| Field | Required | Description |
|---|---|---|
| `scene_id` | yes | Stable scene identifier from the validation split. |
| `room_type` | yes | One of `bedroom`, `livingroom`, `diningroom`. |
| `objects` | yes | Object instances with stable index, category label, center, size, yaw, and optional mesh id. |
| `target_relations` | yes | Parsed explicit target triples from the instruction. |
| `layout_variant` | yes | `baseline`, `floor_prior`, `collision_gated_floor_prior`, or control baseline id. |
| `source_config_id` | yes | Configuration used to generate or repair the layout. |

The evaluator reads layouts after generation/repair only. It must not inspect
optimizer candidate lists, rejected repairs, or gate-internal scores.

## 4. Coordinate Convention

The evaluator uses the same coordinate axes for every method:

| Axis | Meaning |
|---|---|
| `x` | horizontal left/right axis |
| `y` | vertical height axis |
| `z` | horizontal front/behind axis |

All directional relations are evaluated on object centers unless a relation
definition below explicitly uses oriented footprint distance.

## 5. Object Label Normalization

Before matching, labels are normalized by:

1. lowercase;
2. replacing `_`, `-`, and multiple spaces with a single space;
3. trimming whitespace;
4. applying the frozen alias table.

Initial alias table:

| Canonical | Aliases |
|---|---|
| nightstand | night stand, bedside table, bedside cabinet |
| wardrobe | closet, cabinet wardrobe |
| armchair | lounge chair, single sofa |
| sofa | couch |
| coffee table | tea table |
| dining table | dinner table |
| tv stand | television stand, tv cabinet |

Any new alias after protocol freeze requires a version bump.

## 6. Instance Matching Rule

Many instructions name object categories but not object instance IDs. The
independent evaluator therefore freezes instance matching before comparing
methods.

For each scene and target triple `(subject_class, predicate, object_class)`:

1. Find all subject instances whose normalized class matches `subject_class`.
2. Find all object instances whose normalized class matches `object_class`.
3. If either set is empty, mark the triple as `missing_subject`,
   `missing_object`, or `missing_both`.
4. If both sets are non-empty, choose the candidate pair using the baseline
   layout only:
   - first minimize center distance on the XZ plane;
   - tie-break by lower subject index;
   - then lower object index.
5. Reuse this frozen `(subject_index, object_index)` pair for all compared
   variants of the same scene.

This prevents the repaired layout from receiving a different, more favorable
object-instance match.

## 7. Relation Definitions

Let `s` be the subject object and `o` the object object. Let object centers be
`c_s=(x_s,y_s,z_s)` and `c_o=(x_o,y_o,z_o)`. Let `d_xz` be Euclidean distance
between centers in the XZ plane.

Frozen thresholds:

| Name | Value | Source |
|---|---:|---|
| `direction_margin` | `0.05 m` | EG-02 independent evaluator tolerance |
| `close_distance` | `0.75 m` | Eurographics main Floor-Prior config |
| `far_distance` | `1.60 m` | Eurographics main Floor-Prior config |
| `vertical_margin` | `0.05 m` | EG-02 independent evaluator tolerance |

Definitions:

| Predicate | Satisfied if |
|---|---|
| `left` / `left of` | `x_s < x_o - direction_margin` |
| `right` / `right of` | `x_s > x_o + direction_margin` |
| `in front of` / `front` | `z_s > z_o + direction_margin` |
| `behind` | `z_s < z_o - direction_margin` |
| `close to` / `near` / `close by` | `d_xz <= close_distance` |
| `far from` | `d_xz >= far_distance` |
| `above` | `y_s > y_o + vertical_margin` |
| `below` | `y_s < y_o - vertical_margin` |

Unsupported predicates must be reported as `unsupported_predicate`, not dropped
silently.

## 8. Conflict Handling

If the same scene contains mutually conflicting target triples for the same
frozen instance pair, the evaluator must:

1. evaluate each triple independently;
2. mark the scene with `has_conflicting_targets=true`;
3. include the conflict count in the per-scene CSV;
4. keep the triples in the denominator unless the protocol is versioned and
   frozen again before seeing final method results.

Conflicts are evidence about task difficulty, not a reason to hide failures.

## 9. Missing Object Handling

Missing object triples remain in the denominator for end-to-end relation
accuracy. The per-triple status must distinguish:

- `missing_subject`;
- `missing_object`;
- `missing_both`;
- `unsupported_predicate`;
- `evaluated`.

For diagnostic analysis, a second conditional metric may be reported on
`status=evaluated` triples only, but the primary paper metric is the
end-to-end score with missing objects included.

## 10. Output Schema

The evaluator must write:

```text
results/independent_eval/eg2027/<run_id>/per_relation.csv
results/independent_eval/eg2027/<run_id>/per_scene.csv
results/independent_eval/eg2027/<run_id>/summary.csv
results/independent_eval/eg2027/<run_id>/audit.json
```

`per_relation.csv` columns:

```text
scene_id,room_type,layout_variant,source_config_id,relation_id,
subject_class,object_class,predicate,subject_index,object_index,
status,is_satisfied,failure_reason,dx,dy,dz,d_xz
```

`per_scene.csv` columns:

```text
scene_id,room_type,layout_variant,source_config_id,
n_relations,n_evaluated,n_satisfied,n_missing,n_unsupported,
relation_accuracy,conditional_accuracy,has_conflicting_targets
```

`summary.csv` columns:

```text
layout_variant,source_config_id,room_type,n_scenes,n_relations,
relation_accuracy,conditional_accuracy,missing_rate,unsupported_rate
```

## 11. Human Review Link

The human-review protocol and annotation table live at:

```text
docs/eurographics2027/eg02_human_review_protocol.md
annotations/eurographics2027/eg02_relation_annotation_template.csv
annotations/eurographics2027/eg02_sampling_plan.csv
```

The evaluator must be compared against the frozen human subset before its
numbers are used for final claims.

## 12. Acceptance Gate

EG-02 can be marked `DONE` only when:

- [ ] this protocol is reviewed by A and D;
- [ ] the protocol commit hash is recorded;
- [ ] the sampling plan contains at least 90 relations;
- [ ] the human-review template is finalized;
- [ ] Cohen's kappa calculation rule is frozen;
- [ ] EG-05 implementation agrees to this protocol without importing repair
      decision logic.
