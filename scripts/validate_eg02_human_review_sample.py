#!/usr/bin/env python3
"""Validate the generated EG-02 human-review sample CSV."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


EXPECTED_ROOMS = {"bedroom": 30, "livingroom": 30, "diningroom": 30}
FORBIDDEN_RAW_PREDICATES = {"unmapped_8"}
REQUIRED_COLUMNS = {
    "annotation_id",
    "scene_id",
    "room_type",
    "layout_variant",
    "relation_id",
    "subject_class",
    "predicate",
    "object_class",
    "source_text",
    "source_json",
    "raw_predicate",
    "baseline_satisfied",
    "repair_satisfied",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", default="annotations/eurographics2027/eg02_human_review_sample.csv")
    args = parser.parse_args()

    path = Path(args.sample)
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_columns = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"{path} missing columns: {sorted(missing_columns)}")
        rows = list(reader)

    failures = []
    if len(rows) != sum(EXPECTED_ROOMS.values()):
        failures.append(f"expected 90 rows, found {len(rows)}")

    ids = [row["annotation_id"] for row in rows]
    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    if duplicate_ids:
        failures.append(f"duplicate annotation_id values: {duplicate_ids[:5]}")

    room_counts = Counter(row["room_type"] for row in rows)
    for room, expected in EXPECTED_ROOMS.items():
        if room_counts[room] != expected:
            failures.append(f"{room}: expected {expected}, found {room_counts[room]}")

    forbidden = sorted({row["raw_predicate"] for row in rows} & FORBIDDEN_RAW_PREDICATES)
    if forbidden:
        failures.append(f"forbidden raw predicates included: {forbidden}")

    empty_required = []
    for index, row in enumerate(rows, start=2):
        for column in ("scene_id", "room_type", "relation_id", "subject_class", "predicate", "object_class"):
            if not row.get(column):
                empty_required.append(f"line {index} empty {column}")
    if empty_required:
        failures.extend(empty_required[:10])

    print(f"rows={len(rows)}")
    for room in ("bedroom", "livingroom", "diningroom"):
        print(f"{room}={room_counts[room]}")

    if failures:
        print("EG-02 HUMAN SAMPLE: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    print("EG-02 HUMAN SAMPLE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
