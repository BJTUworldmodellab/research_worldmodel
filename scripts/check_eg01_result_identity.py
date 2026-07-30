#!/usr/bin/env python3
"""Check EG-01 result identity consistency.

This script intentionally checks only the Eurographics 2027 identity files and
the paper draft paths declared in the manifest. It does not rewrite old T05
materials, because EG-01 is a separate submission track.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_missing(text: str, needles: Iterable[str]) -> List[str]:
    return [needle for needle in needles if needle not in text]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument(
        "--manifest",
        default="manifests/eurographics2027/eg01_main_method_manifest.json",
        help="EG-01 manifest path relative to root",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / args.manifest
    if not manifest_path.exists():
        print(f"FAIL missing manifest: {manifest_path}")
        return 1

    manifest = json.loads(read_text(manifest_path))
    scan_policy: Dict = manifest.get("scan_policy", {})
    strict_files = scan_policy.get("strict_files", [])
    paper_files = set(scan_policy.get("paper_files", []))
    required = scan_policy.get("required_main_strings", [])
    forbidden_abstract = scan_policy.get("abstract_forbidden_strings", [])

    failures: List[str] = []
    corpus_parts: List[str] = []

    print("EG-01 manifest:", manifest_path)
    print("Main method:", manifest["main_method"]["display_name"])
    print("Config:", manifest["main_method"]["config_id"])
    print()

    for rel in strict_files:
        path = root / rel
        if not path.exists():
            failures.append(f"missing strict file: {rel}")
            continue

        text = read_text(path)
        corpus_parts.append(text)
        digest = sha256_file(path)
        print(f"FILE {rel}")
        print(f"  sha256={digest}")

        forbidden_found = [x for x in forbidden_abstract if rel in paper_files and x in text]
        if forbidden_found:
            print(f"  forbidden abstract/main identity strings found: {', '.join(forbidden_found)}")
            failures.append(f"{rel} contains forbidden EG-01 main identity strings: {forbidden_found}")

    corpus = "\n".join(corpus_parts)
    missing_required = find_missing(corpus, required)
    if missing_required:
        failures.append(f"EG-01 corpus missing required anchors: {missing_required}")

    print()
    if failures:
        print("EG-01 CHECK: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    print("EG-01 CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
