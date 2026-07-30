#!/usr/bin/env python3
"""Build the frozen EG-02 90-relation human-review sample from main result JSONs."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


PREDICATES = {
    0: "above",
    1: "left",
    2: "in front of",
    3: "close_left",
    4: "close_behind",
    5: "below",
    6: "right",
    7: "behind",
    8: "unmapped_8",
    9: "close_front",
}

ROOM_FILES = {
    "bedroom": "results/floor_prior_remote/bedroom_sgdiffusion_vq_objfeat_epoch_01999_relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "livingroom": "results/floor_prior_remote/livingroom_sgdiffusion_vq_objfeat_epoch_01459_relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
    "diningroom": "results/floor_prior_remote/diningroom_sgdiffusion_vq_objfeat_epoch_01239_relation_aware_parsed_floor_prior_max1.8_mesh_p2_close0.75_far1.6_eval_cfg1.0_1.0.json",
}

PLAN_TO_PREDICATES = {
    "left": {"left"},
    "right": {"right"},
    "in front of": {"in front of", "front"},
    "behind": {"behind"},
    "close to": {"close_left", "close_behind", "close_front", "close to", "near"},
    "far from": {"far from"},
    "above/below": {"above", "below"},
}

OUTPUT_COLUMNS = [
    "annotation_id",
    "scene_id",
    "room_type",
    "layout_variant",
    "relation_id",
    "subject_class",
    "predicate",
    "object_class",
    "subject_index",
    "object_index",
    "image_or_view_path",
    "human_label",
    "missing_object",
    "visibility_quality",
    "annotator_id",
    "notes",
    "source_text",
    "source_json",
    "raw_predicate",
    "baseline_satisfied",
    "repair_satisfied",
    "subject_center_xyz",
    "object_center_xyz",
]


def normalized_predicate(raw: str) -> str:
    if raw.startswith("close_"):
        return "close to"
    if raw == "front":
        return "in front of"
    return raw


def box_by_class_id(scene: dict, key: str, class_id: int) -> list[dict]:
    return [box for box in scene.get(key, []) if int(box.get("class_id", -1)) == class_id]


def relation_rows(root: Path, room: str, rel_path: str) -> list[dict]:
    path = root / rel_path
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    variant = data["args"]["output_suffix"]
    for scene_idx, scene in enumerate(data.get("per_scene", [])):
        layout_rel = {tuple(item) for item in scene.get("layout_relations", [])}
        repair_rel = {tuple(item) for item in scene.get("repair_relations", [])}
        for rel_idx, rel in enumerate(scene.get("selected_relations", [])):
            subject_id, pred_id, object_id = map(int, rel)
            raw_pred = PREDICATES.get(pred_id, str(pred_id))
            subject_boxes = box_by_class_id(scene, "repair_boxes", subject_id)
            object_boxes = box_by_class_id(scene, "repair_boxes", object_id)
            subject_box = subject_boxes[0] if subject_boxes else {}
            object_box = object_boxes[0] if object_boxes else {}
            rows.append(
                {
                    "scene_id": scene.get("scene_uid", f"{room}-{scene_idx}"),
                    "room_type": room,
                    "layout_variant": "collision_gated_floor_prior",
                    "relation_id": f"{scene_idx}:{rel_idx}:{subject_id}-{pred_id}-{object_id}",
                    "subject_class": subject_box.get("class_name", str(subject_id)),
                    "predicate": normalized_predicate(raw_pred),
                    "object_class": object_box.get("class_name", str(object_id)),
                    "subject_index": subject_box.get("index", ""),
                    "object_index": object_box.get("index", ""),
                    "image_or_view_path": "",
                    "human_label": "",
                    "missing_object": "none" if subject_box and object_box else "uncertain",
                    "visibility_quality": "",
                    "annotator_id": "",
                    "notes": "",
                    "source_text": scene.get("text", ""),
                    "source_json": rel_path,
                    "raw_predicate": raw_pred,
                    "baseline_satisfied": int(tuple(rel) in layout_rel),
                    "repair_satisfied": int(tuple(rel) in repair_rel),
                    "subject_center_xyz": json.dumps(subject_box.get("translation", []), separators=(",", ":")),
                    "object_center_xyz": json.dumps(object_box.get("translation", []), separators=(",", ":")),
                }
            )
    return rows


def read_plan(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sample_rows(all_rows: list[dict], plan_rows: list[dict], seed: int) -> list[dict]:
    rng = random.Random(seed)
    all_rows = [row for row in all_rows if row["raw_predicate"] != "unmapped_8"]
    by_room_pred: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_room: dict[str, list[dict]] = defaultdict(list)
    for row in all_rows:
        by_room[row["room_type"]].append(row)
        by_room_pred[(row["room_type"], row["predicate"])].append(row)

    selected: list[dict] = []
    used_relation_ids: set[tuple[str, str]] = set()
    for plan in plan_rows:
        room = plan["room_type"].strip()
        predicate_group = plan["predicate"].strip()
        if predicate_group == "failure cases":
            candidates = [
                row
                for row in by_room[room]
                if row["baseline_satisfied"] != row["repair_satisfied"]
                and (row["scene_id"], row["relation_id"]) not in used_relation_ids
            ]
        else:
            allowed = PLAN_TO_PREDICATES.get(predicate_group, {predicate_group})
            candidates = [
                row
                for predicate in allowed
                for row in by_room_pred[(room, predicate)]
                if (row["scene_id"], row["relation_id"]) not in used_relation_ids
            ]
        candidates = sorted(candidates, key=lambda row: (row["scene_id"], row["relation_id"]))
        rng.shuffle(candidates)
        need = int(plan["planned_count"])
        if len(candidates) < need:
            raise RuntimeError(
                f"not enough candidates for {room}/{predicate_group}: "
                f"need {need}, have {len(candidates)}"
            )
        for row in candidates[:need]:
            used_relation_ids.add((row["scene_id"], row["relation_id"]))
            selected.append(row)

    room_offsets = {"bedroom": "BED", "livingroom": "LIV", "diningroom": "DIN"}
    counters: dict[str, int] = defaultdict(int)
    final_rows = []
    for row in sorted(selected, key=lambda r: (r["room_type"], r["predicate"], r["scene_id"], r["relation_id"])):
        counters[row["room_type"]] += 1
        item = dict(row)
        item["annotation_id"] = f"EG02-{room_offsets[row['room_type']]}-{counters[row['room_type']]:04d}"
        final_rows.append(item)
    return final_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--plan", default="annotations/eurographics2027/eg02_sampling_plan.csv")
    parser.add_argument("--output", default="annotations/eurographics2027/eg02_human_review_sample.csv")
    parser.add_argument("--seed", type=int, default=20260730)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    all_rows = []
    for room, rel_path in ROOM_FILES.items():
        all_rows.extend(relation_rows(root, room, rel_path))
    rows = sample_rows(all_rows, read_plan(root / args.plan), args.seed)
    write_csv(root / args.output, rows)

    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["room_type"]] += 1
    print(f"wrote {root / args.output}")
    for room in ("bedroom", "livingroom", "diningroom"):
        print(f"{room}={counts[room]}")
    print(f"total={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
