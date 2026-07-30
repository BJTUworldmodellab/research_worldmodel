#!/usr/bin/env python3
"""Check that EG-02 protocol-freeze files exist and contain key commitments."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED = {
    "evaluation/independent_protocol.md": [
        "Non-Negotiable Independence Rule",
        "Instance Matching Rule",
        "Missing Object Handling",
        "Output Schema",
    ],
    "docs/eurographics2027/eg02_human_review_protocol.md": [
        "kappa >= 0.70",
        "at least 90 target relations",
        "Bedroom",
        "Living room",
        "Dining room",
    ],
    "annotations/eurographics2027/eg02_relation_annotation_template.csv": [
        "annotation_id,scene_id,room_type",
        "human_label",
    ],
    "annotations/eurographics2027/eg02_sampling_plan.csv": [
        "bedroom,30",
        "livingroom,30",
        "diningroom,30",
    ],
    "docs/eurographics2027/eg02_protocol_freeze_handoff_20260730.md": [
        "EG-02 should remain `IN PROGRESS`",
        "Hand-off to EG-05",
    ],
    "scripts/compute_eg02_kappa.py": [
        "cohens_kappa",
        "threshold",
    ],
    "scripts/validate_eg02_sampling_plan.py": [
        "min-per-room",
        "EG-02 SAMPLING PLAN: PASS",
    ],
    "scripts/write_eg02_protocol_manifest.py": [
        "eg2027-eg02-v1",
        "PENDING_EG05_IMPLEMENTATION",
    ],
    "manifests/eurographics2027/eg02_protocol_manifest.json": [
        "eg2027-eg02-v1",
        "cohens_kappa_min",
        "PENDING_EG05_ACTUAL_SAMPLE_EXPORT",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    failures = []
    for rel, needles in REQUIRED.items():
        path = root / rel
        if not path.exists():
            failures.append(f"missing: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [needle for needle in needles if needle not in text]
        if missing:
            failures.append(f"{rel} missing anchors: {missing}")
        else:
            print(f"OK {rel}")

    if failures:
        print("EG-02 CHECK: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    print("EG-02 CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
