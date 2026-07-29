"""Typed public data structures for CW-GCP."""

import math
from numbers import Integral
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass(frozen=True)
class LayoutObject:
    """One immutable object description on the XZ floor plane."""

    index: int
    class_id: int
    class_name: str
    center_xz: np.ndarray
    half_size_xz: np.ndarray
    yaw: float = 0.0

    def __post_init__(self) -> None:
        center = np.asarray(self.center_xz, dtype=np.float64)
        half_size = np.asarray(self.half_size_xz, dtype=np.float64)
        if center.shape != (2,) or half_size.shape != (2,):
            raise ValueError("center_xz and half_size_xz must both have shape (2,)")
        if not np.all(np.isfinite(center)) or not np.all(np.isfinite(half_size)):
            raise ValueError("object geometry must be finite")
        if np.any(half_size <= 0):
            raise ValueError("half_size_xz must be positive")
        object.__setattr__(self, "center_xz", center)
        object.__setattr__(self, "half_size_xz", half_size)


@dataclass(frozen=True)
class RelationProposal:
    """A class-level or instance-hinted spatial relation proposal."""

    subject_class_id: int
    predicate: str
    object_class_id: int
    confidence: float = 1.0
    subject_index_hint: Optional[int] = None
    object_index_hint: Optional[int] = None
    source_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class ResolvedRelation:
    """An instance-level relation used by the optimizer."""

    subject_index: int
    predicate: str
    object_index: int
    confidence: float
    source_index: int
    ambiguity_margin: float


@dataclass(frozen=True)
class CWGCPConfig:
    """Frozen optimization and safety settings.

    Defaults are conservative CPU-pilot values.  ``total_movement_budget`` may
    be overridden per scene to match another method's realized movement.
    """

    close_distance: float = 0.75
    far_distance: float = 1.6
    relation_margin: float = 0.0
    per_object_budget: float = 1.8
    total_movement_budget: float = 3.6
    max_edited_objects: int = 3
    ambiguity_scale: float = 0.5
    min_confidence: float = 0.05
    max_slack: float = 1.0
    relation_weight: float = 10.0
    slack_weight: float = 4.0
    collision_weight: float = 20.0
    boundary_weight: float = 20.0
    movement_weight: float = 1.0
    edit_weight: float = 0.1
    edit_threshold: float = 1e-3
    huber_delta: float = 0.25
    restarts: int = 4
    outer_iterations: int = 3
    solver_max_iterations: int = 120
    initial_trust_radius: float = 0.45
    max_trust_radius: float = 1.8
    min_trust_radius: float = 0.03
    improvement_epsilon: float = 1e-6
    relation_preservation_tolerance: float = 1e-6
    collision_tolerance: float = 1e-7
    boundary_tolerance: float = 1e-7
    seed: int = 0

    def __post_init__(self) -> None:
        continuous = {
            "close_distance": self.close_distance,
            "far_distance": self.far_distance,
            "relation_margin": self.relation_margin,
            "per_object_budget": self.per_object_budget,
            "total_movement_budget": self.total_movement_budget,
            "ambiguity_scale": self.ambiguity_scale,
            "min_confidence": self.min_confidence,
            "max_slack": self.max_slack,
            "relation_weight": self.relation_weight,
            "slack_weight": self.slack_weight,
            "collision_weight": self.collision_weight,
            "boundary_weight": self.boundary_weight,
            "movement_weight": self.movement_weight,
            "edit_weight": self.edit_weight,
            "edit_threshold": self.edit_threshold,
            "huber_delta": self.huber_delta,
            "initial_trust_radius": self.initial_trust_radius,
            "max_trust_radius": self.max_trust_radius,
            "min_trust_radius": self.min_trust_radius,
            "improvement_epsilon": self.improvement_epsilon,
            "relation_preservation_tolerance": (
                self.relation_preservation_tolerance
            ),
            "collision_tolerance": self.collision_tolerance,
            "boundary_tolerance": self.boundary_tolerance,
        }
        for name, value in continuous.items():
            if not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")

        strictly_positive = (
            "close_distance",
            "far_distance",
            "per_object_budget",
            "ambiguity_scale",
            "edit_threshold",
            "huber_delta",
            "initial_trust_radius",
            "max_trust_radius",
            "min_trust_radius",
        )
        for name in strictly_positive:
            if continuous[name] <= 0:
                raise ValueError(f"{name} must be positive")
        non_negative = (
            "relation_margin",
            "total_movement_budget",
            "max_slack",
            "relation_weight",
            "slack_weight",
            "collision_weight",
            "boundary_weight",
            "movement_weight",
            "edit_weight",
            "improvement_epsilon",
            "relation_preservation_tolerance",
            "collision_tolerance",
            "boundary_tolerance",
        )
        for name in non_negative:
            if continuous[name] < 0:
                raise ValueError(f"{name} must be non-negative")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")

        integer_fields = {
            "max_edited_objects": self.max_edited_objects,
            "restarts": self.restarts,
            "outer_iterations": self.outer_iterations,
            "solver_max_iterations": self.solver_max_iterations,
            "seed": self.seed,
        }
        for name, value in integer_fields.items():
            if not isinstance(value, Integral):
                raise ValueError(f"{name} must be an integer")
        if self.max_edited_objects < 0:
            raise ValueError("max_edited_objects must be non-negative")
        if (
            self.restarts < 1
            or self.outer_iterations < 1
            or self.solver_max_iterations < 1
        ):
            raise ValueError(
                "restarts, outer_iterations, and solver_max_iterations must be >= 1"
            )


@dataclass
class RepairResult:
    """A repaired set of centers plus a JSON-serializable certificate."""

    centers_xz: np.ndarray
    accepted: bool
    certificate: Dict[str, Any]
    resolved_relations: List[ResolvedRelation] = field(default_factory=list)
