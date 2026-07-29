"""Instance resolution with ambiguity-aware Hungarian assignment."""

from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

from src.cwgcp.constraints import (
    SUPPORTED_HORIZONTAL_RELATIONS,
    normalize_predicate,
    relation_violation,
)
from src.cwgcp.types import (
    CWGCPConfig,
    LayoutObject,
    RelationProposal,
    ResolvedRelation,
)


def _candidate_pairs(
    objects: Sequence[LayoutObject], proposal: RelationProposal
) -> List[Tuple[int, int]]:
    subjects = [
        i for i, obj in enumerate(objects)
        if obj.class_id == proposal.subject_class_id
        and (
            proposal.subject_index_hint is None
            or obj.index == proposal.subject_index_hint
        )
    ]
    targets = [
        i for i, obj in enumerate(objects)
        if obj.class_id == proposal.object_class_id
        and (
            proposal.object_index_hint is None
            or obj.index == proposal.object_index_hint
        )
    ]
    return [(i, j) for i in subjects for j in targets if i != j]


def _pair_cost(
    objects: Sequence[LayoutObject],
    pair: Tuple[int, int],
    proposal: RelationProposal,
    source_index: int,
    config: CWGCPConfig,
) -> float:
    distance = float(
        np.linalg.norm(objects[pair[0]].center_xz - objects[pair[1]].center_xz)
    )
    candidate = ResolvedRelation(
        subject_index=pair[0],
        predicate=proposal.predicate,
        object_index=pair[1],
        confidence=proposal.confidence,
        source_index=source_index,
        ambiguity_margin=0.0,
    )
    centers = np.stack([obj.center_xz for obj in objects], axis=0)
    violation = relation_violation(centers, objects, candidate, config)
    scale = max(config.far_distance, 1e-6)
    # Prefer an already semantically plausible pair.  Distance remains a
    # weak deterministic prior rather than the complete assignment rule.
    return float(violation / scale + 0.05 * distance / scale)


def resolve_relations(
    objects: Sequence[LayoutObject],
    proposals: Sequence[RelationProposal],
    config: CWGCPConfig,
) -> Tuple[List[ResolvedRelation], List[dict]]:
    """Resolve class-level proposals to instances.

    Duplicate proposals with the same class pair and predicate are assigned to
    distinct candidate pairs when possible.  This is the only case where
    one-to-one assignment is justified by the archived class-level triples;
    unrelated predicates are allowed to refer to the same object pair.
    """

    unresolved: List[dict] = []
    groups: Dict[Tuple[int, str, int], List[int]] = defaultdict(list)
    for index, proposal in enumerate(proposals):
        predicate = normalize_predicate(proposal.predicate)
        if predicate not in SUPPORTED_HORIZONTAL_RELATIONS:
            unresolved.append(
                {
                    "source_index": index,
                    "reason": "unsupported_non_xz_relation",
                    "predicate": predicate,
                }
            )
            continue
        groups[
            (proposal.subject_class_id, predicate, proposal.object_class_id)
        ].append(index)

    resolved: List[ResolvedRelation] = []
    for indices in groups.values():
        all_pairs = []
        for index in indices:
            all_pairs.extend(_candidate_pairs(objects, proposals[index]))
        unique_pairs = sorted(set(all_pairs))
        if not unique_pairs:
            for index in indices:
                unresolved.append(
                    {"source_index": index, "reason": "no_instance_pair"}
                )
            continue

        costs = np.full((len(indices), len(unique_pairs)), 1e6, dtype=np.float64)
        for row, index in enumerate(indices):
            valid = set(_candidate_pairs(objects, proposals[index]))
            for column, pair in enumerate(unique_pairs):
                if pair in valid:
                    cost = _pair_cost(
                        objects, pair, proposals[index], index, config
                    )
                    costs[row, column] = cost

        assignments: Dict[int, int] = {}
        if len(unique_pairs) >= len(indices):
            rows, columns = linear_sum_assignment(costs)
            assignments.update(zip(rows.tolist(), columns.tolist()))
        else:
            for row in range(len(indices)):
                assignments[row] = int(np.argmin(costs[row]))

        for row, index in enumerate(indices):
            column = assignments.get(row)
            if column is None or costs[row, column] >= 1e5:
                unresolved.append(
                    {"source_index": index, "reason": "assignment_failed"}
                )
                continue
            assigned_cost = float(costs[row, column])
            alternative_costs = [
                float(costs[row, other_column])
                for other_column in range(len(unique_pairs))
                if other_column != column and costs[row, other_column] < 1e5
            ]
            if not alternative_costs:
                ambiguity_margin = config.ambiguity_scale
                ambiguity_factor = 1.0
            else:
                # The Hungarian assignment can force a row away from its
                # individually cheapest pair.  Confidence must therefore be
                # based on the selected pair's cost, not the row's two best
                # unconstrained costs.
                ambiguity_margin = max(
                    0.0, min(alternative_costs) - assigned_cost
                )
                ambiguity_factor = min(
                    1.0, ambiguity_margin / config.ambiguity_scale
                )
            confidence = max(
                config.min_confidence,
                proposals[index].confidence * ambiguity_factor,
            )
            subject, target = unique_pairs[column]
            resolved.append(
                ResolvedRelation(
                    subject_index=subject,
                    predicate=normalize_predicate(proposals[index].predicate),
                    object_index=target,
                    confidence=float(confidence),
                    source_index=index,
                    ambiguity_margin=float(ambiguity_margin),
                )
            )

    resolved.sort(key=lambda relation: relation.source_index)
    unresolved.sort(key=lambda item: item["source_index"])
    return resolved, unresolved
