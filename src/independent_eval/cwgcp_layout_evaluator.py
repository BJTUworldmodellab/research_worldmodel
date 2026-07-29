"""Independent geometric evaluator for exported CW-GCP layouts.

This module deliberately does not import ``src.cwgcp``.  Its relation
classification uses center directions, proximity, and vertical extents rather
than the optimizer's margin-violation implementation.  A human-audited subset
is still required before treating it as the final paper evaluator.
"""

import math
from typing import Dict, Sequence, Tuple

import numpy as np
from shapely.geometry import Polygon

from src.relation_schema import PREDICATE_ID_TO_NAME


EVALUATOR_VERSION = "independent-layout-evaluator-v1"
EVALUATOR_CLOSE_DISTANCE = 0.75


def _center(box: dict) -> np.ndarray:
    return np.asarray(box["translation"], dtype=np.float64)


def _size(box: dict) -> np.ndarray:
    return np.asarray(box["size"], dtype=np.float64)


def _directional_relation(subject: dict, target: dict) -> str:
    delta = _center(subject)[[0, 2]] - _center(target)[[0, 2]]
    theta = math.atan2(float(delta[1]), float(delta[0]))
    if theta >= 3 * math.pi / 4 or theta < -3 * math.pi / 4:
        return "left of"
    if -3 * math.pi / 4 <= theta < -math.pi / 4:
        return "behind"
    if -math.pi / 4 <= theta < math.pi / 4:
        return "right of"
    return "in front of"


def relation_holds(
    subject: dict,
    predicate: str,
    target: dict,
    close_distance: float = EVALUATOR_CLOSE_DISTANCE,
) -> bool:
    """Evaluate one relation without using optimizer predicates."""

    predicate = " ".join(predicate.lower().replace("_", " ").split())
    subject_center = _center(subject)
    target_center = _center(target)
    if predicate == "above":
        return bool(
            subject_center[1] - _size(subject)[1]
            >= target_center[1] + _size(target)[1]
        )
    if predicate == "below":
        return bool(
            subject_center[1] + _size(subject)[1]
            <= target_center[1] - _size(target)[1]
        )

    is_close = predicate.startswith("closely ")
    base = predicate.replace("closely ", "", 1) if is_close else predicate
    if base not in {"left of", "right of", "in front of", "behind"}:
        return False
    if _directional_relation(subject, target) != base:
        return False
    if is_close:
        distance = float(
            np.linalg.norm(subject_center[[0, 2]] - target_center[[0, 2]])
        )
        return distance < close_distance
    return True


def _relation_record(relation: Sequence[int]) -> Tuple[int, str, int]:
    subject_class, predicate_id, object_class = map(int, relation)
    predicate = PREDICATE_ID_TO_NAME.get(predicate_id)
    if predicate is None:
        raise ValueError(f"unsupported predicate id: {predicate_id}")
    return subject_class, predicate, object_class


def evaluate_relations(
    boxes: Sequence[dict],
    relations: Sequence[Sequence[int]],
    close_distance: float = EVALUATOR_CLOSE_DISTANCE,
) -> Dict[str, object]:
    """Evaluate class-level relation triples using any matching instance pair."""

    satisfied = 0
    records = []
    for relation_index, raw_relation in enumerate(relations):
        subject_class, predicate, object_class = _relation_record(raw_relation)
        subjects = [
            box for box in boxes if int(box["class_id"]) == subject_class
        ]
        targets = [
            box for box in boxes if int(box["class_id"]) == object_class
        ]
        matching_pairs = []
        for subject in subjects:
            for target in targets:
                if int(subject["index"]) == int(target["index"]):
                    continue
                if relation_holds(
                    subject, predicate, target, close_distance=close_distance
                ):
                    matching_pairs.append(
                        [int(subject["index"]), int(target["index"])]
                    )
        holds = bool(matching_pairs)
        satisfied += int(holds)
        records.append(
            {
                "relation_index": relation_index,
                "subject_class_id": subject_class,
                "predicate": predicate,
                "object_class_id": object_class,
                "satisfied": holds,
                "matching_pairs": matching_pairs,
            }
        )

    total = len(relations)
    return {
        "total_relations": total,
        "satisfied_relations": satisfied,
        "relation_accuracy": float(satisfied / total) if total else 0.0,
        "relation_records": records,
    }


def _footprint(box: dict) -> Polygon:
    center = _center(box)[[0, 2]]
    half_size = _size(box)[[0, 2]]
    yaw = float(box.get("angle", 0.0))
    c = math.cos(yaw)
    s = math.sin(yaw)
    axis_x = np.array([c, s])
    axis_z = np.array([-s, c])
    corners = np.array(
        [
            center - half_size[0] * axis_x - half_size[1] * axis_z,
            center + half_size[0] * axis_x - half_size[1] * axis_z,
            center + half_size[0] * axis_x + half_size[1] * axis_z,
            center - half_size[0] * axis_x + half_size[1] * axis_z,
        ]
    )
    polygon = Polygon(corners)
    return polygon if polygon.is_valid else polygon.buffer(0)


def evaluate_geometry(boxes: Sequence[dict]) -> Dict[str, float]:
    collision_pairs = 0
    overlap_area = 0.0
    polygons = [_footprint(box) for box in boxes]
    for i in range(len(polygons)):
        for j in range(i + 1, len(polygons)):
            area = float(polygons[i].intersection(polygons[j]).area)
            if area > 1e-9:
                collision_pairs += 1
                overlap_area += area
    return {
        "obb_collision_pairs": int(collision_pairs),
        "obb_overlap_area": float(overlap_area),
    }


def evaluate_layout(
    boxes: Sequence[dict],
    relations: Sequence[Sequence[int]],
    close_distance: float = EVALUATOR_CLOSE_DISTANCE,
) -> Dict[str, object]:
    result = evaluate_relations(boxes, relations, close_distance)
    result.update(evaluate_geometry(boxes))
    return result
