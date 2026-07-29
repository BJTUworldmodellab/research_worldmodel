"""Relation normalization and differentiable violation functions."""

from typing import Sequence

import numpy as np

from src.cwgcp.types import (
    CWGCPConfig,
    LayoutObject,
    RelationProposal,
    ResolvedRelation,
)


SUPPORTED_HORIZONTAL_RELATIONS = {
    "left of",
    "right of",
    "in front of",
    "behind",
    "closely left of",
    "closely right of",
    "closely in front of",
    "closely behind",
    "near",
    "far",
}


def normalize_predicate(predicate: str) -> str:
    value = " ".join(predicate.lower().replace("_", " ").split())
    aliases = {
        "front of": "in front of",
        "close left": "closely left of",
        "close right": "closely right of",
        "close front": "closely in front of",
        "close behind": "closely behind",
    }
    return aliases.get(value, value)


def relation_violation(
    centers: np.ndarray,
    objects: Sequence[LayoutObject],
    relation: ResolvedRelation,
    config: CWGCPConfig,
) -> float:
    """Continuous non-negative violation for one resolved relation."""

    predicate = normalize_predicate(relation.predicate)
    s_center = centers[relation.subject_index]
    o_center = centers[relation.object_index]

    close = predicate.startswith("closely ")
    base = predicate.replace("closely ", "", 1) if close else predicate
    margin = config.relation_margin
    delta = s_center - o_center

    # Continuous hinge form of the evaluator's 45-degree direction sectors.
    # Collision separation is handled independently by the OBB penalty/gate;
    # requiring full OBB separation here made valid directional relations
    # unnecessarily expensive and could invert the independent metric.
    if base == "left of":
        signed_axis = float(-delta[0])
        orthogonal = abs(float(delta[1]))
        directional = max(0.0, orthogonal + margin - signed_axis)
    elif base == "right of":
        signed_axis = float(delta[0])
        orthogonal = abs(float(delta[1]))
        directional = max(0.0, orthogonal + margin - signed_axis)
    elif base == "in front of":
        signed_axis = float(delta[1])
        orthogonal = abs(float(delta[0]))
        directional = max(0.0, orthogonal + margin - signed_axis)
    elif base == "behind":
        signed_axis = float(-delta[1])
        orthogonal = abs(float(delta[0]))
        directional = max(0.0, orthogonal + margin - signed_axis)
    elif base in {"near", "far"}:
        directional = 0.0
    else:
        return 0.0

    distance = float(np.linalg.norm(s_center - o_center))
    if close or base == "near":
        proximity = max(0.0, distance - config.close_distance)
    elif base == "far":
        proximity = max(0.0, config.far_distance - distance)
    else:
        proximity = 0.0
    return float(directional + proximity)


def relation_metrics(
    centers: np.ndarray,
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    config: CWGCPConfig,
) -> dict:
    violations = [
        relation_violation(centers, objects, relation, config)
        for relation in relations
    ]
    weighted = [
        relation.confidence * violation
        for relation, violation in zip(relations, violations)
    ]
    return {
        "relation_violations": violations,
        "relation_violation_sum": float(sum(violations)),
        "weighted_relation_violation": float(sum(weighted)),
        "satisfied_relations": int(
            sum(violation <= config.improvement_epsilon for violation in violations)
        ),
        "total_relations": len(relations),
    }


def proposal_relation_metrics(
    centers: np.ndarray,
    objects: Sequence[LayoutObject],
    proposals: Sequence[RelationProposal],
    config: CWGCPConfig,
) -> dict:
    """Class-level existential metric for archived relation triples.

    The optimizer still uses an explicit instance assignment.  This metric is
    only the internal acceptance guard needed when the export has lost mention
    identity: a class-level relation is satisfied when at least one valid
    instance pair has zero violation.
    """

    violations = []
    confidences = []
    source_indices = []
    for source_index, proposal in enumerate(proposals):
        predicate = normalize_predicate(proposal.predicate)
        if predicate not in SUPPORTED_HORIZONTAL_RELATIONS:
            continue
        subjects = [
            index for index, obj in enumerate(objects)
            if obj.class_id == proposal.subject_class_id
        ]
        targets = [
            index for index, obj in enumerate(objects)
            if obj.class_id == proposal.object_class_id
        ]
        pair_violations = []
        for subject_index in subjects:
            for object_index in targets:
                if subject_index == object_index:
                    continue
                relation = ResolvedRelation(
                    subject_index=subject_index,
                    predicate=predicate,
                    object_index=object_index,
                    confidence=proposal.confidence,
                    source_index=source_index,
                    ambiguity_margin=0.0,
                )
                pair_violations.append(
                    relation_violation(centers, objects, relation, config)
                )
        if not pair_violations:
            continue
        violations.append(float(min(pair_violations)))
        confidences.append(float(proposal.confidence))
        source_indices.append(source_index)
    weighted = [
        confidence * violation
        for confidence, violation in zip(confidences, violations)
    ]
    return {
        "proposal_relation_violations": violations,
        "proposal_relation_source_indices": source_indices,
        "proposal_weighted_relation_violation": float(sum(weighted)),
        "proposal_satisfied_relations": int(
            sum(value <= config.improvement_epsilon for value in violations)
        ),
        "proposal_total_relations": len(violations),
    }
