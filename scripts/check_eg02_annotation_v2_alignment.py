#!/usr/bin/env python3
"""Write an alignment audit for EG-02 annotation v2 CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with Path(args.input).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    audit_rows = []
    for row in rows:
        repair_label = "satisfied" if row.get("repair_relation_exact_present") == "1" else "not_satisfied"
        coord_label = row.get("coord_rule_label", "")
        status = "ok"
        if row.get("pair_alignment_status") != "ok":
            status = "missing_pair"
        elif coord_label in {"satisfied", "not_satisfied"} and coord_label != repair_label:
            status = "coord_repair_disagree"
        if status != "ok":
            audit_rows.append(
                {
                    "annotation_id": row.get("annotation_id", ""),
                    "status": status,
                    "room_type": row.get("room_type", ""),
                    "predicate": row.get("predicate", ""),
                    "subject_class": row.get("subject_class", ""),
                    "object_class": row.get("object_class", ""),
                    "coord_rule_label": coord_label,
                    "repair_relation_exact_label": repair_label,
                    "dx": row.get("dx_subject_minus_object", ""),
                    "dy": row.get("dy_subject_minus_object", ""),
                    "dz": row.get("dz_subject_minus_object", ""),
                    "distance_xz": row.get("distance_xz", ""),
                    "image_or_view_path": row.get("image_or_view_path", ""),
                    "source_text": row.get("source_text", ""),
                }
            )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "annotation_id",
        "status",
        "room_type",
        "predicate",
        "subject_class",
        "object_class",
        "coord_rule_label",
        "repair_relation_exact_label",
        "dx",
        "dy",
        "dz",
        "distance_xz",
        "image_or_view_path",
        "source_text",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"rows={len(rows)}")
    print(f"audit_rows={len(audit_rows)}")
    print(f"output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
