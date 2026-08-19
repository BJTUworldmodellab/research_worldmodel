#!/usr/bin/env python3
"""Analyze automatic relation labels against EG-02 adjudicated human labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


BINARY = {"satisfied", "not_satisfied"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def auto_label(row: dict[str, str], column: str) -> str:
    return "satisfied" if str(row.get(column, "")).strip() == "1" else "not_satisfied"


def rates(rows: list[dict[str, str]], pred_col: str, label_col: str = "final_label") -> dict[str, object]:
    eligible = [row for row in rows if row.get(label_col) in BINARY]
    tp = sum(row[label_col] == "satisfied" and row[pred_col] == "satisfied" for row in eligible)
    tn = sum(row[label_col] == "not_satisfied" and row[pred_col] == "not_satisfied" for row in eligible)
    fp = sum(row[label_col] == "not_satisfied" and row[pred_col] == "satisfied" for row in eligible)
    fn = sum(row[label_col] == "satisfied" and row[pred_col] == "not_satisfied" for row in eligible)
    n = len(eligible)
    return {
        "n": n,
        "accuracy": round((tp + tn) / n, 6) if n else None,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision_satisfied": round(tp / (tp + fp), 6) if (tp + fp) else None,
        "recall_satisfied": round(tp / (tp + fn), 6) if (tp + fn) else None,
        "specificity_not_satisfied": round(tn / (tn + fp), 6) if (tn + fp) else None,
    }


def grouped_rates(rows: list[dict[str, str]], group_col: str, pred_col: str) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(group_col, "")].append(row)
    output = []
    for group, items in sorted(groups.items()):
        stats = rates(items, pred_col)
        output.append({"group": group, **stats})
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-labels", required=True)
    parser.add_argument("--output-dir", default="results/eurographics2027/eg02_auto_human_alignment")
    args = parser.parse_args()

    rows = read_csv(Path(args.final_labels))
    for row in rows:
        row["auto_repair_label"] = auto_label(row, "repair_relation_exact_present")
        row["auto_baseline_label"] = auto_label(row, "baseline_relation_exact_present")
        coord = row.get("coord_rule_label", "")
        row["coord_binary_label"] = coord if coord in BINARY else "not_satisfied"
        row["repair_vs_human"] = "agree" if row["auto_repair_label"] == row.get("final_label") else "disagree"
        row["coord_vs_human"] = "agree" if row["coord_binary_label"] == row.get("final_label") else "disagree"

    binary_rows = [row for row in rows if row.get("final_label") in BINARY]
    repair_disagreements = [
        row for row in binary_rows if row["repair_vs_human"] == "disagree"
    ]
    coord_disagreements = [
        row for row in binary_rows if row["coord_vs_human"] == "disagree"
    ]

    summary = {
        "task": "EG-02 automatic vs adjudicated human alignment",
        "n_relations": len(rows),
        "binary_evaluable_relations": len(binary_rows),
        "not_judgable_relations": sum(row.get("final_label") == "not_judgable" for row in rows),
        "repair_auto_vs_human": rates(rows, "auto_repair_label"),
        "baseline_auto_vs_human": rates(rows, "auto_baseline_label"),
        "coord_rule_vs_human": rates(rows, "coord_binary_label"),
        "repair_disagreement_count": len(repair_disagreements),
        "coord_disagreement_count": len(coord_disagreements),
        "label_counts": dict(Counter(row.get("final_label", "") for row in rows)),
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(
        output_dir / "summary.csv",
        [
            {"metric": "repair_auto_accuracy", "value": summary["repair_auto_vs_human"]["accuracy"]},
            {"metric": "baseline_auto_accuracy", "value": summary["baseline_auto_vs_human"]["accuracy"]},
            {"metric": "coord_rule_accuracy", "value": summary["coord_rule_vs_human"]["accuracy"]},
            {"metric": "binary_evaluable_relations", "value": summary["binary_evaluable_relations"]},
            {"metric": "not_judgable_relations", "value": summary["not_judgable_relations"]},
        ],
        ["metric", "value"],
    )
    write_csv(
        output_dir / "repair_auto_disagreements.csv",
        repair_disagreements,
        [
            "annotation_id",
            "room_type",
            "predicate",
            "subject_class",
            "object_class",
            "final_label",
            "auto_repair_label",
            "coord_rule_label",
            "pair_alignment_status",
            "image_or_view_path",
            "source_text",
        ],
    )
    write_csv(
        output_dir / "coord_rule_disagreements.csv",
        coord_disagreements,
        [
            "annotation_id",
            "room_type",
            "predicate",
            "subject_class",
            "object_class",
            "final_label",
            "auto_repair_label",
            "coord_rule_label",
            "pair_alignment_status",
            "image_or_view_path",
            "source_text",
        ],
    )
    write_csv(output_dir / "repair_by_room.csv", grouped_rates(rows, "room_type", "auto_repair_label"), ["group", "n", "accuracy", "tp", "tn", "fp", "fn", "precision_satisfied", "recall_satisfied", "specificity_not_satisfied"])
    write_csv(output_dir / "repair_by_predicate.csv", grouped_rates(rows, "predicate", "auto_repair_label"), ["group", "n", "accuracy", "tp", "tn", "fp", "fn", "precision_satisfied", "recall_satisfied", "specificity_not_satisfied"])

    print(f"binary_evaluable_relations={summary['binary_evaluable_relations']}")
    print(f"repair_auto_accuracy={summary['repair_auto_vs_human']['accuracy']}")
    print(f"baseline_auto_accuracy={summary['baseline_auto_vs_human']['accuracy']}")
    print(f"coord_rule_accuracy={summary['coord_rule_vs_human']['accuracy']}")
    print(f"repair_disagreement_count={len(repair_disagreements)}")
    print(f"output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
