#!/usr/bin/env python3
"""Finalize EG-02 v2 labels after adjudication."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ALLOWED = {"satisfied", "not_satisfied", "uncertain", "not_judgable"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def label_from_coord(row: dict[str, str]) -> str:
    label = (row.get("coord_rule_label") or "").strip().lower()
    return label if label in ALLOWED else "not_judgable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator-a", required=True)
    parser.add_argument("--annotator-d", required=True)
    parser.add_argument("--adjudication", required=True)
    parser.add_argument("--output-dir", default="results/eurographics2027/eg02_human_review_v2_final")
    args = parser.parse_args()

    rows_a = read_csv(Path(args.annotator_a))
    rows_d = read_csv(Path(args.annotator_d))
    adjudication_rows = read_csv(Path(args.adjudication))
    by_id_a = {row["annotation_id"]: row for row in rows_a}
    by_id_d = {row["annotation_id"]: row for row in rows_d}
    adjudicated = {}
    for row in adjudication_rows:
        label = (row.get("final_label") or "").strip().lower()
        if label not in ALLOWED:
            raise ValueError(f"invalid final_label for {row.get('annotation_id')}: {label!r}")
        adjudicated[row["annotation_id"]] = row

    if set(by_id_a) != set(by_id_d):
        raise ValueError("A/D annotation ids do not match")

    final_rows = []
    for annotation_id in sorted(by_id_a):
        row_a = by_id_a[annotation_id]
        row_d = by_id_d[annotation_id]
        label_a = row_a["human_label"].strip().lower()
        label_d = row_d["human_label"].strip().lower()
        item = dict(row_a)
        item["label_a"] = label_a
        item["label_d"] = label_d
        item["coord_rule_label"] = row_a.get("coord_rule_label", "")
        if annotation_id in adjudicated:
            adj = adjudicated[annotation_id]
            item["final_label"] = adj["final_label"].strip().lower()
            item["final_label_source"] = "adjudicated"
            item["adjudicator_id"] = adj.get("adjudicator_id", "")
            item["adjudication_notes"] = adj.get("adjudication_notes", "")
        elif label_a == label_d:
            item["final_label"] = label_a
            item["final_label_source"] = "a_d_agree"
            item["adjudicator_id"] = ""
            item["adjudication_notes"] = ""
        else:
            raise ValueError(f"missing adjudication for disagreement {annotation_id}")
        item["final_vs_coord"] = "agree" if item["final_label"] == label_from_coord(row_a) else "disagree"
        final_rows.append(item)

    label_counts = Counter(row["final_label"] for row in final_rows)
    source_counts = Counter(row["final_label_source"] for row in final_rows)
    final_vs_coord = Counter(row["final_vs_coord"] for row in final_rows)
    room_stats: dict[str, Counter] = defaultdict(Counter)
    for row in final_rows:
        room = row.get("room_type", "")
        room_stats[room]["total"] += 1
        room_stats[room][row["final_label"]] += 1
        room_stats[room]["coord_agree"] += int(row["final_vs_coord"] == "agree")

    binary = [row for row in final_rows if row["final_label"] in {"satisfied", "not_satisfied"}]
    binary_satisfied = sum(row["final_label"] == "satisfied" for row in binary)
    summary = {
        "task": "EG-02 adjudicated human review v2",
        "status": "ADJUDICATED_FINAL_LABELS_READY",
        "n_relations": len(final_rows),
        "adjudicated_disagreements": len(adjudicated),
        "label_counts": dict(label_counts),
        "final_label_sources": dict(source_counts),
        "final_vs_coord_rule": dict(final_vs_coord),
        "final_vs_coord_rule_agreement": round(final_vs_coord["agree"] / len(final_rows), 6),
        "binary_n_relations": len(binary),
        "binary_satisfied_rate": round(binary_satisfied / len(binary), 6) if binary else None,
        "room_stats": {
            room: {
                "total": counts["total"],
                "satisfied": counts["satisfied"],
                "not_satisfied": counts["not_satisfied"],
                "uncertain": counts["uncertain"],
                "not_judgable": counts["not_judgable"],
                "coord_rule_agreement": round(counts["coord_agree"] / counts["total"], 6),
            }
            for room, counts in sorted(room_stats.items())
        },
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    columns = list(final_rows[0].keys())
    write_csv(output_dir / "final_labels.csv", final_rows, columns)
    write_csv(output_dir / "summary.csv", [{"metric": k, "value": v} for k, v in summary.items() if not isinstance(v, (dict, list))], ["metric", "value"])
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"n_relations={len(final_rows)}")
    print(f"adjudicated_disagreements={len(adjudicated)}")
    print(f"label_counts={dict(label_counts)}")
    print(f"final_vs_coord_rule_agreement={summary['final_vs_coord_rule_agreement']}")
    print(f"binary_satisfied_rate={summary['binary_satisfied_rate']}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
