#!/usr/bin/env python3
"""Validate the EG-04 Eurographics 2027 method freeze files.

This check is intentionally lightweight and dependency-free. It avoids a YAML
parser so that a clean reproduction environment can run it before installing the
full project stack.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

CONFIG = ROOT / "configs" / "eurographics2027" / "paper_main.yaml"
MATRIX = ROOT / "docs" / "eurographics2027" / "eg04_method_variant_matrix_20260805.md"
DECISION = ROOT / "docs" / "eurographics2027" / "eg04_freeze_decision_record_20260805.md"
MANIFEST = ROOT / "manifests" / "eurographics2027" / "eg04_freeze_manifest.json"

REQUIRED_FILES = [CONFIG, MATRIX, DECISION, MANIFEST]

REQUIRED_STRINGS = {
    CONFIG: [
        'version: "2026-08-05-eg04-freeze-v1"',
        'status: "EG-04 method/config/code freeze"',
        'status: "skipped_no_go"',
        'display_name: "Collision-gated Floor-Prior"',
        'default_config_id: "floor_prior_max1.8_mesh_p2_close0.75_far1.6"',
        "code_commit",
        "config_sha256",
        "environment_summary",
    ],
    MATRIX: [
        "EG-03 is skipped",
        "`Collision-gated Floor-Prior`",
        "| CW-GCP | Skipped / future work | No |",
        "| Weighted |",
        "Do not use `0.8449 / 0.6871 / 0.7212` as Floor-Prior main results.",
    ],
    DECISION: [
        "Freeze `Collision-gated Floor-Prior` as the only Eurographics 2027 main method.",
        "`feb37414db42faec3d600b66d17186ed3da8a22e`",
        "EG-03 is recorded as `skipped_no_go`",
        "fix implementation bugs found by EG-05/EG-06/EG-07",
        "change relation thresholds to improve the table after seeing results",
    ],
}

FORBIDDEN_MAIN_PROMOTION_PATTERNS = [
    ("CW-GCP is the main method", ["Do not say CW-GCP is the main method"]),
    ("Direct Repair is the main method", []),
    ("CommonScenes is the main method", []),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(messages: list[str]) -> None:
    for msg in messages:
        print(f"FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    errors: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        fail(errors)

    config_text = CONFIG.read_text(encoding="utf-8")
    matrix_text = MATRIX.read_text(encoding="utf-8")
    decision_text = DECISION.read_text(encoding="utf-8")

    for path, needles in REQUIRED_STRINGS.items():
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{path.relative_to(ROOT)} missing required string: {needle}")

    for needle, allowed_contexts in FORBIDDEN_MAIN_PROMOTION_PATTERNS:
        combined = "\n".join([config_text, matrix_text, decision_text])
        allowed_hits = sum(combined.count(context) for context in allowed_contexts)
        total_hits = combined.count(needle)
        if total_hits > allowed_hits:
            errors.append(f"forbidden main-method promotion wording found: {needle}")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"manifest is not valid JSON: {exc}")
        manifest = {}

    if manifest:
        expected_hash = sha256(CONFIG)
        actual_hash = manifest.get("frozen_main_method", {}).get("config_sha256")
        if actual_hash != expected_hash:
            errors.append(
                "config hash mismatch: "
                f"manifest={actual_hash} actual={expected_hash}"
            )

        checks = {
            "manifest_version": "2026-08-05-eg04-freeze-v1",
            "status": "frozen",
            "method_code_commit": "feb37414db42faec3d600b66d17186ed3da8a22e",
        }
        for key, expected in checks.items():
            if manifest.get(key) != expected:
                errors.append(f"manifest {key} expected {expected!r}, got {manifest.get(key)!r}")

        method = manifest.get("frozen_main_method", {})
        if method.get("id") != "collision_gated_floor_prior":
            errors.append("manifest main method id is not collision_gated_floor_prior")
        if method.get("config_id") != "floor_prior_max1.8_mesh_p2_close0.75_far1.6":
            errors.append("manifest config id is not the frozen Floor-Prior config")
        if not method.get("collision_gate"):
            errors.append("manifest collision_gate must be true")
        if not method.get("preserve_height"):
            errors.append("manifest preserve_height must be true")

        if manifest.get("eg03_decision", {}).get("status") != "skipped_no_go":
            errors.append("EG-03 decision is not recorded as skipped_no_go")

    if errors:
        fail(errors)

    print("EG-04 freeze check passed.")
    print(f"config_sha256={sha256(CONFIG)}")
    print("main_method=collision_gated_floor_prior")
    print("eg03_decision=skipped_no_go")


if __name__ == "__main__":
    main()
