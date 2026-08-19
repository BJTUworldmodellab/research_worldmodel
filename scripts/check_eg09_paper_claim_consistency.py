#!/usr/bin/env python3
"""Validate the EG-09 paper-facing claim freeze against EG07/EG08 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SCHEMA = "eg2027-eg09-paper-claim-freeze-v1"
MAIN_TEX = Path("paper/neurips_ra_instructscene/main.tex")
CLAIM_MAP = Path("docs/eurographics2027/claim_to_table_map_eg2027.md")
EG07_METRICS = Path(
    "eg07_final_delivery_20260814/final/eg07_final_metrics_20260814.json"
)
EG08_CANONICAL = Path(
    "results/independent_eval/eg2027/eg08_paired_statistics_20260816/"
    "canonical_eg06_ci.json"
)
EG08_MANIFEST = Path("manifests/eurographics2027/eg08_paired_statistics_manifest.json")
EG09_MANIFEST = Path("manifests/eurographics2027/eg09_paper_claim_freeze_manifest.json")
PDF_STATUS = Path("paper/neurips_ra_instructscene/EG09_PDF_STATUS.md")

# Development anchors are allowed only in the explicitly labelled historical
# boundary of the claim map, not in current paper-facing prose or tables.
STALE_TOKENS = (
    "0.8449",
    "0.6871",
    "0.7212",
    "+10.2",
    "+14.3",
    "+13.4",
    "0.8163",
    "0.6395",
    "0.6729",
    "+7.76",
    "+8.84",
    "+7.81",
    "0.7040",
    "+8.2",
)

REQUIRED_MAIN_TOKENS = (
    "frozen 531-scene evaluation",
    "0.6399",
    "0.6254",
    "1.44 percentage points",
    "0.75 to 2.20 points",
    "1,061",
    "1,075",
    "confidence interval includes zero",
    "generic optimizer",
    "93 cases per variant",
    "808 target relations",
    "0.7265 & 0.7306",
    "0.6054 & 0.6122",
    "0.5836 & 0.5874",
    "154 & 8 & 162",
    "174 & 18 & 192",
    "164 & 13 & 177",
)

REQUIRED_BOUNDARY_TOKENS = (
    "not superiority to every comparator",
    "no superiority claim for that comparison",
    "statistically inconclusive",
    "does not imply that collision-free generation has been solved",
    "remaining provenance gap",
)


def close(actual: float, expected: float, tolerance: float = 1e-12) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_text_surfaces(main_text: str, claim_text: str) -> list[str]:
    errors: list[str] = []
    for token in STALE_TOKENS:
        if token in main_text:
            errors.append(f"paper contains stale development token: {token}")

    boundary_marker = "## Historical-number boundary"
    if boundary_marker not in claim_text:
        errors.append("claim map lacks the historical-number boundary")
        active_claim_text = claim_text
    else:
        active_claim_text = claim_text.split(boundary_marker, 1)[0]
    for token in STALE_TOKENS:
        if token in active_claim_text:
            errors.append(f"active claim map contains stale development token: {token}")

    for token in REQUIRED_MAIN_TOKENS:
        if token not in main_text:
            errors.append(f"paper lacks required formal token: {token}")
    for token in REQUIRED_BOUNDARY_TOKENS:
        if token not in main_text:
            errors.append(f"paper lacks required claim boundary: {token}")

    if "EG09_CLAIMS_FROZEN" not in claim_text:
        errors.append("claim map lacks EG09_CLAIMS_FROZEN marker")
    return errors


def validate(repo_root: Path) -> dict[str, Any]:
    paths = {
        "main_tex": repo_root / MAIN_TEX,
        "claim_map": repo_root / CLAIM_MAP,
        "eg07_metrics": repo_root / EG07_METRICS,
        "eg08_canonical": repo_root / EG08_CANONICAL,
        "eg08_manifest": repo_root / EG08_MANIFEST,
        "eg09_manifest": repo_root / EG09_MANIFEST,
        "pdf_status": repo_root / PDF_STATUS,
    }
    errors = [f"missing required file: {path}" for path in paths.values() if not path.is_file()]
    if errors:
        return {"schema": SCHEMA, "status": "EG09_NO_GO", "errors": errors}

    main_text = paths["main_tex"].read_text(encoding="utf-8")
    claim_text = paths["claim_map"].read_text(encoding="utf-8")
    errors.extend(check_text_surfaces(main_text, claim_text))

    eg07 = load_json(paths["eg07_metrics"])
    canonical = load_json(paths["eg08_canonical"])
    eg08_manifest = load_json(paths["eg08_manifest"])
    eg09_manifest = load_json(paths["eg09_manifest"])

    checks = {
        "scenes": (eg07["structural"]["scenes"], 531),
        "relations": (eg07["structural"]["target_relations"], 808),
        "main_accuracy": (eg07["eg05"]["relation_accuracy"]["main_overall"], 0.6398514851485149),
        "baseline_accuracy": (eg07["eg05"]["relation_accuracy"]["baseline_overall"], 0.6349009900990099),
        "random_mean_accuracy": (eg07["eg06"]["baselines"]["random_mean"], 0.6254125412541254),
        "chosen_collision_pairs": (eg07["structural"]["chosen_main_collision_pairs_total"], 1061),
        "baseline_collision_pairs": (eg07["structural"]["baseline_collision_pairs_total"], 1075),
        "repair_selected": (eg07["structural"]["gate_decision"]["repair"], 492),
        "baseline_fallback": (eg07["structural"]["gate_decision"]["fallback_baseline"], 39),
    }
    for name, (actual, expected) in checks.items():
        if isinstance(expected, float):
            if not close(float(actual), expected):
                errors.append(f"{name} mismatch: {actual} != {expected}")
        elif actual != expected:
            errors.append(f"{name} mismatch: {actual} != {expected}")

    room_relations = eg07["eg05"]["relation_accuracy"]
    room_counts = eg07["structural"]["scene_count_by_room"]
    room_gates = eg07["structural"]["gate_decision_by_room"]
    for room in ("bedroom", "livingroom", "diningroom"):
        frozen_room = eg09_manifest["formal_relation_accuracy"][room]
        for variant in ("baseline", "main"):
            actual = float(room_relations[variant][room])
            expected = float(frozen_room[variant])
            if not close(actual, expected):
                errors.append(f"{room} {variant} mismatch in EG09 manifest")
        if room_counts[room] != sum(room_gates[room].values()):
            errors.append(f"{room} gate decisions do not sum to scene count")

    primary = canonical["random_mean"]
    expected_primary = eg08_manifest["primary_result"]
    for name, actual, expected in (
        ("primary_gain", primary["relation_weighted_diff"], expected_primary["gain"]),
        ("primary_ci_low", primary["relation_weighted_ci95"][0], expected_primary["ci95_low"]),
        ("primary_ci_high", primary["relation_weighted_ci95"][1], expected_primary["ci95_high"]),
    ):
        if not close(float(actual), float(expected)):
            errors.append(f"{name} mismatch between EG08 canonical data and manifest")

    if primary["relation_weighted_ci95"][0] <= 0:
        errors.append("primary random-mean interval lower bound is not positive")
    if canonical["baseline"]["relation_weighted_ci95"][0] > 0:
        errors.append("baseline interval unexpectedly supports superiority")
    if not (
        canonical["generic_relation_optimizer"]["relation_weighted_ci95"][0]
        <= 0
        <= canonical["generic_relation_optimizer"]["relation_weighted_ci95"][1]
    ):
        errors.append("generic-optimizer interval no longer includes zero")

    if eg09_manifest.get("schema") != SCHEMA:
        errors.append("EG09 manifest schema mismatch")
    if eg09_manifest.get("status") != "EG09_CLAIMS_FROZEN":
        errors.append("EG09 manifest status is not EG09_CLAIMS_FROZEN")
    compiled = eg09_manifest.get("compiled_artifact", {})
    if compiled.get("status") != "STALE_PRE_EG09_NOT_FOR_DELIVERY":
        errors.append("pre-EG09 PDF is not explicitly excluded from delivery")
    pdf_status = paths["pdf_status"].read_text(encoding="utf-8")
    if "not an EG09 deliverable" not in pdf_status:
        errors.append("PDF status file lacks the delivery exclusion")
    for name, item in eg09_manifest.get("inputs", {}).items():
        if "sha256" not in item:
            continue
        input_path = repo_root / item["path"]
        if not input_path.is_file():
            errors.append(f"manifest input is missing: {name}")
        elif sha256(input_path) != item["sha256"]:
            errors.append(f"manifest input hash mismatch: {name}")

    return {
        "schema": SCHEMA,
        "status": "EG09_CLAIMS_FROZEN" if not errors else "EG09_NO_GO",
        "errors": errors,
        "formal_result": {
            "scenes": 531,
            "relations": 808,
            "main_accuracy": checks["main_accuracy"][0],
            "baseline_accuracy": checks["baseline_accuracy"][0],
            "random_mean_accuracy": checks["random_mean_accuracy"][0],
            "main_vs_random_mean_gain": primary["relation_weighted_diff"],
            "main_vs_random_mean_ci95": primary["relation_weighted_ci95"],
            "chosen_collision_pairs": checks["chosen_collision_pairs"][0],
            "baseline_collision_pairs": checks["baseline_collision_pairs"][0],
        },
        "historical_files_rewritten": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = validate(args.repo_root.resolve())
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else args.repo_root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if payload["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
