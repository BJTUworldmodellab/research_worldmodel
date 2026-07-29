"""Deterministic multi-start constrained solver for CW-GCP."""

import warnings
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import minimize

from src.cwgcp.constraints import (
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
    scores = np.zeros(n_objects, dtype=np.float64)
    for relation in relations:
        scores[relation.subject_index] += relation.confidence + 1e-6
        scores[relation.object_index] += relation.confidence
    ranked = sorted(range(n_objects), key=lambda index: (-scores[index], index))
    return [
        index
        for index in ranked
        if scores[index] > 0
    ][:max_edited_objects]


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
    improvement = float(baseline[relation_key]) - float(candidate[relation_key])
    if improvement < config.improvement_epsilon:
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


def solve_projection(
    objects: Sequence[LayoutObject],
    relations: Sequence[ResolvedRelation],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
    config: CWGCPConfig,
    external_safety_fn: Optional[Callable[[np.ndarray], Dict[str, float]]] = None,
    warm_start_centers: Optional[Sequence[np.ndarray]] = None,
    proposals: Optional[Sequence[RelationProposal]] = None,
) -> Tuple[np.ndarray, Dict[str, object]]:
    """Solve CW-GCP and return centers plus a detailed solver certificate."""

    original = np.stack([obj.center_xz for obj in objects], axis=0)
    baseline = _candidate_metrics(
        original,
        original,
        objects,
        relations,
        proposals,
        room_bounds,
        config,
        external_safety_fn,
    )
    n_objects = len(objects)
    n_relations = len(relations)
    if n_relations == 0 or config.total_movement_budget <= 0:
        reason = "no_resolved_relations" if n_relations == 0 else "zero_budget"
        return original.copy(), {
            "accepted": False,
            "rollback_reason": reason,
            "baseline_metrics": baseline,
            "candidate_metrics": [],
            "selected_metrics": baseline,
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
    editable_set = set(editable_indices)
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
        vector = np.concatenate(
            [
                displacement.reshape(-1),
                np.zeros(n_relations, dtype=np.float64),
            ]
        )
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
        best_vector = vector.copy()
        best_objective = float(objective(vector))

        for outer in range(config.outer_iterations):
            delta_bound = min(
                radius, config.per_object_budget, config.max_trust_radius
            )
            displacement_bounds = []
            for object_index in range(n_objects):
                bound = (
                    (-delta_bound, delta_bound)
                    if object_index in editable_set
                    else (0.0, 0.0)
                )
                displacement_bounds.extend([bound, bound])
            bounds = displacement_bounds + [
                (0.0, config.max_slack)
            ] * n_relations
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
            solver_runs.append(
                {
                    "restart": restart,
                    "outer_iteration": outer,
                    "success": bool(result.success),
                    "status": int(result.status),
                    "message": str(result.message),
                    "objective": value,
                    "trust_radius": float(radius),
                    "iterations": int(getattr(result, "nit", 0)),
                    "editable_object_indices": editable_indices,
                }
            )
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
        metrics["candidate_source"] = "solver"
        candidates.append((centers, best_vector, metrics))

    feasible = []
    candidate_records = []
    for centers, vector, metrics in candidates:
        passes, rejection_reasons = _passes_gate(baseline, metrics, config)
        record = dict(metrics)
        record["gate_passed"] = passes
        record["rejection_reasons"] = rejection_reasons
        candidate_records.append(record)
        if passes:
            feasible.append((centers, vector, metrics))

    if not feasible:
        return original.copy(), {
            "accepted": False,
            "rollback_reason": "no_candidate_passed_gate",
            "baseline_metrics": baseline,
            "candidate_metrics": candidate_records,
            "selected_metrics": baseline,
            "solver_runs": solver_runs,
        }

    selected = min(
        feasible,
        key=lambda item: (
            float(
                item[2].get(
                    "proposal_weighted_relation_violation",
                    item[2]["weighted_relation_violation"],
                )
            ),
            int(item[2]["collision_pairs"]),
            int(item[2]["boundary_violations"]),
            float(item[2]["total_movement"]),
            int(item[2]["edited_object_count"]),
        ),
    )
    selected_centers, _selected_vector, selected_metrics = selected
    return selected_centers, {
        "accepted": True,
        "rollback_reason": None,
        "baseline_metrics": baseline,
        "candidate_metrics": candidate_records,
        "selected_metrics": selected_metrics,
        "solver_runs": solver_runs,
    }
