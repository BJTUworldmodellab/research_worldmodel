"""Adapters for archived InstructScene JSON layout records."""

import copy
from typing import List, Sequence

import numpy as np

from src.cwgcp.types import LayoutObject, RelationProposal
from src.relation_schema import PREDICATE_ID_TO_NAME


def objects_from_exported_boxes(boxes: Sequence[dict]) -> List[LayoutObject]:
    objects = []
    for box in boxes:
        translation = np.asarray(box["translation"], dtype=np.float64)
        size = np.asarray(box["size"], dtype=np.float64)
        objects.append(
            LayoutObject(
                index=int(box["index"]),
                class_id=int(box["class_id"]),
                class_name=str(box.get("class_name", box["class_id"])),
                center_xz=translation[[0, 2]],
                # InstructScene's trs_to_corners multiplies the stored size by
                # +/-1, so these values are already half extents.
                half_size_xz=size[[0, 2]],
                yaw=float(box.get("angle", 0.0)),
            )
        )
    return objects


def proposals_from_exported_relations(
    relations: Sequence[Sequence[int]],
) -> List[RelationProposal]:
    proposals = []
    for index, relation in enumerate(relations):
        subject_class, predicate_id, object_class = map(int, relation)
        if predicate_id not in PREDICATE_ID_TO_NAME:
            predicate = f"unsupported_{predicate_id}"
        else:
            predicate = PREDICATE_ID_TO_NAME[predicate_id]
        proposals.append(
            RelationProposal(
                subject_class_id=subject_class,
                predicate=predicate,
                object_class_id=object_class,
                confidence=1.0,
                source_id=str(index),
            )
        )
    return proposals


def apply_centers_to_exported_boxes(
    boxes: Sequence[dict], centers_xz: np.ndarray
) -> List[dict]:
    if len(boxes) != len(centers_xz):
        raise ValueError("box and center counts differ")
    repaired = copy.deepcopy(list(boxes))
    for box, center in zip(repaired, centers_xz):
        box["translation"][0] = float(center[0])
        box["translation"][2] = float(center[1])
    return repaired
