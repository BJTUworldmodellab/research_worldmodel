#!/usr/bin/env python3
"""Write the EG-02 protocol-freeze manifest with file hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


FILES = [
    "evaluation/independent_protocol.md",
    "docs/eurographics2027/eg02_human_review_protocol.md",
    "annotations/eurographics2027/eg02_relation_annotation_template.csv",
    "annotations/eurographics2027/eg02_sampling_plan.csv",
    "docs/eurographics2027/eg02_protocol_freeze_handoff_20260730.md",
    "scripts/check_eg02_protocol_files.py",
    "scripts/compute_eg02_kappa.py",
    "scripts/validate_eg02_sampling_plan.py",
    "scripts/write_eg02_protocol_manifest.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--output",
        default="manifests/eurographics2027/eg02_protocol_manifest.json",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    file_hashes = {}
    for rel in FILES:
        path = root / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        file_hashes[rel] = sha256(path)

    payload = {
        "protocol": "EG-02 independent relation evaluation protocol",
        "version": "eg2027-eg02-v1",
        "status": "IN PROGRESS",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "cohens_kappa_min": 0.70,
        "human_review_min_relations": 90,
        "human_review_rooms": ["bedroom", "livingroom", "diningroom"],
        "evaluator_independence": "must not import repair optimizer relation logic",
        "data_hash": "PENDING_EG05_ACTUAL_SAMPLE_EXPORT",
        "evaluator_commit_hash": "PENDING_EG05_IMPLEMENTATION",
        "files": file_hashes,
    }

    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
