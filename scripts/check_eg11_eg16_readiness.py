#!/usr/bin/env python3
"""Generate a machine-readable EG11--EG16 readiness report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "results" / "independent_eval" / "eg2027" / "eg11_eg16_readiness_20260825",
    )
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    paper = root / "paper" / "eurographics2027_submission"
    tex = paper / "EGauthorGuidelines-conf-sub.tex"
    bib = paper / "references.bib"
    figure = paper / "figures" / "eg11_formal_qualitative.pdf"
    figure_manifest = paper / "figures" / "eg11_formal_qualitative_selection.json"
    pdf = paper / "build" / "EGauthorGuidelines-conf-sub.pdf"
    source_files = [path for path in (tex, bib, figure_manifest) if path.is_file()]
    source_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in source_files)
    identity_rules = {
        "windows_user_path": r"[A-Za-z]:[\\/]Users[\\/]",
        "root_path": r"/root/",
        "repository_identity": r"(?:BJTUworldmodellab|research_worldmodel|jomify|sachi25250102)",
        "credential_pattern": r"(?:github_pat_|sk-(?:proj-)?[A-Za-z0-9_-]{16,}|BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY)",
    }
    anonymity_findings = [name for name, pattern in identity_rules.items() if re.search(pattern, source_text, re.I)]
    source_requirements = {
        "conference_submission": "\\ConferenceSubmission" in source_text,
        "anonymous_author_placeholder": "\\author[SUBMISSION ID]{SUBMISSION ID}" in source_text,
        "ccs": source_text.count("\\ccsdesc") >= 3,
        "keywords": "\\begin{keywords}" in source_text,
        "formal_figure": figure.is_file() and figure_manifest.is_file(),
        "relscene_citation": "ye2024relscene" in source_text,
    }
    dependencies = [path for path in (tex, bib, figure) if path.is_file()]
    pdf_fresh = pdf.is_file() and all(pdf.stat().st_mtime >= path.stat().st_mtime for path in dependencies)
    eg11_pass = all(source_requirements.values()) and not anonymity_findings and pdf_fresh

    citation_report = root / "docs" / "eurographics2027" / "eg12_related_work_citation_audit_20260825.md"
    eg12_pass = citation_report.is_file() and "EG12_CITATIONS_VERIFIED" in citation_report.read_text(encoding="utf-8")

    build_result_path = root / "artifacts" / "eurographics2027" / "eg13_build_result.json"
    build_result = json.loads(build_result_path.read_text(encoding="utf-8")) if build_result_path.is_file() else {}
    supplement = root / build_result.get("zip", "missing")
    eg13_pass = (
        build_result.get("status") == "PASS"
        and build_result.get("anonymity_findings") == []
        and supplement.is_file()
        and sha256(supplement) == build_result.get("zip_sha256")
    )

    human_receipts = sorted((root / "docs" / "eurographics2027").glob("eg14_uninvolved_human_review_receipt_*.json"))
    accepted_human_receipt = False
    accepted_human_receipts = []
    current_pdf_human_receipts = []
    current_pdf_sha256 = sha256(pdf) if pdf.is_file() else None
    for receipt in human_receipts:
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        if payload.get("uninvolved_confirmed") is True and payload.get("decision") == "ACCEPT":
            accepted_human_receipt = True
            accepted_human_receipts.append(receipt.relative_to(root).as_posix())
            if payload.get("reviewed_pdf", {}).get("sha256") == current_pdf_sha256:
                current_pdf_human_receipts.append(receipt.relative_to(root).as_posix())
    eg14_current_pdf_pass = bool(current_pdf_human_receipts)
    eg14_pass = eg14_current_pdf_pass and eg11_pass

    deferral_path = root / "submission" / "eurographics2027" / "eg15_eg16_deferred_20260901.md"
    deferral_text = deferral_path.read_text(encoding="utf-8") if deferral_path.is_file() else ""
    submission_deferred = "ARTICLE_DEVELOPMENT_ONLY" in deferral_text

    metadata_path = root / "submission" / "eurographics2027" / "eg15_metadata_draft_20260825.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else {}
    eg15_pass = (
        metadata.get("state") == "EG15_METADATA_FROZEN"
        and bool(metadata.get("authors"))
        and bool(metadata.get("affiliations"))
        and bool(metadata.get("corresponding_author"))
        and bool(metadata.get("ai_use_disclosure"))
        and eg11_pass
        and eg14_pass
    )

    registration_path = root / "submission" / "eurographics2027" / "eg16_srmv2_abstract_registration_20260825.md"
    registration_text = registration_path.read_text(encoding="utf-8") if registration_path.is_file() else ""
    id_match = re.search(r"Submission/paper ID:\s*`([^`]+)`", registration_text)
    submission_id = id_match.group(1) if id_match else None
    eg16_pass = bool(submission_id and submission_id != "PENDING" and eg15_pass)

    tasks = {
        "EG11": {
            "state": "EG11_FRESH_PDF_PASS" if eg11_pass else "EG11_COMPILE_BLOCKED_TOOLCHAIN",
            "pass": eg11_pass,
            "source_requirements": source_requirements,
            "source_anonymity_findings": anonymity_findings,
            "pdf": {"exists": pdf.is_file(), "fresh": pdf_fresh, "sha256": sha256(pdf) if pdf.is_file() else None},
        },
        "EG12": {"state": "EG12_CITATIONS_VERIFIED" if eg12_pass else "EG12_REVIEW_REQUIRED", "pass": eg12_pass},
        "EG13": {"state": "EG13_ANONYMOUS_REPRO_PASS" if eg13_pass else "EG13_REPRO_FAILED", "pass": eg13_pass, "build_result": build_result},
        "EG14": {
            "state": "EG14_DONE" if eg14_pass else ("EG14_DONE_FOR_REVIEWED_SNAPSHOT_CURRENT_DELTA_REVIEW_DEFERRED" if accepted_human_receipt and eg11_pass else ("EG14_BLOCKED_HUMAN_REVIEW" if eg11_pass else "EG14_BLOCKED_HUMAN_REVIEW_AND_FRESH_PDF")),
            "pass": eg14_pass,
            "accepted_human_receipt": accepted_human_receipt,
            "accepted_human_receipts": accepted_human_receipts,
            "current_pdf_human_receipts": current_pdf_human_receipts,
        },
        "EG15": {"state": "EG15_METADATA_FROZEN" if eg15_pass else ("EG15_DEFERRED_BY_AUTHOR" if submission_deferred else "EG15_AUTHOR_CONFIRMATION_BLOCKED"), "pass": eg15_pass, "blocking_fields": metadata.get("blocking_fields", [])},
        "EG16": {"state": "EG16_ABSTRACT_REGISTERED" if eg16_pass else ("EG16_DEFERRED_BY_AUTHOR" if submission_deferred else "EG16_REGISTRATION_BLOCKED_INPUTS"), "pass": eg16_pass, "submission_id": submission_id},
    }
    external_actions_required = []
    if not eg14_pass and not submission_deferred:
        external_actions_required.append("uninvolved human fresh-PDF and supplement review")
    if not eg15_pass and not submission_deferred:
        external_actions_required.append("author metadata and AI-disclosure confirmation")
    if not eg16_pass and not submission_deferred:
        external_actions_required.append("authorized SRMv2 abstract registration and submission-ID receipt")
    if submission_deferred:
        external_actions_required.append("none during article development; resume submission actions only on explicit author request")
    else:
        external_actions_required.append("public-repository anonymity decision and trace audit")

    payload = {
        "schema": "eg2027-eg11-eg16-readiness-v1",
        "created_date": "2026-08-25",
        "overall": "EG11_EG16_COMPLETE" if all(task["pass"] for task in tasks.values()) else ("ARTICLE_DEVELOPMENT_ACTIVE_SUBMISSION_DEFERRED" if submission_deferred and all(tasks[key]["pass"] for key in ("EG11", "EG12", "EG13")) else "IN_PROGRESS_EXTERNAL_INPUT_REQUIRED"),
        "tasks": tasks,
        "external_actions_required": external_actions_required,
    }
    (output / "status.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# EG11–EG16 readiness", "", f"Overall: **{payload['overall']}**", "", "| Task | State |", "|---|---|"]
    lines.extend(f"| {task} | `{data['state']}` |" for task, data in tasks.items())
    lines.extend(["", "## External actions required", "", *[f"- {item}" for item in payload["external_actions_required"]]])
    (output / "status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"overall": payload["overall"], "tasks": {key: value["state"] for key, value in tasks.items()}, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
