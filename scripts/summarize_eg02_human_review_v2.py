#!/usr/bin/env python3
"""Summarize EG-02 annotation v2 CSV labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ALLOWED = {"satisfied", "not_satisfied", "uncertain", "not_judgable"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    seen = set()
    for row in rows:
        annotation_id = row.get("annotation_id", "").strip()
        if not annotation_id:
            raise ValueError(f"{path} has empty annotation_id")
        if annotation_id in seen:
            raise ValueError(f"{path} duplicate annotation_id {annotation_id}")
        seen.add(annotation_id)
        label = row.get("human_label", "").strip().lower()
        if label not in ALLOWED:
            raise ValueError(f"{path} invalid human_label for {annotation_id}: {label!r}")
        row["human_label"] = label
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def cohens_kappa(labels_a: dict[str, str], labels_d: dict[str, str]) -> tuple[float, float, float, int]:
    ids_a = set(labels_a)
    ids_d = set(labels_d)
    if ids_a != ids_d:
        raise ValueError(f"annotation id mismatch only_a={sorted(ids_a - ids_d)[:5]} only_d={sorted(ids_d - ids_a)[:5]}")
    ids = sorted(ids_a)
    n = len(ids)
    observed = sum(labels_a[key] == labels_d[key] for key in ids) / n
    all_labels = sorted(set(labels_a.values()) | set(labels_d.values()))
    count_a = Counter(labels_a[key] for key in ids)
    count_d = Counter(labels_d[key] for key in ids)
    expected = sum((count_a[label] / n) * (count_d[label] / n) for label in all_labels)
    kappa = 1.0 if expected == 1.0 and observed == 1.0 else (observed - expected) / (1.0 - expected)
    return kappa, observed, expected, n


def label_agreement_with_coord(rows: list[dict[str, str]]) -> dict[str, object]:
    eligible = [row for row in rows if row.get("coord_rule_label") in {"satisfied", "not_satisfied"} and row["human_label"] in {"satisfied", "not_satisfied"}]
    agree = sum(row["human_label"] == row.get("coord_rule_label") for row in eligible)
    return {
        "n": len(eligible),
        "agreement": round(agree / len(eligible), 6) if eligible else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator-a", required=True)
    parser.add_argument("--annotator-d", required=True)
    parser.add_argument("--output-dir", default="results/eurographics2027/eg02_human_review_v2")
    args = parser.parse_args()

    rows_a = read_csv(Path(args.annotator_a))
    rows_d = read_csv(Path(args.annotator_d))
    by_id_a = {row["annotation_id"]: row for row in rows_a}
    by_id_d = {row["annotation_id"]: row for row in rows_d}
    labels_a = {key: row["human_label"] for key, row in by_id_a.items()}
    labels_d = {key: row["human_label"] for key, row in by_id_d.items()}

    kappa_all, observed_all, expected_all, n_all = cohens_kappa(labels_a, labels_d)
    binary_ids = [
        key for key in labels_a
        if labels_a[key] in {"satisfied", "not_satisfied"}
        and labels_d[key] in {"satisfied", "not_satisfied"}
    ]
    kappa_binary, observed_binary, expected_binary, n_binary = cohens_kappa(
        {key: labels_a[key] for key in binary_ids},
        {key: labels_d[key] for key in binary_ids},
    )

    disagreements = []
    room_stats: dict[str, Counter] = defaultdict(Counter)
    for key in sorted(labels_a):
        row = by_id_a[key]
        room = row.get("room_type", "")
        room_stats[room]["total"] += 1
        room_stats[room]["agree"] += int(labels_a[key] == labels_d[key])
        if labels_a[key] in {"satisfied", "not_satisfied"} and labels_d[key] in {"satisfied", "not_satisfied"}:
            room_stats[room]["binary_total"] += 1
            room_stats[room]["binary_agree"] += int(labels_a[key] == labels_d[key])
        if labels_a[key] != labels_d[key]:
            disagreements.append(
                {
                    "annotation_id": key,
                    "room_type": room,
                    "predicate": row.get("predicate", ""),
                    "subject_class": row.get("subject_class", ""),
                    "object_class": row.get("object_class", ""),
                    "label_a": labels_a[key],
                    "label_d": labels_d[key],
                    "coord_rule_label": row.get("coord_rule_label", ""),
                    "pair_alignment_status": row.get("pair_alignment_status", ""),
                    "image_or_view_path": row.get("image_or_view_path", ""),
                    "source_text": row.get("source_text", ""),
                }
            )

    summary = {
        "task": "EG-02 human review v2",
        "status": "PASS_KAPPA_GATE" if kappa_all >= 0.70 else "FAIL_KAPPA_GATE",
        "threshold": 0.70,
        "n_relations": n_all,
        "all_label_kappa": round(kappa_all, 6),
        "all_label_observed_agreement": round(observed_all, 6),
        "all_label_expected_agreement": round(expected_all, 6),
        "binary_n_relations": n_binary,
        "binary_kappa": round(kappa_binary, 6),
        "binary_observed_agreement": round(observed_binary, 6),
        "binary_expected_agreement": round(expected_binary, 6),
        "disagreement_count": len(disagreements),
        "label_counts_a": dict(Counter(labels_a.values())),
        "label_counts_d": dict(Counter(labels_d.values())),
        "coord_rule_agreement_a": label_agreement_with_coord(rows_a),
        "coord_rule_agreement_d": label_agreement_with_coord(rows_d),
        "room_stats": {
            room: {
                "total": counts["total"],
                "agreement": round(counts["agree"] / counts["total"], 6),
                "binary_total": counts["binary_total"],
                "binary_agreement": round(counts["binary_agree"] / counts["binary_total"], 6) if counts["binary_total"] else None,
            }
            for room, counts in sorted(room_stats.items())
        },
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(output_dir / "summary.csv", [{"metric": k, "value": v} for k, v in summary.items() if not isinstance(v, (dict, list))], ["metric", "value"])
    write_csv(
        output_dir / "disagreements.csv",
        disagreements,
        ["annotation_id", "room_type", "predicate", "subject_class", "object_class", "label_a", "label_d", "coord_rule_label", "pair_alignment_status", "image_or_view_path", "source_text"],
    )
    adjudication_rows = [
        {
            **row,
            "final_label": "",
            "adjudicator_id": "",
            "adjudication_notes": "",
        }
        for row in disagreements
    ]
    write_csv(
        output_dir / "adjudication_template.csv",
        adjudication_rows,
        [
            "annotation_id",
            "room_type",
            "predicate",
            "subject_class",
            "object_class",
            "label_a",
            "label_d",
            "coord_rule_label",
            "pair_alignment_status",
            "final_label",
            "adjudicator_id",
            "adjudication_notes",
            "image_or_view_path",
            "source_text",
        ],
    )
    write_csv(output_dir / "eg02_human_review_v2_A.csv", rows_a, list(rows_a[0].keys()))
    write_csv(output_dir / "eg02_human_review_v2_D.csv", rows_d, list(rows_d[0].keys()))

    print(f"n_relations={n_all}")
    print(f"all_label_kappa={kappa_all:.4f}")
    print(f"binary_n_relations={n_binary}")
    print(f"binary_kappa={kappa_binary:.4f}")
    print(f"disagreement_count={len(disagreements)}")
    print(f"coord_rule_agreement_a={summary['coord_rule_agreement_a']}")
    print(f"coord_rule_agreement_d={summary['coord_rule_agreement_d']}")
    print(f"output_dir={output_dir}")
    if kappa_all < 0.70:
        print("EG-02 V2 HUMAN REVIEW: FAIL all-label kappa below 0.70")
        return 1
    print("EG-02 V2 HUMAN REVIEW: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
