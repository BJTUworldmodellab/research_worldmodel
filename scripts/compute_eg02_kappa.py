#!/usr/bin/env python3
"""Compute Cohen's kappa for EG-02 double annotation CSV files."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def read_labels(path: Path, annotator: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"annotation_id", "human_label"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        for row in reader:
            annotation_id = (row.get("annotation_id") or "").strip()
            label = (row.get("human_label") or "").strip().lower()
            if not annotation_id:
                continue
            if not label:
                raise ValueError(f"{path} has empty human_label for {annotation_id}")
            if annotation_id in labels:
                raise ValueError(f"{path} has duplicate annotation_id: {annotation_id}")
            labels[annotation_id] = label
    if not labels:
        raise ValueError(f"{path} has no labels for {annotator}")
    return labels


def cohens_kappa(labels_a: dict[str, str], labels_b: dict[str, str]) -> tuple[float, int, float, float]:
    ids_a = set(labels_a)
    ids_b = set(labels_b)
    if ids_a != ids_b:
        only_a = sorted(ids_a - ids_b)
        only_b = sorted(ids_b - ids_a)
        raise ValueError(f"annotation_id mismatch: only_a={only_a[:5]} only_b={only_b[:5]}")

    ids = sorted(ids_a)
    n = len(ids)
    agree = sum(labels_a[item] == labels_b[item] for item in ids)
    observed = agree / n

    labels = sorted(set(labels_a.values()) | set(labels_b.values()))
    counts_a = Counter(labels_a[item] for item in ids)
    counts_b = Counter(labels_b[item] for item in ids)
    expected = sum((counts_a[label] / n) * (counts_b[label] / n) for label in labels)
    if expected == 1.0:
        kappa = 1.0 if observed == 1.0 else 0.0
    else:
        kappa = (observed - expected) / (1.0 - expected)
    return kappa, n, observed, expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator-a", required=True, help="CSV labels from annotator A")
    parser.add_argument("--annotator-b", required=True, help="CSV labels from annotator B")
    parser.add_argument("--threshold", type=float, default=0.70)
    args = parser.parse_args()

    labels_a = read_labels(Path(args.annotator_a), "A")
    labels_b = read_labels(Path(args.annotator_b), "B")
    kappa, n, observed, expected = cohens_kappa(labels_a, labels_b)

    print(f"relations={n}")
    print(f"observed_agreement={observed:.4f}")
    print(f"expected_agreement={expected:.4f}")
    print(f"cohens_kappa={kappa:.4f}")
    if kappa < args.threshold:
        print(f"EG-02 KAPPA: FAIL below threshold {args.threshold:.2f}")
        return 1
    print(f"EG-02 KAPPA: PASS threshold {args.threshold:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
