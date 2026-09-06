#!/usr/bin/env python3
"""Build and validate the anonymous EG13 reproducibility package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


FORBIDDEN = {
    "windows_user_path": re.compile(rb"[A-Za-z]:[\\/]Users[\\/]", re.I),
    "root_path": re.compile(rb"/root/", re.I),
    "cloud_host": re.compile(rb"(?:autodl|seetacloud)", re.I),
    "public_repository_identity": re.compile(rb"(?:BJTUworldmodellab|research_worldmodel|jomify|sachi25250102)", re.I),
    "github_pat": re.compile(rb"github_pat_[A-Za-z0-9_]+"),
    "openai_key": re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{16,}"),
    "private_key": re.compile(rb"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    "email": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def semantic_layout_hash(payload: Any) -> str | None:
    if not isinstance(payload, dict) or "layouts" not in payload:
        return None
    encoded = json.dumps(payload["layouts"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sanitize_string(value: str) -> str:
    value = re.sub(r"[A-Za-z]:[\\/]Users[\\/][^\\/\s\"']+", "<redacted-local-user>", value, flags=re.I)
    value = re.sub(r"/root(?:/[^\s\"']*)?", "<redacted-origin>", value, flags=re.I)
    value = re.sub(r"(?:BJTUworldmodellab|jomify|sachi25250102(?:-wq)?)/research_worldmodel", "anonymous/repository", value, flags=re.I)
    value = re.sub(r"github_pat_[A-Za-z0-9_]+", "<redacted-token>", value)
    value = re.sub(r"sk-(?:proj-)?[A-Za-z0-9_-]{16,}", "<redacted-key>", value)
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<redacted-email>", value)
    value = re.sub(r"(?:autodl|seetacloud)", "anonymous-cloud", value, flags=re.I)
    return value


def sanitize_json(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {str(k): sanitize_json(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item, key) for item in value]
    if isinstance(value, str):
        lowered = key.lower()
        if "commit" in lowered or lowered in {"repository", "branch", "method_code_anchor"}:
            return "withheld_for_double_blind_review"
        return sanitize_string(value)
    return value


def write_sanitized_json(source: Path, destination: Path) -> dict[str, Any]:
    original = json.loads(source.read_text(encoding="utf-8"))
    sanitized = sanitize_json(original)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(sanitized, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "source_semantic_layouts_sha256": semantic_layout_hash(original),
        "packaged_semantic_layouts_sha256": semantic_layout_hash(sanitized),
    }


def scan_package(root: Path) -> list[dict[str, Any]]:
    findings = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        data = path.read_bytes()
        for name, pattern in FORBIDDEN.items():
            if pattern.search(data):
                findings.append({"file": path.relative_to(root).as_posix(), "rule": name})
    return findings


def deterministic_zip(root: Path, destination: Path) -> None:
    if destination.exists():
        destination.unlink()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            info = zipfile.ZipInfo((Path(root.name) / path.relative_to(root)).as_posix())
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    default_output = repo / "artifacts" / "eurographics2027" / "eg13_anonymous_repro"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=default_output)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    allowed_parent = (repo / "artifacts" / "eurographics2027").resolve()
    if output.parent != allowed_parent or output.name != "eg13_anonymous_repro":
        raise SystemExit(f"refusing to replace unexpected output path: {output}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    sources: list[tuple[Path, Path, bool]] = [
        (repo / "eg07_final_delivery_20260814" / "eg05" / "audit.json", Path("data/eg05/audit.json"), True),
        (repo / "eg07_final_delivery_20260814" / "eg05" / "per_relation.csv", Path("data/eg05/per_relation.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "eg05" / "per_scene.csv", Path("data/eg05/per_scene.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "eg05" / "summary.csv", Path("data/eg05/summary.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "eg06" / "audit.json", Path("data/eg06/audit.json"), True),
        (repo / "eg07_final_delivery_20260814" / "eg06" / "eg06_augmented_layouts.json", Path("data/eg06/eg06_augmented_layouts.json"), True),
        (repo / "eg07_final_delivery_20260814" / "eg06" / "movement_audit.csv", Path("data/eg06/movement_audit.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "eg06" / "per_relation.csv", Path("data/eg06/per_relation.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "eg06" / "per_scene.csv", Path("data/eg06/per_scene.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "eg06" / "summary.csv", Path("data/eg06/summary.csv"), False),
        (repo / "eg07_final_delivery_20260814" / "layouts" / "layouts.json", Path("data/layouts/layouts.json"), True),
        (repo / "eg07_final_delivery_20260814" / "layouts" / "validation.json", Path("data/layouts/validation.json"), True),
        (repo / "eg07_final_delivery_20260814" / "layouts" / "validation_recheck.json", Path("data/layouts/validation_recheck.json"), True),
        (repo / "eg07_final_delivery_20260814" / "final" / "eg07_final_metrics_20260814.json", Path("data/final/final_metrics.json"), True),
        (repo / "results" / "independent_eval" / "eg2027" / "eg08_paired_statistics_20260816" / "paired_statistics.json", Path("data/stats/paired_statistics.json"), True),
        (repo / "results" / "independent_eval" / "eg2027" / "eg08_paired_statistics_20260816" / "paired_ci.csv", Path("data/stats/paired_ci.csv"), False),
        (repo / "results" / "independent_eval" / "eg2027" / "eg08_paired_statistics_20260816" / "canonical_eg06_ci.json", Path("data/stats/canonical_eg06_ci.json"), True),
        (repo / "evaluation" / "independent_relation_evaluator.py", Path("evaluation/independent_relation_evaluator.py"), False),
        (repo / "evaluation" / "independent_protocol.md", Path("evaluation/independent_protocol.md"), False),
        (repo / "fixtures" / "eg13_smoke_layouts.json", Path("fixtures/eg13_smoke_layouts.json"), True),
        (repo / "scripts" / "reproduce_eg13_main_table.py", Path("scripts/reproduce_main_table.py"), False),
        (repo / "scripts" / "run_eg13_smoke_test.py", Path("scripts/smoke_test.py"), False),
    ]
    semantic_checks = {}
    for source, relative, is_json in sources:
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if is_json:
            semantic_checks[relative.as_posix()] = write_sanitized_json(source, destination)
        else:
            shutil.copyfile(source, destination)

    readme = """# Anonymous EG2027 reproducibility package

This package rebuilds the three quantitative paper tables from the frozen 531-scene evidence and runs a minimal independent-evaluator smoke test. It requires Python 3.9 or later and no third-party packages.

## One-command table reproduction

```bash
python scripts/reproduce_main_table.py
```

Expected terminal status: `PASS`. Generated machine- and human-readable outputs are written under `output/reproduction/`.

## Minimal evaluator smoke test

```bash
python scripts/smoke_test.py
```

Expected terminal status: `PASS` with four evaluated relation rows.

## Scope and claim boundary

- Population: the frozen existing-protocol validation set (162 bedrooms, 192 living rooms, 177 dining rooms; 531 scenes total).
- Primary denominator: 808 explicit target relations. Missing targets remain in the denominator; unsupported targets are counted and expected to be zero.
- Main method: collision-gated Floor-Prior applied after a fixed pretrained InstructScene generator.
- Supported comparison: the main method exceeds the mean of three per-object movement-matched random controls under the frozen paired scene-level relation-weighted bootstrap protocol.
- Unsupported comparisons: the confidence intervals versus the original generator and the generic optimizer include zero. This package does not establish superiority to ReSpace, SDGScenes, or any cross-protocol method.

## Anonymous sanitization

Machine-specific paths, repository identity, user identifiers, e-mail addresses, cloud-host identifiers, credentials, and public commit anchors are removed or withheld. For JSON layout containers, `MANIFEST.json` records a semantic hash over the `layouts` array before and after sanitization; those hashes must remain identical. Container file hashes differ when provenance metadata is sanitized.

Third-party datasets, pretrained checkpoints, and the original room-level generator output JSON files are not redistributed. Consequently, this package supports layout-to-statistics reconstruction and evaluator smoke testing, not a fresh end-to-end generator run.
"""
    (output / "README.md").write_text(readme, encoding="utf-8")

    pre_manifest_findings = scan_package(output)
    if pre_manifest_findings:
        print(json.dumps({"status": "FAIL", "anonymity_findings": pre_manifest_findings}, indent=2))
        raise SystemExit(1)
    for relative, check in semantic_checks.items():
        if check["source_semantic_layouts_sha256"] != check["packaged_semantic_layouts_sha256"]:
            raise SystemExit(f"semantic layout content changed during sanitization: {relative}")

    manifest_files = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        manifest_files.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "schema": "eg2027-eg13-anonymous-package-v1",
        "status": "PASS",
        "created_date": "2026-08-25",
        "file_count_excluding_manifest": len(manifest_files),
        "files": manifest_files,
        "semantic_layout_checks": semantic_checks,
        "anonymity_scan": {"status": "PASS", "finding_count": 0, "rules": sorted(FORBIDDEN)},
    }
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    reproduction = subprocess.run(
        [sys.executable, str(output / "scripts" / "reproduce_main_table.py")],
        cwd=output,
        text=True,
        capture_output=True,
    )
    smoke = subprocess.run(
        [sys.executable, str(output / "scripts" / "smoke_test.py")],
        cwd=output,
        text=True,
        capture_output=True,
    )
    findings = scan_package(output)
    if reproduction.returncode or smoke.returncode or findings:
        print(json.dumps({"status": "FAIL", "reproduction": reproduction.stdout + reproduction.stderr, "smoke": smoke.stdout + smoke.stderr, "anonymity_findings": findings}, indent=2))
        raise SystemExit(1)

    # Refresh the manifest after the reproduction outputs have been created.
    manifest_files = []
    for path in sorted(item for item in output.rglob("*") if item.is_file() and item.name != "MANIFEST.json"):
        manifest_files.append({"path": path.relative_to(output).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest.update({
        "file_count_excluding_manifest": len(manifest_files),
        "files": manifest_files,
        "clean_environment_checks": {
            "reproduction": "PASS",
            "evaluator_smoke": "PASS",
        },
    })
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    findings = scan_package(output)
    if findings:
        raise SystemExit(f"anonymity scan failed after manifest refresh: {findings}")

    zip_path = output.with_suffix(".zip")
    deterministic_zip(output, zip_path)
    result = {
        "status": "PASS",
        "package": output.relative_to(repo).as_posix(),
        "zip": zip_path.relative_to(repo).as_posix(),
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256(zip_path),
        "reproduction": {
            "status": json.loads(reproduction.stdout)["status"],
            "errors": json.loads(reproduction.stdout)["errors"],
        },
        "smoke": json.loads(smoke.stdout),
        "anonymity_findings": findings,
    }
    (allowed_parent / "eg13_build_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
