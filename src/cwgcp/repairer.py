"""Public CW-GCP repair entrypoint and reproducibility certificate."""

import hashlib
import json
import platform
import time
from dataclasses import asdict
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import scipy
import shapely

from src.cwgcp.assignment import resolve_relations
from src.cwgcp.solver import solve_projection
from src.cwgcp.types import (
    CWGCPConfig,
    LayoutObject,
    RelationProposal,
    RepairResult,
)


def _stable_hash(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _input_record(
    objects: Sequence[LayoutObject], relations: Sequence[RelationProposal]
) -> dict:
    return {
        "objects": [
            {
                "index": obj.index,
                "class_id": obj.class_id,
                "class_name": obj.class_name,
                "center_xz": obj.center_xz.tolist(),
                "half_size_xz": obj.half_size_xz.tolist(),
                "yaw": obj.yaw,
            }
            for obj in objects
        ],
        "relations": [asdict(relation) for relation in relations],
    }


def repair_layout_cwgcp(
    objects: Sequence[LayoutObject],
    relations: Sequence[RelationProposal],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None,
    config: Optional[CWGCPConfig] = None,
    external_safety_fn: Optional[Callable[[np.ndarray], Dict[str, float]]] = None,
    warm_start_centers: Optional[Sequence[np.ndarray]] = None,
    anchor_centers: Optional[np.ndarray] = None,
    external_safety_metadata: Optional[Mapping[str, Any]] = None,
    provenance: Optional[Mapping[str, Any]] = None,
) -> RepairResult:
    """Repair one layout using confidence-weighted global projection.

    ``external_safety_fn`` is the fail-closed integration point for FCL or
    another mesh-level gate.  The certificate explicitly reports whether it
    was available; callers must not infer mesh safety from the OBB-only path.
    """

    if config is None:
        config = CWGCPConfig()
    if not objects:
        raise ValueError("objects must not be empty")
    if config.certified_feasible_projection and anchor_centers is None:
        raise ValueError(
            "certified feasible projection requires anchor_centers"
        )
    if (
        config.enable_cone_ball_close_projection
        and anchor_centers is None
    ):
        raise ValueError(
            "cone-ball close projection requires anchor_centers"
        )

    started = time.perf_counter()
    resolved, unresolved = resolve_relations(objects, relations, config)
    centers, solver_certificate = solve_projection(
        objects,
        resolved,
        room_bounds,
        config,
        external_safety_fn,
        warm_start_centers,
        relations,
        anchor_centers,
    )
    duration = time.perf_counter() - started
    layout_relation_record = _input_record(objects, relations)
    warm_start_record = [
        np.asarray(centers, dtype=np.float64).tolist()
        for centers in (
            [] if warm_start_centers is None else warm_start_centers
        )
    ]
    room_bounds_record = (
        None
        if room_bounds is None
        else [
            np.asarray(room_bounds[0], dtype=np.float64).tolist(),
            np.asarray(room_bounds[1], dtype=np.float64).tolist(),
        ]
    )
    execution_input_record = {
        "layout_and_relations": layout_relation_record,
        "room_bounds": room_bounds_record,
        "warm_start_centers": warm_start_record,
        "anchor_centers": (
            None
            if anchor_centers is None
            else np.asarray(anchor_centers, dtype=np.float64).tolist()
        ),
        "external_safety_metadata": dict(external_safety_metadata or {}),
        "provenance": dict(provenance or {}),
    }
    config_record = asdict(config)
    is_scfp = bool(config.certified_feasible_projection)
    is_fapsp = bool(
        not is_scfp
        and anchor_centers is not None
        and (
            config.coverage_first_selection
            or config.require_coverage_gain
            or config.enable_proposal_nudge
        )
    )
    certificate = {
        "algorithm": (
            "SCFP" if is_scfp else ("FA-PSP" if is_fapsp else "CW-GCP")
        ),
        "algorithm_version": (
            "0.4.0-safety-certified-feasible-projection"
            if is_scfp
            else (
                (
                    "0.3.1-fa-psp-cone-ball"
                    if (
                        config.enable_cone_ball_close_projection
                        and config.enable_proposal_nudge
                    )
                    else (
                        "0.3.1-fa-psp-no-nudge"
                        if config.enable_cone_ball_close_projection
                        else "0.3.0-fa-psp"
                    )
                )
                if is_fapsp
                else "0.2.1-cpu-pilot"
            )
        ),
        "accepted": bool(solver_certificate["accepted"]),
        "rollback_reason": solver_certificate["rollback_reason"],
        "input_hash": _stable_hash(execution_input_record),
        "layout_relation_hash": _stable_hash(layout_relation_record),
        "room_bounds_hash": _stable_hash(room_bounds_record),
        "warm_start_hashes": [
            _stable_hash(centers) for centers in warm_start_record
        ],
        "config_hash": _stable_hash(config_record),
        "config": config_record,
        "external_safety_metadata": dict(external_safety_metadata or {}),
        "provenance": dict(provenance or {}),
        "resolved_relations": [asdict(relation) for relation in resolved],
        "unresolved_relations": unresolved,
        "solver": solver_certificate,
        "runtime_seconds": float(duration),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "shapely": shapely.__version__,
        },
        "safety_scope": {
            "obb_gate": True,
            "pairwise_obb_contact_monotonicity": is_scfp,
            "rectangular_boundary_gate": room_bounds is not None,
            "external_mesh_gate": external_safety_fn is not None,
            "certified_feasible_projection": is_scfp,
        },
        "warm_start_count": (
            0 if warm_start_centers is None else len(warm_start_centers)
        ),
    }
    return RepairResult(
        centers_xz=centers,
        accepted=bool(solver_certificate["accepted"]),
        certificate=certificate,
        resolved_relations=resolved,
    )
