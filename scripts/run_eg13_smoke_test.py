#!/usr/bin/env python3
"""Run a dependency-free smoke test of the independent relation evaluator."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", type=Path, default=root / "evaluation" / "independent_relation_evaluator.py")
    parser.add_argument("--fixture", type=Path, default=root / "fixtures" / "eg13_smoke_layouts.json")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="eg13-smoke-") as tmp:
        output = Path(tmp) / "out"
        subprocess.run(
            [sys.executable, str(args.evaluator), "--input", str(args.fixture), "--output-dir", str(output), "--run-id", "anonymous-smoke"],
            check=True,
            text=True,
            capture_output=True,
        )
        with (output / "per_relation.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        by_key = {(row["layout_variant"], row["relation_id"]): row for row in rows}
        expected = {
            ("baseline", "right_relation"): "0",
            ("collision_gated_floor_prior", "right_relation"): "1",
            ("baseline", "missing_relation"): "0",
            ("collision_gated_floor_prior", "missing_relation"): "0",
        }
        errors = []
        for key, value in expected.items():
            if key not in by_key or by_key[key]["is_satisfied"] != value:
                errors.append(f"{key}: expected is_satisfied={value}")
        audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
        if audit["thresholds"] != {"close_distance": 0.75, "direction_margin": 0.05, "far_distance": 1.6, "vertical_margin": 0.05}:
            errors.append("threshold audit mismatch")
        result = {"status": "PASS" if not errors else "FAIL", "relations_checked": len(rows), "errors": errors}
        print(json.dumps(result, indent=2))
        if errors:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
