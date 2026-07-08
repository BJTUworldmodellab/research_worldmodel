# Floor-Prior Relation Repair Algorithm

## Inputs

- Generated layout boxes from InstructScene.
- Explicit target relation triples parsed from the instruction.
- Translation bounds from the training dataset.
- Object sizes and rotations.
- Hyperparameters:
  - `repair_passes = 2`
  - `close_distance = 0.75`
  - `far_distance = 1.6`
  - `max_repair_move in {1.2, 1.8}`
  - `repair_overlap_weight = 1.0`

## Core idea

For each unsatisfied target relation, generate bounded floor-plane candidates and choose the least disruptive candidate that satisfies the relation.

## Pseudocode

```text
for pass in repair_passes:
    current_relations = evaluate_relations(layout)

    for target_relation in target_relations:
        if target_relation in current_relations:
            continue

        subject, predicate, object = target_relation
        pair = nearest_subject_object_pair_on_xz(subject, object)
        offset = predicate_to_xz_offset(predicate)

        target_subject_xz = object_xz + offset
        candidate_direct = clamp_to_room_bounds(target_subject_xz)

        candidates = []
        for alpha in [0.25, 0.50, 0.75, 1.00]:
            candidate = interpolate_xz(original, candidate_direct, alpha)
            preserve_y_height(candidate)

            if not satisfies(target_relation, candidate):
                continue
            if xz_movement(candidate) > max_repair_move:
                continue

            score = xz_movement(candidate) + overlap_weight * footprint_overlap(candidate)
            candidates.append((score, candidate))

        if candidates is empty:
            skip this repair
        else:
            layout = candidate with minimum score
```

## Why this is better than direct repair

Direct repair optimizes relation satisfaction only. Floor-prior repair turns relation repair into a constrained candidate-selection problem:

- It can move `z` when needed for front/behind relations.
- It keeps the change bounded by `max_repair_move`.
- It preserves `y`, so objects stay on their original support plane.
- It avoids candidates with worse coarse overlap when another satisfying candidate exists.

## Expected paper framing

The method is not a full physical-scene optimizer. It is a lightweight verifier-repair layer that adds a scene-prior guard around explicit spatial relation correction.
