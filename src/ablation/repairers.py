"""Layout repair: overlap reduction with SG consistency guard.

Works purely with bbox parameters — no mesh/retrieval/render.
"""

import copy
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.ablation.evaluators import (
    trs_to_corners,
    _get_ground_polygon,
    evaluate_overlap,
    evaluate_constraint_satisfaction,
)


# ---------------------------------------------------------------------------
# Repair algorithm
# ---------------------------------------------------------------------------

def _compute_pair_iou(
    bbox: np.ndarray, cls_dim: int, i: int, j: int
) -> Tuple[float, np.ndarray, np.ndarray]:
    """Compute ground-plane XZ IoU for a single object pair.

    Returns (iou, corners_i, corners_j).
    """
    ti = bbox[i, cls_dim : cls_dim + 3]
    ri = float(bbox[i, cls_dim + 6])
    si = bbox[i, cls_dim + 3 : cls_dim + 6]
    tj = bbox[j, cls_dim : cls_dim + 3]
    rj = float(bbox[j, cls_dim + 6])
    sj = bbox[j, cls_dim + 3 : cls_dim + 6]

    ci = trs_to_corners(ti, ri, si)
    cj = trs_to_corners(tj, rj, sj)
    pi = _get_ground_polygon(ci)
    pj = _get_ground_polygon(cj)

    if not pi.is_valid:
        pi = pi.buffer(0)
    if not pj.is_valid:
        pj = pj.buffer(0)

    inter = pi.intersection(pj).area
    union = pi.union(pj).area
    iou = inter / union if union > 0 else 0.0
    return iou, ci, cj


def _compute_push_direction(
    bbox: np.ndarray,
    cls_dim: int,
    i: int,
    j: int,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Compute unit push direction (XZ only) from center_i away from center_j."""
    ci_xz = np.array([
        bbox[i, cls_dim + 0],  # x
        bbox[i, cls_dim + 2],  # z
    ])
    cj_xz = np.array([
        bbox[j, cls_dim + 0],
        bbox[j, cls_dim + 2],
    ])
    diff = ci_xz - cj_xz
    dist = np.linalg.norm(diff)
    if dist < 1e-8:
        # Random small push if centers are identical
        angle = rng.uniform(0, 2 * np.pi)
        diff = np.array([np.cos(angle), np.sin(angle)])
    else:
        diff = diff / dist
    return diff


def _scene_overlap_iou_sum(bbox: np.ndarray, obj_masks: np.ndarray, cls_dim: int) -> float:
    """Compute total overlap IoU sum for a scene."""
    active = np.where(obj_masks == 1)[0]
    total = 0.0
    for a in range(len(active)):
        for b in range(a + 1, len(active)):
            iou, _, _ = _compute_pair_iou(bbox, cls_dim, int(active[a]), int(active[b]))
            total += iou
    return total


def _scene_sg_consistency(
    bbox: np.ndarray, objs: np.ndarray, edges: np.ndarray,
    obj_masks: np.ndarray, object_types: List[str], predicate_types: List[str],
) -> float:
    """Compute sg_layout_consistency for a scene."""
    result = evaluate_constraint_satisfaction(
        bbox, objs, edges, obj_masks, object_types, predicate_types
    )
    return result["sg_layout_consistency"]


_OVERLAP_EPSILON = 1e-6


def repair_overlap_with_sg_guard(
    bbox_params: np.ndarray,
    objs: np.ndarray,
    edges: np.ndarray,
    obj_masks: np.ndarray,
    object_types: List[str],
    predicate_types: List[str],
    max_iter: int = 50,
    step_size: float = 0.05,
    max_displacement: float = 0.25,
    seed: int = 42,
) -> Tuple[np.ndarray, Dict]:
    """Reduce overlap by pushing objects apart in XZ, guarding SG consistency.

    Guarantees:
    1. No scene with baseline overlap <= epsilon is modified (early skip).
    2. Each step's overlap_iou_sum is strictly decreasing (never increases).
    3. Final guard: if repaired overlap > baseline + epsilon, full rollback.

    Args:
        bbox_params: (12, 29) — original bbox parameters
        objs, edges, obj_masks: scene graph arrays
        object_types, predicate_types: vocabulary lists
        max_iter: maximum repair iterations
        step_size: per-iteration push distance in meters
        max_displacement: per-object cumulative displacement limit
        seed: RNG seed

    Returns:
        repaired_bbox: (12, 29) repaired bbox parameters
        log: dict with repair statistics
    """
    rng = np.random.RandomState(seed)
    cls_dim = len(object_types) + 1  # 22
    active = np.where(obj_masks == 1)[0]

    # Baseline metrics
    baseline_overlap = _scene_overlap_iou_sum(bbox_params, obj_masks, cls_dim)
    baseline_consistency = _scene_sg_consistency(
        bbox_params, objs, edges, obj_masks, object_types, predicate_types
    )

    # --- Guard 1: skip scenes with negligible overlap ---
    if baseline_overlap <= _OVERLAP_EPSILON:
        movement = np.zeros(bbox_params.shape[0])
        return bbox_params.copy(), {
            "iterations_run": 0,
            "accepted_moves": 0,
            "rejected_overlap_or_consistency": 0,
            "skipped_no_overlap": True,
            "baseline_overlap_iou_sum": float(baseline_overlap),
            "repaired_overlap_iou_sum": float(baseline_overlap),
            "baseline_sg_consistency": float(baseline_consistency),
            "repaired_sg_consistency": float(baseline_consistency),
            "movement_mean": 0.0,
            "movement_max": 0.0,
            "movement_per_object": movement.tolist(),
        }

    repaired = bbox_params.copy()
    displacement = np.zeros((bbox_params.shape[0], 2))  # (12, 2) XZ per object
    current_iou = float(baseline_overlap)

    accepted_moves = 0
    rejected_total = 0
    iterations_run = 0

    for iteration in range(max_iter):
        iterations_run = iteration + 1
        # Find all overlapping pairs, sorted by IoU (worst first)
        overlapping = []
        for a in range(len(active)):
            for b in range(a + 1, len(active)):
                i, j = int(active[a]), int(active[b])
                iou, _, _ = _compute_pair_iou(repaired, cls_dim, i, j)
                if iou > 0:
                    overlapping.append((iou, i, j))

        if not overlapping:
            break  # no more overlaps

        overlapping.sort(key=lambda x: -x[0])  # worst overlap first

        any_improvement = False
        for _iou_val, i, j in overlapping:
            direction = _compute_push_direction(repaired, cls_dim, i, j, rng)
            dx = direction[0] * step_size
            dz = direction[1] * step_size

            accepted_this_pair = False

            # Try three push variants: i only, j only, both
            for variant in ["i", "j", "both"]:
                candidate = repaired.copy()
                new_disp_i = displacement[i].copy()
                new_disp_j = displacement[j].copy()

                if variant == "i":
                    candidate[i, cls_dim + 0] += dx
                    candidate[i, cls_dim + 2] += dz
                    new_disp_i += np.array([dx, dz])
                    if np.linalg.norm(new_disp_i) > max_displacement:
                        continue
                elif variant == "j":
                    candidate[j, cls_dim + 0] -= dx
                    candidate[j, cls_dim + 2] -= dz
                    new_disp_j += np.array([-dx, -dz])
                    if np.linalg.norm(new_disp_j) > max_displacement:
                        continue
                else:  # both
                    candidate[i, cls_dim + 0] += dx
                    candidate[i, cls_dim + 2] += dz
                    candidate[j, cls_dim + 0] -= dx
                    candidate[j, cls_dim + 2] -= dz
                    new_disp_i += np.array([dx, dz])
                    new_disp_j += np.array([-dx, -dz])
                    if (np.linalg.norm(new_disp_i) > max_displacement or
                            np.linalg.norm(new_disp_j) > max_displacement):
                        continue

                new_iou = _scene_overlap_iou_sum(candidate, obj_masks, cls_dim)
                new_cons = _scene_sg_consistency(
                    candidate, objs, edges, obj_masks, object_types, predicate_types
                )

                # --- Guard 2: step must strictly reduce overlap AND not drop consistency ---
                if new_cons >= baseline_consistency and new_iou < current_iou - _OVERLAP_EPSILON:
                    repaired = candidate
                    displacement[i] = new_disp_i
                    displacement[j] = new_disp_j
                    current_iou = float(new_iou)
                    accepted_moves += 1
                    any_improvement = True
                    accepted_this_pair = True
                    break  # move on to next overlapping pair

            if not accepted_this_pair:
                rejected_total += 1

        if not any_improvement:
            break

    # --- Guard 3: scene-level rollback if overlap got worse ---
    repaired_overlap = _scene_overlap_iou_sum(repaired, obj_masks, cls_dim)

    if repaired_overlap > baseline_overlap + _OVERLAP_EPSILON:
        # Rollback to original
        repaired = bbox_params.copy()
        displacement = np.zeros_like(displacement)
        repaired_overlap = baseline_overlap
        repaired_consistency = baseline_consistency
        rollback = True
    else:
        repaired_consistency = _scene_sg_consistency(
            repaired, objs, edges, obj_masks, object_types, predicate_types
        )
        rollback = False

    movement = np.linalg.norm(displacement, axis=1)

    log = {
        "iterations_run": iterations_run,
        "accepted_moves": accepted_moves,
        "rejected_overlap_or_consistency": rejected_total,
        "skipped_no_overlap": False,
        "rollback": rollback,
        "baseline_overlap_iou_sum": float(baseline_overlap),
        "repaired_overlap_iou_sum": float(repaired_overlap),
        "baseline_sg_consistency": float(baseline_consistency),
        "repaired_sg_consistency": float(repaired_consistency),
        "movement_mean": float(movement[active].mean()),
        "movement_max": float(movement[active].max()),
        "movement_per_object": movement.tolist(),
    }

    return repaired, log
