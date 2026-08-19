#!/usr/bin/env python3
"""Build EG-02 real-mesh annotation v2 with explicit coordinate diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PREDICATE_IDS = {
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


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_data_cache(root: Path, rows: list[dict[str, str]]) -> dict[str, dict]:
    cache = {}
    for row in rows:
        source = row["source_json"]
        if source not in cache:
            cache[source] = json.loads((root / source).read_text(encoding="utf-8"))
    return cache


def scene_by_id(data: dict, scene_id: str) -> dict:
    for scene in data.get("per_scene", []):
        if scene.get("scene_uid") == scene_id:
            return scene
    raise KeyError(scene_id)


def norm_predicate(raw: str) -> str:
    if raw.startswith("close_"):
        return "close to"
    if raw == "front":
        return "in front of"
    return raw


def exact_relation_present(rel: tuple[int, int, int], relations: list) -> bool:
    items = list(map(tuple, relations))
    if rel in items:
        items.remove(rel)
        return True
    return False


def class_pair_from_exact_rel(scene: dict, rel: tuple[int, int, int]) -> tuple[dict | None, dict | None]:
    subject_class, _predicate, object_class = rel
    boxes = scene.get("repair_boxes", [])
    subjects = [box for box in boxes if int(box.get("class_id", -1)) == subject_class]
    objects = [box for box in boxes if int(box.get("class_id", -1)) == object_class]
    if not subjects or not objects:
        return None, None
    best = None
    best_distance = float("inf")
    for subject in subjects:
        for obj in objects:
            dx = float(subject["translation"][0]) - float(obj["translation"][0])
            dz = float(subject["translation"][2]) - float(obj["translation"][2])
            distance = dx * dx + dz * dz
            if distance < best_distance:
                best_distance = distance
                best = (subject, obj)
    return best if best else (None, None)


def json_array(values: list[float] | None) -> str:
    if values is None:
        return ""
    return json.dumps([round(float(value), 6) for value in values], separators=(",", ":"))


def coord_rule_label(predicate: str, dx: float, dy: float, dz: float, distance_xz: float) -> str:
    # This follows the relation convention observed in the project outputs.
    if predicate == "left":
        return "satisfied" if dx < 0 else "not_satisfied"
    if predicate == "right":
        return "satisfied" if dx > 0 else "not_satisfied"
    if predicate == "in front of":
        return "satisfied" if dz > 0 else "not_satisfied"
    if predicate == "behind":
        return "satisfied" if dz < 0 else "not_satisfied"
    if predicate == "above":
        return "satisfied" if dy > 0 else "not_satisfied"
    if predicate == "below":
        return "satisfied" if dy < 0 else "not_satisfied"
    if predicate == "close to":
        return "satisfied" if distance_xz <= 0.75 else "not_satisfied"
    return "not_judgable"


def build_rows(sample_rows: list[dict[str, str]], data_root: Path) -> list[dict[str, str]]:
    cache = load_data_cache(data_root, sample_rows)
    output = []
    for row in sample_rows:
        data = cache[row["source_json"]]
        scene = scene_by_id(data, row["scene_id"])
        rel_parts = row["relation_id"].split(":", 2)[-1].split("-")
        rel = tuple(map(int, rel_parts))
        subject_box, object_box = class_pair_from_exact_rel(scene, rel)
        raw_predicate = PREDICATE_IDS.get(rel[1], str(rel[1]))
        predicate = norm_predicate(raw_predicate)

        item = dict(row)
        item["predicate"] = predicate
        item["raw_predicate"] = raw_predicate
        item["repair_relation_exact_present"] = "1" if exact_relation_present(rel, scene.get("repair_relations", [])) else "0"
        item["baseline_relation_exact_present"] = "1" if exact_relation_present(rel, scene.get("layout_relations", [])) else "0"

        if subject_box and object_box:
            subject_xyz = [float(v) for v in subject_box["translation"]]
            object_xyz = [float(v) for v in object_box["translation"]]
            dx = subject_xyz[0] - object_xyz[0]
            dy = subject_xyz[1] - object_xyz[1]
            dz = subject_xyz[2] - object_xyz[2]
            distance_xz = math.hypot(dx, dz)
            item["subject_index"] = str(subject_box.get("index", ""))
            item["object_index"] = str(object_box.get("index", ""))
            item["subject_class"] = str(subject_box.get("class_name", row.get("subject_class", "")))
            item["object_class"] = str(object_box.get("class_name", row.get("object_class", "")))
            item["subject_center_xyz"] = json_array(subject_xyz)
            item["object_center_xyz"] = json_array(object_xyz)
            item["dx_subject_minus_object"] = f"{dx:.6f}"
            item["dy_subject_minus_object"] = f"{dy:.6f}"
            item["dz_subject_minus_object"] = f"{dz:.6f}"
            item["distance_xz"] = f"{distance_xz:.6f}"
            item["coord_rule_label"] = coord_rule_label(predicate, dx, dy, dz, distance_xz)
            item["coord_rule"] = (
                "left dx<0; right dx>0; in_front_of dz>0; behind dz<0; "
                "above dy>0; below dy<0; close_to distance_xz<=0.75"
            )
            item["pair_alignment_status"] = "ok"
        else:
            item["subject_center_xyz"] = ""
            item["object_center_xyz"] = ""
            item["dx_subject_minus_object"] = ""
            item["dy_subject_minus_object"] = ""
            item["dz_subject_minus_object"] = ""
            item["distance_xz"] = ""
            item["coord_rule_label"] = "not_judgable"
            item["coord_rule"] = "missing subject/object class in repair boxes"
            item["pair_alignment_status"] = "missing_pair"
        item["human_label"] = ""
        item["visibility_quality"] = ""
        item["annotator_id"] = ""
        item["notes"] = ""
        output.append(item)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--data-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = build_rows(read_rows(Path(args.sample)), Path(args.data_root))
    columns = list(rows[0].keys())
    priority = [
        "annotation_id",
        "image_or_view_path",
        "scene_id",
        "room_type",
        "subject_class",
        "predicate",
        "object_class",
        "subject_index",
        "object_index",
        "subject_center_xyz",
        "object_center_xyz",
        "dx_subject_minus_object",
        "dy_subject_minus_object",
        "dz_subject_minus_object",
        "distance_xz",
        "coord_rule_label",
        "repair_relation_exact_present",
        "baseline_relation_exact_present",
        "pair_alignment_status",
        "human_label",
        "missing_object",
        "visibility_quality",
        "annotator_id",
        "notes",
        "source_text",
        "coord_rule",
    ]
    ordered = priority + [column for column in columns if column not in priority]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    ok_count = sum(row["pair_alignment_status"] == "ok" for row in rows)
    mismatch = sum(row["coord_rule_label"] != ("satisfied" if row["repair_relation_exact_present"] == "1" else "not_satisfied") for row in rows if row["coord_rule_label"] in {"satisfied", "not_satisfied"})
    print(f"rows={len(rows)}")
    print(f"pair_alignment_ok={ok_count}")
    print(f"coord_vs_repair_exact_mismatch={mismatch}")
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
