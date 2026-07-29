"""Deterministic multi-start constrained solver for CW-GCP."""

import warnings
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import minimize

from src.cwgcp.constraints import (
    normalize_predicate,
    proposal_relation_metrics,
    relation_metrics,
    relation_violation,
)
from src.cwgcp.geometry import (
    boundary_metrics,
    collision_metrics,
    exact_overlap_metrics,
    movement_metrics,
)
from src.cwgcp.types import (
    CWGCPConfig,
    LayoutObject,
    RelationProposal,
    ResolvedRelation,
)


def _huber(value: float, delta: float) -> float:
    value = abs(float(value))
    if value <= delta:
        return 0.5 * value * value
    return delta * (value - 0.5 * delta)


def _candidate_metrics(
    original: np.ndarray,
    centers: np.ndarray,
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    proposals: Optional[Sequence[RelationProposal]],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
    config: CWGCPConfig,
    external_safety_fn: Optional[Callable[[np.ndarray], Dict[str, float]]] = None,
) -> Dict[str, object]:
    metrics: Dict[str, object] = {}
    metrics.update(relation_metrics(centers, objects, relations, config))
    if proposals is not None:
        metrics.update(
            proposal_relation_metrics(centers, objects, proposals, config)
        )
    metrics.update(collision_metrics(centers, objects))
    metrics.update(exact_overlap_metrics(centers, objects))
    metrics.update(boundary_metrics(centers, objects, room_bounds))
    metrics.update(movement_metrics(original, centers, config.edit_threshold))
    if external_safety_fn is None:
        metrics["external_safety_available"] = False
    else:
        try:
            external = external_safety_fn(centers)
            if not isinstance(external, dict) or not external:
                raise ValueError("external safety result must be a non-empty dict")
            normalized = {
                str(key): float(value) for key, value in external.items()
            }
            if not all(np.isfinite(value) for value in normalized.values()):
                raise ValueError("external safety values must be finite")
            metrics["external_safety_available"] = True
            metrics["external_safety"] = normalized
        except Exception as error:
            metrics["external_safety_available"] = False
            metrics["external_safety_error"] = str(error)
    return metrics


def _objective_factory(
    original: np.ndarray,
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
    config: CWGCPConfig,
):
    n_objects = len(objects)
    n_relations = len(relations)

    def objective(vector: np.ndarray) -> float:
        displacement = vector[: 2 * n_objects].reshape(n_objects, 2)
        slack = vector[2 * n_objects : 2 * n_objects + n_relations]
        centers = original + displacement

        relation_cost = 0.0
        slack_cost = 0.0
        for index, relation in enumerate(relations):
            violation = relation_violation(centers, objects, relation, config)
            residual = max(0.0, violation - float(slack[index]))
            relation_cost += (
                config.relation_weight
                * relation.confidence
                * _huber(residual, config.huber_delta)
            )
            # Squared confidence makes slack relatively cheaper for an
            # ambiguous relation while keeping it expensive for q≈1.
            slack_cost += (
                config.slack_weight
                * relation.confidence
                * relation.confidence
                * float(slack[index])
            )

        collision = collision_metrics(centers, objects)["collision_penalty"]
        boundary = boundary_metrics(centers, objects, room_bounds)[
            "boundary_penalty"
        ]
        movement = np.linalg.norm(displacement, axis=1)
        movement_cost = sum(
            _huber(value / config.per_object_budget, config.huber_delta)
            for value in movement
        )
        edit_cost = float(
            np.sum(
                1.0
                - np.exp(
                    -np.square(movement / max(config.edit_threshold * 10.0, 1e-6))
                )
            )
        )
        return float(
            relation_cost
            + slack_cost
            + config.collision_weight * float(collision)
            + config.boundary_weight * float(boundary)
            + config.movement_weight * movement_cost
            + config.edit_weight * edit_cost
        )

    return objective


def _constraints(n_objects: int, config: CWGCPConfig):
    def per_object(vector: np.ndarray) -> np.ndarray:
        displacement = vector[: 2 * n_objects].reshape(n_objects, 2)
        return config.per_object_budget - np.linalg.norm(displacement, axis=1)

    def total_movement(vector: np.ndarray) -> float:
        displacement = vector[: 2 * n_objects].reshape(n_objects, 2)
        return float(
            config.total_movement_budget
            - np.linalg.norm(displacement, axis=1).sum()
        )

    return [
        {"type": "ineq", "fun": per_object},
        {"type": "ineq", "fun": total_movement},
    ]


def _editable_indices(
    relations: Sequence[ResolvedRelation],
    n_objects: int,
    max_edited_objects: int,
) -> List[int]:
    """Choose a deterministic sparse edit set from relation participation.

    Subjects receive a tiny tie-break preference because moving the subject is
    the convention used by the existing repairer.  Objects outside this set
    are fixed with zero-width displacement bounds, so sparsity is enforced by
    construction rather than checked only after optimization.
    """

    if max_edited_objects <= 0:
        return []
    return _relation_ranked_indices(relations, n_objects)[:max_edited_objects]


def _initial_vector(
    rng: np.random.RandomState,
    restart: int,
    n_objects: int,
    n_relations: int,
    radius: float,
    config: CWGCPConfig,
    editable_indices: Sequence[int],
) -> np.ndarray:
    displacement = np.zeros((n_objects, 2), dtype=np.float64)
    if restart > 0 and config.total_movement_budget > 0:
        directions = rng.normal(size=(len(editable_indices), 2))
        norms = np.linalg.norm(directions, axis=1, keepdims=True)
        directions = directions / np.maximum(norms, 1e-12)
        scales = rng.uniform(
            0.0, radius * 0.35, size=(len(editable_indices), 1)
        )
        for local_index, object_index in enumerate(editable_indices):
            displacement[object_index] = directions[local_index] * scales[
                local_index
            ]
        total = float(np.linalg.norm(displacement, axis=1).sum())
        if total > config.total_movement_budget:
            displacement *= config.total_movement_budget / total
    return np.concatenate(
        [displacement.reshape(-1), np.zeros(n_relations, dtype=np.float64)]
    )


def _vector_from_displacement(
    displacement: np.ndarray,
    n_relations: int,
) -> np.ndarray:
    return np.concatenate(
        [
            np.asarray(displacement, dtype=np.float64).reshape(-1),
            np.zeros(n_relations, dtype=np.float64),
        ]
    )


def _relation_ranked_indices(
    relations: Sequence[ResolvedRelation],
    n_objects: int,
    excluded: Optional[set] = None,
) -> List[int]:
    excluded = set() if excluded is None else excluded
    scores = np.zeros(n_objects, dtype=np.float64)
    for relation in relations:
        scores[relation.subject_index] += relation.confidence + 1e-6
        scores[relation.object_index] += relation.confidence
    return [
        index
        for index in sorted(range(n_objects), key=lambda index: (-scores[index], index))
        if scores[index] > 0 and index not in excluded
    ]


def _editable_indices_for_warm_start(
    warm_displacement: np.ndarray,
    relations: Sequence[ResolvedRelation],
    n_objects: int,
    config: CWGCPConfig,
) -> List[int]:
    if config.max_edited_objects <= 0:
        return []
    moved = [
        index
        for index in range(n_objects)
        if float(np.linalg.norm(warm_displacement[index])) > config.edit_threshold
    ]
    moved = sorted(
        moved,
        key=lambda index: (-float(np.linalg.norm(warm_displacement[index])), index),
    )[: config.max_edited_objects]
    if len(moved) >= config.max_edited_objects:
        return moved
    fill = _relation_ranked_indices(relations, n_objects, set(moved))
    return (moved + fill)[: config.max_edited_objects]


def _clip_displacement_to_budgets(
    displacement: np.ndarray, config: CWGCPConfig
) -> np.ndarray:
    clipped = np.asarray(displacement, dtype=np.float64).copy()
    norms = np.linalg.norm(clipped, axis=1)
    over = norms > config.per_object_budget
    if np.any(over):
        clipped[over] *= (
            config.per_object_budget / np.maximum(norms[over], 1e-12)
        )[:, None]
    total = float(np.linalg.norm(clipped, axis=1).sum())
    if total > config.total_movement_budget and total > 0.0:
        clipped *= config.total_movement_budget / total
    return clipped


def _optimize_from_vector(
    initial_vector: np.ndarray,
    initial_radius: float,
    editable_indices: Sequence[int],
    objective,
    constraints,
    original: np.ndarray,
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    proposals: Optional[Sequence[RelationProposal]],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
    config: CWGCPConfig,
    external_safety_fn: Optional[Callable[[np.ndarray], Dict[str, float]]],
    source: str,
    trust_around_current: bool,
    restart: Optional[int] = None,
    warm_start_index: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object], List[dict]]:
    n_objects = len(objects)
    n_relations = len(relations)
    editable_set = set(editable_indices)
    vector = np.asarray(initial_vector, dtype=np.float64).copy()
    best_vector = vector.copy()
    best_objective = float(objective(vector))
    radius = float(initial_radius)
    solver_runs: List[dict] = []

    for outer in range(config.outer_iterations):
        delta_bound = min(radius, config.per_object_budget, config.max_trust_radius)
        current_displacement = vector[: 2 * n_objects].reshape(n_objects, 2)
        displacement_bounds = []
        for object_index in range(n_objects):
            for axis in range(2):
                if object_index not in editable_set:
                    fixed = float(current_displacement[object_index, axis])
                    displacement_bounds.append((fixed, fixed))
                elif trust_around_current:
                    center = float(current_displacement[object_index, axis])
                    displacement_bounds.append(
                        (
                            max(-config.per_object_budget, center - delta_bound),
                            min(config.per_object_budget, center + delta_bound),
                        )
                    )
                else:
                    displacement_bounds.append((-delta_bound, delta_bound))
        bounds = displacement_bounds + [(0.0, config.max_slack)] * n_relations
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Values in x were outside bounds during a minimize step",
                category=RuntimeWarning,
            )
            result = minimize(
                objective,
                vector,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={
                    "maxiter": config.solver_max_iterations,
                    "ftol": 1e-8,
                    "disp": False,
                },
            )
        value = float(objective(result.x))
        improved = np.isfinite(value) and value < best_objective - 1e-10
        run: dict = {
            "source": source,
            "outer_iteration": outer,
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "objective": value,
            "trust_radius": float(radius),
            "iterations": int(getattr(result, "nit", 0)),
            "editable_object_indices": list(editable_indices),
        }
        if restart is not None:
            run["restart"] = restart
        if warm_start_index is not None:
            run["warm_start_index"] = warm_start_index
        solver_runs.append(run)
        if improved:
            best_vector = result.x.copy()
            best_objective = value
            vector = result.x.copy()
            radius = min(radius * 1.25, config.max_trust_radius)
        else:
            radius *= 0.5
            vector = best_vector.copy()
        if radius < config.min_trust_radius:
            break

    displacement = best_vector[: 2 * n_objects].reshape(n_objects, 2)
    centers = original + displacement
    metrics = _candidate_metrics(
        original,
        centers,
        objects,
        relations,
        proposals,
        room_bounds,
        config,
        external_safety_fn,
    )
    metrics["objective"] = best_objective
    metrics["slack"] = best_vector[2 * n_objects :].tolist()
    metrics["candidate_source"] = source
    return centers, best_vector, metrics, solver_runs


def _external_safety_not_worse(
    baseline: Dict[str, object], candidate: Dict[str, object]
) -> bool:
    if not baseline.get("external_safety_available"):
        return False
    if not candidate.get("external_safety_available"):
        return False
    baseline_external = baseline.get("external_safety", {})
    candidate_external = candidate.get("external_safety", {})
    if not baseline_external or set(candidate_external) != set(baseline_external):
        return False
    for key, baseline_value in baseline_external.items():
        candidate_value = candidate_external[key]
        if not np.isfinite(float(baseline_value)) or not np.isfinite(
            float(candidate_value)
        ):
            return False
        if float(candidate_value) > float(baseline_value) + 1e-9:
            return False
    return True


def _passes_gate(
    baseline: Dict[str, object],
    candidate: Dict[str, object],
    config: CWGCPConfig,
) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    relation_key = (
        "proposal_weighted_relation_violation"
        if "proposal_weighted_relation_violation" in baseline
        else "weighted_relation_violation"
    )
    violation_key = (
        "proposal_relation_violations"
        if "proposal_relation_violations" in baseline
        else "relation_violations"
    )
    coverage_key = (
        "proposal_satisfied_relations"
        if "proposal_satisfied_relations" in baseline
        else None
    )
    improvement = float(baseline[relation_key]) - float(candidate[relation_key])
    coverage_improved = False
    if config.coverage_first_selection and coverage_key is not None:
        baseline_coverage = int(baseline[coverage_key])
        candidate_coverage = int(candidate[coverage_key])
        coverage_improved = candidate_coverage > baseline_coverage
        if candidate_coverage < baseline_coverage:
            reasons.append("proposal_coverage_drop")
        if config.require_coverage_gain and not coverage_improved:
            reasons.append("proposal_coverage_gain_required")
    if improvement < config.improvement_epsilon and not (
        config.coverage_first_selection and coverage_improved
    ):
        reasons.append("no_relation_improvement")
    for baseline_violation, candidate_violation in zip(
        baseline[violation_key], candidate[violation_key]
    ):
        if (
            float(baseline_violation) <= config.improvement_epsilon
            and float(candidate_violation)
            > config.relation_preservation_tolerance
        ):
            reasons.append("previously_satisfied_relation_broken")
            break
    # OBB and external mesh gates are conjunctive.  An external callback can
    # strengthen safety evidence but can never disable local geometry checks.
    if int(candidate["exact_obb_collision_pairs"]) > int(
        baseline["exact_obb_collision_pairs"]
    ):
        reasons.append("exact_obb_collision_pair_increase")
    if float(candidate["exact_obb_overlap_area"]) > (
        float(baseline["exact_obb_overlap_area"]) + config.collision_tolerance
    ):
        reasons.append("exact_obb_overlap_area_increase")
    if (
        baseline["boundary_available"]
        and float(candidate["boundary_penalty"])
        > float(baseline["boundary_penalty"]) + config.boundary_tolerance
    ):
        reasons.append("boundary_penalty_increase")
    if (
        baseline["boundary_available"]
        and int(candidate["boundary_violations"])
        > int(baseline["boundary_violations"])
    ):
        reasons.append("boundary_violation_count_increase")
    if float(candidate["max_movement"]) > config.per_object_budget + 1e-6:
        reasons.append("per_object_budget_exceeded")
    if (
        float(candidate["total_movement"])
        > config.total_movement_budget + 1e-6
    ):
        reasons.append("total_movement_budget_exceeded")
    if int(candidate["edited_object_count"]) > config.max_edited_objects:
        reasons.append("edited_object_budget_exceeded")
    external_safety_expected = (
        "external_safety" in baseline
        or "external_safety_error" in baseline
    )
    if external_safety_expected:
        if not baseline.get("external_safety_available") or not candidate.get(
            "external_safety_available"
        ):
            reasons.append("external_safety_unavailable")
        elif not _external_safety_not_worse(baseline, candidate):
            reasons.append("external_safety_increase")
    return not reasons, reasons


def _external_safety_score(metrics: Dict[str, object]) -> float:
    if not metrics.get("external_safety_available"):
        return 0.0
    external = metrics.get("external_safety", {})
    if not isinstance(external, dict):
        return float("inf")
    return float(sum(float(value) for value in external.values()))


def _selection_key(metrics: Dict[str, object], config: CWGCPConfig) -> tuple:
    if (
        config.coverage_first_selection
        and "proposal_satisfied_relations" in metrics
    ):
        return (
            -int(metrics["proposal_satisfied_relations"]),
            float(metrics["proposal_weighted_relation_violation"]),
            int(metrics["exact_obb_collision_pairs"]),
            float(metrics["exact_obb_overlap_area"]),
            int(metrics["boundary_violations"]),
            _external_safety_score(metrics),
            float(metrics["total_movement"]),
            int(metrics["edited_object_count"]),
        )
    return (
        float(
            metrics.get(
                "proposal_weighted_relation_violation",
                metrics["weighted_relation_violation"],
            )
        ),
        int(metrics["collision_pairs"]),
        int(metrics["boundary_violations"]),
        float(metrics["total_movement"]),
        int(metrics["edited_object_count"]),
    )


def _proposal_pairs(
    objects: Sequence[LayoutObject],
    proposal: RelationProposal,
) -> List[Tuple[int, int]]:
    subjects = [
        index
        for index, obj in enumerate(objects)
        if obj.class_id == proposal.subject_class_id
    ]
    targets = [
        index
        for index, obj in enumerate(objects)
        if obj.class_id == proposal.object_class_id
    ]
    return [
        (subject_index, object_index)
        for subject_index in subjects
        for object_index in targets
        if subject_index != object_index
    ]


def _nudge_pair_for_relation(
    original: np.ndarray,
    centers: np.ndarray,
    relation: ResolvedRelation,
    editable_indices: Sequence[int],
    config: CWGCPConfig,
) -> Optional[np.ndarray]:
    predicate = normalize_predicate(relation.predicate)
    close = predicate.startswith("closely ")
    base = predicate.replace("closely ", "", 1) if close else predicate
    subject = relation.subject_index
    target = relation.object_index
    editable = set(editable_indices)
    if subject not in editable and target not in editable:
        return None

    updated = np.asarray(centers, dtype=np.float64).copy()
    delta = updated[subject] - updated[target]
    margin = config.relation_margin + max(config.improvement_epsilon * 10.0, 1e-5)
    correction = np.zeros(2, dtype=np.float64)

    if base == "left of":
        required = abs(float(delta[1])) + margin
        correction[0] = -required - float(delta[0])
    elif base == "right of":
        required = abs(float(delta[1])) + margin
        correction[0] = required - float(delta[0])
    elif base == "in front of":
        required = abs(float(delta[0])) + margin
        correction[1] = required - float(delta[1])
    elif base == "behind":
        required = abs(float(delta[0])) + margin
        correction[1] = -required - float(delta[1])
    elif base in {"near", "far"}:
        vector = delta.copy()
        distance = float(np.linalg.norm(vector))
        if distance <= 1e-9:
            vector = np.array([1.0, 0.0], dtype=np.float64)
            distance = 1.0
        direction = vector / distance
        if base == "near":
            desired = max(0.0, config.close_distance - margin)
            correction = direction * (desired - distance)
        else:
            desired = config.far_distance + margin
            correction = direction * (desired - distance)
    else:
        return None

    if close and base not in {"near", "far"}:
        vector = delta + correction
        distance = float(np.linalg.norm(vector))
        if distance > config.close_distance:
            correction += vector * ((config.close_distance - margin) / distance - 1.0)

    if subject in editable and target in editable:
        updated[subject] += 0.5 * correction
        updated[target] -= 0.5 * correction
    elif subject in editable:
        updated[subject] += correction
    else:
        updated[target] -= correction

    displacement = _clip_displacement_to_budgets(updated - original, config)
    return original + displacement


def _proposal_nudge_candidates(
    original: np.ndarray,
    anchor: np.ndarray,
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    proposals: Sequence[RelationProposal],
    editable_indices: Sequence[int],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
    config: CWGCPConfig,
    external_safety_fn: Optional[Callable[[np.ndarray], Dict[str, float]]],
) -> List[Tuple[np.ndarray, np.ndarray, Dict[str, object]]]:
    candidates = []
    anchor_proposal_metrics = proposal_relation_metrics(
        anchor, objects, proposals, config
    )
    source_to_violation = dict(
        zip(
            anchor_proposal_metrics["proposal_relation_source_indices"],
            anchor_proposal_metrics["proposal_relation_violations"],
        )
    )
    for source_index, proposal in enumerate(proposals):
        if source_to_violation.get(source_index, 0.0) <= config.improvement_epsilon:
            continue
        predicate = normalize_predicate(proposal.predicate)
        pairs = _proposal_pairs(objects, proposal)
        if not pairs:
            continue
        ranked_pairs = []
        for subject_index, object_index in pairs:
            relation = ResolvedRelation(
                subject_index=subject_index,
                predicate=predicate,
                object_index=object_index,
                confidence=proposal.confidence,
                source_index=source_index,
                ambiguity_margin=0.0,
            )
            ranked_pairs.append(
                (
                    relation_violation(anchor, objects, relation, config),
                    subject_index,
                    object_index,
                    relation,
                )
            )
        for _violation, _subject, _object, relation in sorted(ranked_pairs)[:3]:
            nudged = _nudge_pair_for_relation(
                original, anchor, relation, editable_indices, config
            )
            if nudged is None:
                continue
            vector = _vector_from_displacement(nudged - original, len(relations))
            metrics = _candidate_metrics(
                original,
                nudged,
                objects,
                relations,
                proposals,
                room_bounds,
                config,
                external_safety_fn,
            )
            metrics["objective"] = 0.0
            metrics["slack"] = []
            metrics["candidate_source"] = "proposal_nudge"
            metrics["proposal_source_index"] = source_index
            metrics["proposal_pair"] = [relation.subject_index, relation.object_index]
            candidates.append((nudged, vector, metrics))
    return candidates


def solve_projection(
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
    config: CWGCPConfig,
    external_safety_fn: Optional[Callable[[np.ndarray], Dict[str, float]]] = None,
    warm_start_centers: Optional[Sequence[np.ndarray]] = None,
    proposals: Optional[Sequence[RelationProposal]] = None,
    anchor_centers: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Dict[str, object]]:
    """Solve CW-GCP and return centers plus a detailed solver certificate."""

    original = np.stack([obj.center_xz for obj in objects], axis=0)
    if anchor_centers is None:
        anchor = original
        rollback_source = "baseline_rollback"
    else:
        anchor = np.asarray(anchor_centers, dtype=np.float64)
        if anchor.shape != original.shape or not np.all(np.isfinite(anchor)):
            raise ValueError("anchor_centers must match object centers and be finite")
        rollback_source = "anchor_rollback"

    original_metrics = _candidate_metrics(
        original,
        original,
        objects,
        relations,
        proposals,
        room_bounds,
        config,
        external_safety_fn,
    )
    original_metrics["candidate_source"] = "baseline"
    anchor_metrics = _candidate_metrics(
        original,
        anchor,
        objects,
        relations,
        proposals,
        room_bounds,
        config,
        external_safety_fn,
    )
    anchor_metrics["candidate_source"] = rollback_source
    n_objects = len(objects)
    n_relations = len(relations)
    if n_relations == 0 or config.total_movement_budget <= 0:
        reason = "no_resolved_relations" if n_relations == 0 else "zero_budget"
        return anchor.copy(), {
            "accepted": False,
            "rollback_reason": reason,
            "baseline_metrics": anchor_metrics,
            "original_metrics": original_metrics,
            "anchor_metrics": anchor_metrics,
            "candidate_metrics": [],
            "selected_metrics": anchor_metrics,
            "solver_runs": [],
        }
    if (
        config.require_coverage_gain
        and int(anchor_metrics.get("proposal_total_relations", 0)) > 0
        and int(anchor_metrics["proposal_satisfied_relations"])
        >= int(anchor_metrics["proposal_total_relations"])
    ):
        return anchor.copy(), {
            "accepted": False,
            "rollback_reason": "anchor_already_full_coverage",
            "baseline_metrics": anchor_metrics,
            "original_metrics": original_metrics,
            "anchor_metrics": anchor_metrics,
            "candidate_metrics": [],
            "selected_metrics": anchor_metrics,
            "solver_runs": [],
        }

    objective = _objective_factory(
        original, objects, relations, room_bounds, config
    )
    constraints = _constraints(n_objects, config)
    rng = np.random.RandomState(config.seed)
    editable_indices = _editable_indices(
        relations, n_objects, config.max_edited_objects
    )
    candidates: List[Tuple[np.ndarray, np.ndarray, Dict[str, object]]] = []
    solver_runs: List[dict] = []

    warm_starts = (
        [] if warm_start_centers is None else list(warm_start_centers)
    )
    for warm_index, warm_centers in enumerate(warm_starts):
        warm = np.asarray(warm_centers, dtype=np.float64)
        if warm.shape != original.shape or not np.all(np.isfinite(warm)):
            solver_runs.append(
                {
                    "source": "warm_start",
                    "warm_start_index": warm_index,
                    "success": False,
                    "message": "invalid_shape_or_non_finite",
                }
            )
            continue
        displacement = warm - original
        vector = _vector_from_displacement(displacement, n_relations)
        metrics = _candidate_metrics(
            original,
            warm,
            objects,
            relations,
            proposals,
            room_bounds,
            config,
            external_safety_fn,
        )
        metrics["objective"] = float(objective(vector))
        metrics["slack"] = [0.0] * n_relations
        metrics["candidate_source"] = "warm_start"
        candidates.append((warm.copy(), vector, metrics))
        solver_runs.append(
            {
                "source": "warm_start",
                "warm_start_index": warm_index,
                "success": True,
                "objective": metrics["objective"],
            }
        )
        if config.refine_warm_starts:
            bounded_displacement = _clip_displacement_to_budgets(
                displacement, config
            )
            warm_editable_indices = _editable_indices_for_warm_start(
                bounded_displacement, relations, n_objects, config
            )
            warm_vector = _vector_from_displacement(
                bounded_displacement, n_relations
            )
            centers, refined_vector, refined_metrics, runs = _optimize_from_vector(
                warm_vector,
                min(config.initial_trust_radius, config.per_object_budget),
                warm_editable_indices,
                objective,
                constraints,
                original,
                objects,
                relations,
                proposals,
                room_bounds,
                config,
                external_safety_fn,
                "warm_refine",
                True,
                warm_start_index=warm_index,
            )
            candidates.append((centers, refined_vector, refined_metrics))
            solver_runs.extend(runs)

    if config.enable_proposal_nudge and proposals:
        nudge_candidates = _proposal_nudge_candidates(
            original,
            anchor,
            objects,
            relations,
            proposals,
            editable_indices,
            room_bounds,
            config,
            external_safety_fn,
        )
        candidates.extend(nudge_candidates)
        solver_runs.append(
            {
                "source": "proposal_nudge",
                "success": True,
                "candidate_count": len(nudge_candidates),
            }
        )

    for restart in range(config.restarts):
        radius = min(config.initial_trust_radius, config.per_object_budget)
        vector = _initial_vector(
            rng,
            restart,
            n_objects,
            n_relations,
            radius,
            config,
            editable_indices,
        )
        centers, best_vector, metrics, runs = _optimize_from_vector(
            vector,
            radius,
            editable_indices,
            objective,
            constraints,
            original,
            objects,
            relations,
            proposals,
            room_bounds,
            config,
            external_safety_fn,
            "solver",
            False,
            restart=restart,
        )
        candidates.append((centers, best_vector, metrics))
        solver_runs.extend(runs)

    feasible = []
    candidate_records = []
    for centers, vector, metrics in candidates:
        passes, rejection_reasons = _passes_gate(anchor_metrics, metrics, config)
        record = dict(metrics)
        record["gate_passed"] = passes
        record["rejection_reasons"] = rejection_reasons
        candidate_records.append(record)
        if passes:
            feasible.append((centers, vector, metrics))

    if not feasible:
        return anchor.copy(), {
            "accepted": False,
            "rollback_reason": "no_candidate_passed_gate",
            "baseline_metrics": anchor_metrics,
            "original_metrics": original_metrics,
            "anchor_metrics": anchor_metrics,
            "candidate_metrics": candidate_records,
            "selected_metrics": anchor_metrics,
            "solver_runs": solver_runs,
        }

    selected = min(feasible, key=lambda item: _selection_key(item[2], config))
    selected_centers, _selected_vector, selected_metrics = selected
    return selected_centers, {
        "accepted": True,
        "rollback_reason": None,
        "baseline_metrics": anchor_metrics,
        "original_metrics": original_metrics,
        "anchor_metrics": anchor_metrics,
        "candidate_metrics": candidate_records,
        "selected_metrics": selected_metrics,
        "solver_runs": solver_runs,
    }
