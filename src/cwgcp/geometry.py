"""Geometry utilities used by the CW-GCP optimizer and safety gate."""

from typing import Dict, Optional, Sequence, Tuple

import numpy as np
from shapely.geometry import Polygon

from src.cwgcp.types import LayoutObject


def rotated_axes(yaw: float) -> Tuple[np.ndarray, np.ndarray]:
    """Return the local X and Z axes of a Y-axis rotated rectangle."""

    c = float(np.cos(yaw))
    s = float(np.sin(yaw))
    return np.array([c, s]), np.array([-s, c])


def rectangle_corners(
    center: np.ndarray, half_size: np.ndarray, yaw: float
) -> np.ndarray:
    """Return four XZ corners in cyclic order."""

    axis_x, axis_z = rotated_axes(yaw)
    return np.array(
        [
            center - half_size[0] * axis_x - half_size[1] * axis_z,
            center + half_size[0] * axis_x - half_size[1] * axis_z,
            center + half_size[0] * axis_x + half_size[1] * axis_z,
            center - half_size[0] * axis_x + half_size[1] * axis_z,
        ],
        dtype=np.float64,
    )


def axis_aligned_extent(half_size: np.ndarray, yaw: float) -> np.ndarray:
    """Half extent of an oriented rectangle projected onto world X and Z."""

    c = abs(float(np.cos(yaw)))
    s = abs(float(np.sin(yaw)))
    return np.array(
        [
            c * half_size[0] + s * half_size[1],
            s * half_size[0] + c * half_size[1],
        ],
        dtype=np.float64,
    )


def _projection_radius(
    half_size: np.ndarray,
    object_axes: Tuple[np.ndarray, np.ndarray],
    test_axis: np.ndarray,
) -> float:
    return float(
        half_size[0] * abs(np.dot(object_axes[0], test_axis))
        + half_size[1] * abs(np.dot(object_axes[1], test_axis))
    )


def obb_penetration(
    center_a: np.ndarray,
    half_a: np.ndarray,
    yaw_a: float,
    center_b: np.ndarray,
    half_b: np.ndarray,
    yaw_b: float,
) -> float:
    """Return minimum SAT penetration depth, or zero when separated."""

    axes_a = rotated_axes(yaw_a)
    axes_b = rotated_axes(yaw_b)
    delta = np.asarray(center_b) - np.asarray(center_a)
    overlaps = []
    for axis in (*axes_a, *axes_b):
        radius_a = _projection_radius(half_a, axes_a, axis)
        radius_b = _projection_radius(half_b, axes_b, axis)
        overlap = radius_a + radius_b - abs(float(np.dot(delta, axis)))
        if overlap <= 0:
            return 0.0
        overlaps.append(overlap)
    return float(min(overlaps))


def collision_metrics(
    centers: np.ndarray, objects: Sequence[LayoutObject]
) -> Dict[str, float]:
    """Compute oriented-rectangle collision count and smooth penalty."""

    count = 0
    penalty = 0.0
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            depth = obb_penetration(
                centers[i],
                objects[i].half_size_xz,
                objects[i].yaw,
                centers[j],
                objects[j].half_size_xz,
                objects[j].yaw,
            )
            if depth > 1e-9:
                count += 1
                penalty += depth * depth
    return {"collision_pairs": int(count), "collision_penalty": float(penalty)}


def exact_overlap_metrics(
    centers: np.ndarray, objects: Sequence[LayoutObject]
) -> Dict[str, object]:
    """Return aggregate and contact-level exact OBB overlap metrics.

    Pair identifiers use stable positions in the immutable object sequence.
    Keeping the per-pair areas prevents a candidate from exchanging one
    collision for another while leaving aggregate pair count and area
    unchanged.
    """

    polygons = [
        Polygon(rectangle_corners(center, obj.half_size_xz, obj.yaw))
        for center, obj in zip(centers, objects)
    ]
    collision_pairs = 0
    overlap_area = 0.0
    pair_overlaps: Dict[str, float] = {}
    for i in range(len(polygons)):
        polygon_i = polygons[i] if polygons[i].is_valid else polygons[i].buffer(0)
        for j in range(i + 1, len(polygons)):
            polygon_j = (
                polygons[j] if polygons[j].is_valid else polygons[j].buffer(0)
            )
            area = float(polygon_i.intersection(polygon_j).area)
            if area > 1e-9:
                collision_pairs += 1
                overlap_area += area
                pair_overlaps[f"{i}:{j}"] = area
    return {
        "exact_obb_collision_pairs": int(collision_pairs),
        "exact_obb_overlap_area": float(overlap_area),
        "exact_obb_pair_overlaps": pair_overlaps,
    }


def boundary_metrics(
    centers: np.ndarray,
    objects: Sequence[LayoutObject],
    room_bounds: Optional[Tuple[np.ndarray, np.ndarray]],
) -> Dict[str, float]:
    """Evaluate OBB containment in rectangular XZ bounds.

    Real room polygons are not available in archived JSON files.  Passing
    ``None`` marks the metric unavailable instead of silently treating it as
    zero.
    """

    if room_bounds is None:
        return {
            "boundary_available": False,
            "boundary_violations": 0,
            "boundary_penalty": 0.0,
        }

    lower = np.asarray(room_bounds[0], dtype=np.float64)
    upper = np.asarray(room_bounds[1], dtype=np.float64)
    if lower.shape != (2,) or upper.shape != (2,) or np.any(lower >= upper):
        raise ValueError("room_bounds must be two ordered XZ vectors")

    violations = 0
    penalty = 0.0
    for center, obj in zip(centers, objects):
        corners = rectangle_corners(center, obj.half_size_xz, obj.yaw)
        below = np.maximum(lower - corners, 0.0)
        above = np.maximum(corners - upper, 0.0)
        excess = below + above
        if np.any(excess > 0):
            violations += 1
            penalty += float(np.sum(excess * excess))
    return {
        "boundary_available": True,
        "boundary_violations": int(violations),
        "boundary_penalty": float(penalty),
    }


def movement_metrics(
    original: np.ndarray, candidate: np.ndarray, edit_threshold: float
) -> Dict[str, object]:
    """Return per-object and aggregate XZ movement."""

    per_object = np.linalg.norm(candidate - original, axis=1)
    return {
        "movement_per_object": per_object.tolist(),
        "total_movement": float(per_object.sum()),
        "max_movement": float(per_object.max()) if len(per_object) else 0.0,
        "edited_object_count": int(np.count_nonzero(per_object > edit_threshold)),
    }
