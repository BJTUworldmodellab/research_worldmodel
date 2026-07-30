#!/usr/bin/env python3
"""Validate the EG-02 human-review sampling plan."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


REQUIRED_ROOMS = ("bedroom", "livingroom", "diningroom")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default="annotations/eurographics2027/eg02_sampling_plan.csv")
    parser.add_argument("--min-per-room", type=int, default=30)
    parser.add_argument("--min-total", type=int, default=90)
    args = parser.parse_args()

    path = Path(args.plan)
    room_counts: dict[str, int] = defaultdict(int)
    predicates: dict[str, set[str]] = defaultdict(set)

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"room_type", "predicate", "planned_count"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        for row in reader:
            room = (row.get("room_type") or "").strip()
            predicate = (row.get("predicate") or "").strip()
            try:
                count = int((row.get("planned_count") or "0").strip())
            except ValueError as exc:
                raise ValueError(f"invalid planned_count in row: {row}") from exc
            room_counts[room] += count
            if predicate:
                predicates[room].add(predicate)

    failures = []
    for room in REQUIRED_ROOMS:
        count = room_counts.get(room, 0)
        if count < args.min_per_room:
            failures.append(f"{room}: planned {count}, expected at least {args.min_per_room}")
        if len(predicates.get(room, set())) < 6:
            failures.append(f"{room}: only {len(predicates.get(room, set()))} predicate groups")

    total = sum(room_counts.values())
    if total < args.min_total:
        failures.append(f"total: planned {total}, expected at least {args.min_total}")

    for room in REQUIRED_ROOMS:
        print(f"{room}={room_counts.get(room, 0)} predicates={len(predicates.get(room, set()))}")
    print(f"total={total}")

    if failures:
        print("EG-02 SAMPLING PLAN: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    print("EG-02 SAMPLING PLAN: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
