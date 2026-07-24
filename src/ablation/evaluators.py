"""Evaluators for layout-only ablation: overlap, constraint satisfaction, bounds proxy.

All evaluators work purely with bbox parameters — no mesh/retrieval/render.
"""

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
from shapely.geometry import Polygon


# ---------------------------------------------------------------------------
# Geometry helpers (standalone, mirrors InstructScene internals)
# ---------------------------------------------------------------------------

def trs_to_corners(
    t: np.ndarray, r: float, s: np.ndarray
) -> np.ndarray:
    """Compute 8 corners of an oriented bounding box.

    Args:
        t: translation (3,) — (x, y, z) in world coords
        r: rotation angle around Y axis (radians)
        s: size (3,) — (w, h, d) extent
    Returns:
        corners: (8, 3) in the same order as trimesh
    """
    template = np.array(
        [
            [-1, -1, -1],
            [-1, -1, 1],
            [-1, 1, -1],
            [-1, 1, 1],
            [1, -1, -1],
            [1, -1, 1],
            [1, 1, -1],
            [1, 1, 1],
        ]
    )
    R = np.zeros((3, 3))
    R[0, 0] = np.cos(r)
    R[0, 2] = -np.sin(r)
    R[2, 0] = np.sin(r)
    R[2, 2] = np.cos(r)
    R[1, 1] = 1.0
    return (template * s).dot(R) + t


def _get_ground_polygon(corners: np.ndarray) -> Polygon:
    """Build a shapely Polygon from the bottom-face (XZ) corners.

    corners order: [0,1,4,5] are bottom face corners;
    then [0,1,3,2] gives convex winding order (matching compute_loc_rel).
    """
    box = corners[[0, 1, 4, 5], :][:, [0, 2]]  # (4, 2) XZ plane
    return Polygon(box[[0, 1, 3, 2], :])


# ---------------------------------------------------------------------------
# Relation computation (replicates src/data/utils_text.py:compute_loc_rel)
# ---------------------------------------------------------------------------

_REVERSE_REL = {
    "above": "below",
    "below": "above",
    "in front of": "behind",
    "behind": "in front of",
    "left of": "right of",
    "right of": "left of",
    "closely in front of": "closely behind",
    "closely behind": "closely in front of",
    "closely left of": "closely right of",
    "closely right of": "closely left of",
}

_REL_TO_ID = {
    "above": 0,
    "left of": 1,
    "in front of": 2,
    "closely left of": 3,
    "closely in front of": 4,
    "below": 5,
    "right of": 6,
    "behind": 7,
    "closely right of": 8,
    "closely behind": 9,
}


def compute_loc_rel(
    corners1: np.ndarray, corners2: np.ndarray,
    name1: str, name2: str,
) -> Optional[str]:
    """Classify spatial relation between two oriented bboxes.

    Mirrors src/data/utils_text.py:compute_loc_rel exactly.
    """
    assert corners1.shape == corners2.shape == (8, 3)

    center1 = corners1.mean(axis=0)
    center2 = corners2.mean(axis=0)

    d = center1 - center2
    theta = math.atan2(d[2], d[0])
    distance = math.sqrt(d[2] ** 2 + d[0] ** 2)

    poly1 = _get_ground_polygon(corners1)
    poly2 = _get_ground_polygon(corners2)
    from shapely.geometry import Point

    point1 = Point(center1[[0, 2]])
    point2 = Point(center2[[0, 2]])

    # Horizontal
    if theta >= 3 * math.pi / 4 or theta < -3 * math.pi / 4:
        p = "left of"
    elif -3 * math.pi / 4 <= theta < -math.pi / 4:
        p = "behind"
    elif -math.pi / 4 <= theta < math.pi / 4:
        p = "right of"
    elif math.pi / 4 <= theta < 3 * math.pi / 4:
        p = "in front of"
    else:
        p = None  # unreachable

    # Vertical override
    if point1.within(poly2) or point2.within(poly1):
        delta1 = center1[1] - center2[1]
        delta2 = (
            corners1[:, 1].max()
            - corners1[:, 1].min()
            + corners2[:, 1].max()
            - corners2[:, 1].min()
        ) / 2.0
        if (delta1 - delta2) >= 0.0 or "lamp" in name1:
            return "above"
        if (-delta1 - delta2) >= 0.0 or "lamp" in name2:
            return "below"

    if distance > 3.0:
        return None
    if distance < 1.0:
        p = "closely " + p
    return p


# ---------------------------------------------------------------------------
# Per-pair and per-scene evaluators
# ---------------------------------------------------------------------------

def _active_pairs(
    obj_masks: np.ndarray,
) -> List[Tuple[int, int]]:
    """Return all (i, j) pairs where both objects are active and i < j."""
    active = np.where(obj_masks == 1)[0]
    return [(int(active[i]), int(active[j])) for i in range(len(active))
            for j in range(i + 1, len(active))]


def evaluate_overlap(
    corners_list: List[np.ndarray],
) -> Dict[str, float]:
    """Compute ground-plane XZ overlap metrics for all object pairs.

    Args:
        corners_list: list of (8,3) corner arrays, one per active object.
    Returns:
        dict with overlap_pair_count, overlap_iou_sum, mean_pair_iou,
        total_pairs.
    """
    n = len(corners_list)
    total_pairs = n * (n - 1) // 2
    overlap_count = 0
    iou_sum = 0.0

    for i in range(n):
        poly_i = _get_ground_polygon(corners_list[i])
        for j in range(i + 1, n):
            poly_j = _get_ground_polygon(corners_list[j])
            if not poly_i.is_valid:
                poly_i = poly_i.buffer(0)
            if not poly_j.is_valid:
                poly_j = poly_j.buffer(0)
            intersection = poly_i.intersection(poly_j).area
            union = poly_i.union(poly_j).area
            if union > 0 and intersection > 0:
                iou = intersection / union
                overlap_count += 1
                iou_sum += iou

    return {
        "overlap_pair_count": overlap_count,
        "overlap_iou_sum": float(iou_sum),
        "mean_pair_iou": float(iou_sum / overlap_count) if overlap_count > 0 else 0.0,
        "total_pairs": total_pairs,
    }


def evaluate_constraint_satisfaction(
    bbox_params: np.ndarray,
    objs: np.ndarray,
    edges: np.ndarray,
    obj_masks: np.ndarray,
    object_types: List[str],
    predicate_types: List[str],
) -> Dict[str, float]:
    """Evaluate how well the generated bbox layout satisfies the generated
    scene graph edges.

    For each directed edge e_ij != empty, the generated scene graph
    "expects" predicate p at (i,j).  We compute the geometric relation from
    the actual bbox positions via compute_loc_rel and compare.

    Because no ground-truth relations are available in the export, this
    metric is named **sg_layout_consistency** (not official relation accuracy).

    Returns:
        total_constraints, satisfied_constraints,
        easy_satisfied_constraints, consistency_rate, easy_consistency_rate
    """
    n_pred = len(predicate_types)
    cls_dim = len(object_types) + 1  # 22
    active = np.where(obj_masks == 1)[0]
    name_map = {i: object_types[int(objs[i])] for i in active}

    total = 0
    satisfied = 0
    easy_satisfied = 0

    for i in active:
        for j in active:
            if i == j:
                continue
            pred_id = int(edges[i, j])
            if pred_id >= n_pred:
                continue  # empty edge

            total += 1

            # Compute geometric relation from bbox
            ti = bbox_params[i, cls_dim : cls_dim + 3]
            ri = float(bbox_params[i, cls_dim + 6])
            si = bbox_params[i, cls_dim + 3 : cls_dim + 6]
            tj = bbox_params[j, cls_dim : cls_dim + 3]
            rj = float(bbox_params[j, cls_dim + 6])
            sj = bbox_params[j, cls_dim + 3 : cls_dim + 6]

            corners_i = trs_to_corners(ti, ri, si)
            corners_j = trs_to_corners(tj, rj, sj)

            rel_str = compute_loc_rel(
                corners_i, corners_j, name_map[i], name_map[j]
            )
            if rel_str is not None and rel_str in _REL_TO_ID:
                geom_id = _REL_TO_ID[rel_str]
                if geom_id == pred_id:
                    satisfied += 1
                    easy_satisfied += 1
                else:
                    # Easy mode: ignore "closely" distinction
                    # Pred ids: 0=above,1=left_of,2=in_front_of,
                    #           3=closely_left_of,4=closely_in_front_of,
                    #           5=below,6=right_of,7=behind,
                    #           8=closely_right_of,9=closely_behind
                    easy_geom = _easy_pred_id(geom_id)
                    easy_pred = _easy_pred_id(pred_id)
                    if easy_geom == easy_pred:
                        easy_satisfied += 1

    rate = satisfied / total if total > 0 else 0.0
    easy_rate = easy_satisfied / total if total > 0 else 0.0

    return {
        "sg_total_constraints": total,
        "sg_satisfied_constraints": satisfied,
        "sg_easy_satisfied_constraints": easy_satisfied,
        "sg_layout_consistency": float(rate),
        "sg_layout_consistency_easy": float(easy_rate),
    }


def _easy_pred_id(pid: int) -> int:
    """Map a predicate id to its non-closely equivalent."""
    # 0=above, 1=left_of, 2=in_front_of, 3=closely_left_of, 4=closely_in_front_of,
    # 5=below, 6=right_of, 7=behind, 8=closely_right_of, 9=closely_behind
    mapping = {3: 1, 4: 2, 8: 6, 9: 7}
    return mapping.get(pid, pid)


def evaluate_bounds_proxy(
    bbox_params: np.ndarray,
    obj_masks: np.ndarray,
    bounds: Dict[str, np.ndarray],
    cls_dim: int,
) -> Dict[str, float]:
    """Check whether bbox translations fall within dataset scale bounds.

    This is a PROXY — it uses the dataset-wide min/max from training,
    NOT the actual room geometry. Room OOB is reported separately as NA.

    Returns:
        n_objects, n_translation_violations, translation_violation_rate
    """
    active = np.where(obj_masks == 1)[0]
    t_low = bounds["translations"][0]   # (3,)
    t_high = bounds["translations"][1]  # (3,)

    n_objects = len(active)
    n_violations = 0

    for i in active:
        t = bbox_params[i, cls_dim : cls_dim + 3]
        if np.any(t < t_low) or np.any(t > t_high):
            n_violations += 1

    return {
        "proxy_n_active_objects": n_objects,
        "proxy_n_translation_violations": n_violations,
        "proxy_translation_violation_rate": float(
            n_violations / n_objects if n_objects > 0 else 0.0
        ),
    }


def evaluate_scene(
    scene_data: Dict,
    object_types: List[str],
    predicate_types: List[str],
    bounds: Optional[Dict[str, np.ndarray]] = None,
) -> Dict[str, float]:
    """Run all evaluators on a single scene. Returns a flat metrics dict."""
    bbox = scene_data["bbox_params"]          # (12, 29)
    objs = scene_data["objs"]                  # (12,)
    edges = scene_data["edges"]                # (12, 12)
    masks = scene_data["obj_masks"]            # (12,)
    scene_idx = scene_data.get("scene_index", -1)
    text = str(scene_data.get("text", ""))

    cls_dim = len(object_types) + 1
    active = np.where(masks == 1)[0]
    n_active = int(len(active))

    # Build class names
    class_names = [
        object_types[int(objs[i])] if i in active else "<empty>"
        for i in range(len(objs))
    ]
    active_names = [object_types[int(objs[i])] for i in active]

    # --- overlap ---
    corners_list = []
    for i in active:
        t = bbox[i, cls_dim : cls_dim + 3]
        r = float(bbox[i, cls_dim + 6])
        s = bbox[i, cls_dim + 3 : cls_dim + 6]
        corners_list.append(trs_to_corners(t, r, s))
    overlap = evaluate_overlap(corners_list)

    # --- constraint satisfaction ---
    constraint = evaluate_constraint_satisfaction(
        bbox, objs, edges, masks, object_types, predicate_types
    )

    # --- bounds proxy ---
    if bounds is not None:
        proxy = evaluate_bounds_proxy(bbox, masks, bounds, cls_dim)
    else:
        proxy = {
            "proxy_n_active_objects": n_active,
            "proxy_n_translation_violations": float("nan"),
            "proxy_translation_violation_rate": float("nan"),
        }

    # --- assemble ---
    metrics = {
        "scene_index": scene_idx,
        "n_active_objects": n_active,
        "active_classes": ", ".join(active_names),
        "text": text[:200],
        "room_oob": "NA",  # no room bounds available
    }
    metrics.update(overlap)
    metrics.update(constraint)
    metrics.update(proxy)
    metrics["movement_mean_displacement"] = 0.0  # baseline only

    return metrics


def evaluate_all(
    scenes: List[Dict],
    object_types: List[str],
    predicate_types: List[str],
    bounds: Optional[Dict[str, np.ndarray]] = None,
) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
    """Run all evaluators across all scenes, return per-scene + aggregate."""
    per_scene = []
    for scene in scenes:
        m = evaluate_scene(scene, object_types, predicate_types, bounds)
        per_scene.append(m)

    # Aggregate
    agg = {}
    numeric_keys = [
        k for k in per_scene[0].keys()
        if k not in ("scene_index", "active_classes", "text", "room_oob")
        and isinstance(per_scene[0][k], (int, float))
    ]
    for k in numeric_keys:
        vals = [s[k] for s in per_scene if not math.isnan(s[k])]
        agg[f"mean_{k}"] = float(np.mean(vals)) if vals else float("nan")
        agg[f"sum_{k}"] = float(np.sum(vals)) if vals else float("nan")

    agg["n_scenes"] = len(scenes)
    agg["room_oob"] = "NA"

    return per_scene, agg
