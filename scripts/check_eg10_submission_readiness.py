#!/usr/bin/env python3
"""Run the EG-10 Eurographics 2027 submission-readiness preflight."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "eg2027-eg10-submission-readiness-v1"
PAPER = Path("paper/neurips_ra_instructscene/main.tex")
BIB = Path("paper/neurips_ra_instructscene/references.bib")
PDF = Path("paper/neurips_ra_instructscene/main.pdf")
OFFICIAL_TEMPLATE = Path("paper/eurographics2027_template/EGauthorGuidelines-conf-sub.tex")
EG09_CHECKER = Path("scripts/check_eg09_paper_claim_consistency.py")
EG10_MANIFEST = Path("manifests/eurographics2027/eg10_submission_readiness_manifest.json")
STALE_PDF_SHA256 = "3234c4a2fd39ec2db593e7fa48a3c40391c3d39d0b1d77133600b256e56e8e49"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cited_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for match in re.finditer(r"\\cite\w*\{([^}]+)\}", tex):
        keys.update(key.strip() for key in match.group(1).split(",") if key.strip())
    return keys


def bibliography_keys(bib: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib))


def labels_and_refs(tex: str) -> tuple[set[str], set[str]]:
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    refs = set(re.findall(r"\\(?:auto|page|eq)?ref\{([^}]+)\}", tex))
    return labels, refs


def load_eg09_checker(repo_root: Path) -> Any:
    script = repo_root / EG09_CHECKER
    spec = importlib.util.spec_from_file_location("eg09_checker_for_eg10", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def blocker(code: str, owner: str, action: str) -> dict[str, str]:
    return {"code": code, "owner": owner, "action": action}


def validate(repo_root: Path) -> dict[str, Any]:
    paper_path = repo_root / PAPER
    bib_path = repo_root / BIB
    pdf_path = repo_root / PDF
    required = (paper_path, bib_path, pdf_path, repo_root / EG09_CHECKER, repo_root / EG10_MANIFEST)
    missing = [path.as_posix() for path in required if not path.is_file()]
    if missing:
        return {
            "schema": SCHEMA,
            "status": "EG10_PRECHECK_BLOCKED",
            "errors": [f"missing required file: {path}" for path in missing],
            "hard_blockers": [],
        }

    tex = paper_path.read_text(encoding="utf-8")
    bib = bib_path.read_text(encoding="utf-8")
    citations = cited_keys(tex)
    bib_keys = bibliography_keys(bib)
    labels, refs = labels_and_refs(tex)
    internal_patterns = (
        "BJTUworldmodellab",
        "C:\\Users",
        "eg07_final_delivery",
        "results/independent_eval",
        "experiment_archive",
        "github.com/",
    )

    eg09 = load_eg09_checker(repo_root).validate(repo_root)
    eg10_manifest = json.loads((repo_root / EG10_MANIFEST).read_text(encoding="utf-8"))
    manifest_inputs = eg10_manifest["inputs"]
    checks: dict[str, Any] = {
        "eg09_claim_freeze_pass": not eg09["errors"],
        "eg10_manifest_schema_matches": eg10_manifest.get("schema") == SCHEMA,
        "eg10_manifest_input_hashes_match": (
            manifest_inputs["paper"]["sha256"] == sha256(paper_path)
            and manifest_inputs["bibliography"]["sha256"] == sha256(bib_path)
            and manifest_inputs["stale_pdf"]["sha256"] == sha256(pdf_path)
        ),
        "all_citations_resolve": citations <= bib_keys,
        "uncited_bibliography_entries": sorted(bib_keys - citations),
        "missing_bibliography_entries": sorted(citations - bib_keys),
        "all_references_resolve": refs <= labels,
        "missing_labels": sorted(refs - labels),
        "duplicate_labels": sorted(
            label for label in labels if len(re.findall(rf"\\label\{{{re.escape(label)}\}}", tex)) > 1
        ),
        "internal_identity_strings_absent": not any(pattern in tex for pattern in internal_patterns),
        "checklist_placeholder_absent": "Checklist Placeholder" not in tex,
        "appendix_removed_from_main": "\\appendix" not in tex,
        "current_documentclass": re.search(r"\\documentclass(?:\[[^]]*\])?\{([^}]+)\}", tex).group(1),
        "uses_egpubl_class": "\\documentclass{egpubl}" in tex,
        "uses_conference_submission_mode": "\\ConferenceSubmission" in tex,
        "uses_eg_bibliography_style": "\\bibliographystyle{eg-alpha-doi}" in tex,
        "has_ccs_categories": "\\ccsdesc" in tex and "\\printccsdesc" in tex,
        "uses_submission_id": "SUBMISSION ID" in tex,
        "has_ai_disclosure": bool(
            re.search(
                r"\\(?:section\*?|paragraph)\{(?:Generative )?AI (?:Use )?Disclosure\}",
                tex,
                re.IGNORECASE,
            )
        ),
        "has_result_figure": "\\includegraphics" in tex,
        "official_2027_template_present": (repo_root / OFFICIAL_TEMPLATE).is_file(),
        "tracked_pdf_is_stale_pre_eg09": sha256(pdf_path) == STALE_PDF_SHA256,
        "word_count_approx": len(re.findall(r"\b[\w'-]+\b", tex)),
        "figure_environments": len(re.findall(r"\\begin\{figure\}", tex)),
        "table_environments": len(re.findall(r"\\begin\{table\}", tex)),
    }

    hard_blockers: list[dict[str, str]] = []
    visibility = eg10_manifest.get("repository_visibility_observed", {}).get("visibility")
    if visibility == "PUBLIC":
        hard_blockers.append(
            blocker(
                "PUBLIC_REPOSITORY_ANONYMITY_RISK",
                "authors",
                "Before submission, make the identified repository private or move submission artifacts to an identity-safe anonymous repository and audit public traces.",
            )
        )
    if not checks["official_2027_template_present"]:
        hard_blockers.append(
            blocker(
                "OFFICIAL_TEMPLATE_LOGIN_REQUIRED",
                "author",
                "Download the EG2027 package from SRMv2 and place it under paper/eurographics2027_template/.",
            )
        )
    if not checks["uses_egpubl_class"] or not checks["uses_conference_submission_mode"]:
        hard_blockers.append(
            blocker("SOURCE_NOT_MIGRATED", "paper", "Migrate the source to EGauthorGuidelines-conf-sub.tex.")
        )
    if not checks["uses_eg_bibliography_style"]:
        hard_blockers.append(
            blocker("BIBLIOGRAPHY_STYLE_MISMATCH", "paper", "Use the bibliography setup bundled with the EG2027 template.")
        )
    if not checks["has_ccs_categories"]:
        hard_blockers.append(
            blocker("CCS_CATEGORIES_MISSING", "authors", "Choose and add verified ACM CCS 2012 categories.")
        )
    if not checks["uses_submission_id"]:
        hard_blockers.append(
            blocker("SUBMISSION_ID_PENDING", "authors", "Insert the SRMv2 submission ID after abstract registration.")
        )
    if checks["tracked_pdf_is_stale_pre_eg09"]:
        hard_blockers.append(
            blocker("PDF_STALE", "build", "Compile and visually inspect a new PDF from the migrated EG2027 source.")
        )
    if not checks["has_ai_disclosure"]:
        hard_blockers.append(
            blocker(
                "AI_DISCLOSURE_AUTHOR_INPUT_NEEDED",
                "authors",
                "Confirm exact tools and uses, then add the disclosure required by Eurographics policy.",
            )
        )

    scientific_risks = [
        {
            "code": "QUALITATIVE_FORMAL_EVIDENCE_MISSING",
            "evidence": "The manuscript has one pipeline schematic and no rendered formal before/after result figure.",
        },
        {
            "code": "GENERIC_COMPARATOR_INCONCLUSIVE",
            "evidence": "Main accuracy 0.6399 is below the generic optimizer point estimate 0.6411; paired CI includes zero.",
        },
        {
            "code": "ORIGINAL_BASELINE_INCONCLUSIVE",
            "evidence": "The +0.50 pp point gain over the original baseline has a paired CI that includes zero.",
        },
        {
            "code": "SINGLE_GENERATOR_SEED_AND_PIPELINE",
            "evidence": "The formal evaluation uses one generated layout per validation scene at generator seed 0 on InstructScene.",
        },
        {
            "code": "NO_HUMAN_VISUAL_STUDY",
            "evidence": "Aggregate collision counts do not establish perceived layout quality or functional plausibility.",
        },
    ]

    integrity_errors = [
        name
        for name in (
            "eg09_claim_freeze_pass",
            "eg10_manifest_schema_matches",
            "eg10_manifest_input_hashes_match",
            "all_citations_resolve",
            "all_references_resolve",
            "internal_identity_strings_absent",
            "checklist_placeholder_absent",
            "appendix_removed_from_main",
        )
        if not checks[name]
    ]
    if checks["duplicate_labels"]:
        integrity_errors.append("duplicate_labels")

    return {
        "schema": SCHEMA,
        "status": "EG10_READY" if not hard_blockers and not integrity_errors else "EG10_PRECHECK_BLOCKED",
        "integrity_status": "PASS" if not integrity_errors else "FAIL",
        "errors": integrity_errors,
        "hard_blockers": hard_blockers,
        "scientific_review_risks": scientific_risks,
        "checks": checks,
        "inputs": {
            "paper": {"path": PAPER.as_posix(), "sha256": sha256(paper_path)},
            "bibliography": {"path": BIB.as_posix(), "sha256": sha256(bib_path)},
            "pdf": {"path": PDF.as_posix(), "sha256": sha256(pdf_path)},
        },
        "official_template_path_expected": OFFICIAL_TEMPLATE.as_posix(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="exit nonzero while blocked")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.repo_root.resolve()
    payload = validate(root)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = args.output if args.output.is_absolute() else root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if args.strict and payload["status"] != "EG10_READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
