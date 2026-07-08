import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables" / "strong_baseline_feasibility.csv"
DOC = ROOT / "docs" / "relation_aware_strong_baseline_status.md"


ROWS = [
    {
        "method": "InstructScene",
        "role": "direct same-protocol baseline",
        "code_status": "available and executed",
        "data_status": "same official validation prompts/checkpoints",
        "blocking_issue": "",
        "fair_comparison_status": "fair",
        "paper_claim": "Use as primary baseline: our repair improves explicit relation satisfaction over original InstructScene outputs under the same split.",
    },
    {
        "method": "Direct y-fixed repair",
        "role": "strong internal relation-repair baseline",
        "code_status": "available and executed",
        "data_status": "same outputs and same FCL mesh evaluator",
        "blocking_issue": "Higher relation gain can come with larger movement and small mesh-pair increases in some rooms.",
        "fair_comparison_status": "fair internal ablation",
        "paper_claim": "Use as ablation showing why floor-prior and collision gating are needed.",
    },
    {
        "method": "Collision-gated direct/floor-prior repair",
        "role": "verifier-selection baseline/variant",
        "code_status": "available and executed",
        "data_status": "same output JSON and same FCL mesh evaluator",
        "blocking_issue": "Post-hoc verifier fallback should be described explicitly, not hidden as pure generation.",
        "fair_comparison_status": "fair internal variant",
        "paper_claim": "Use for mesh-validity claim: relation gains remain positive while mesh collision pair rate does not increase.",
    },
    {
        "method": "ReSpace",
        "role": "close external text-driven 3D scene baseline",
        "code_status": "repo cloned on remote; no runnable same-split result",
        "data_status": "official SSR-3DFRONT protocol differs from InstructScene validation prompts",
        "blocking_issue": "Requires separate environment, SSR-3DFRONT assets/cache, vLLM, and HuggingFace access for released model; remote has no HF token and low /root/autodl-tmp free space.",
        "fair_comparison_status": "not fair yet",
        "paper_claim": "Discuss as close related work only unless a shared protocol is built and executed.",
    },
    {
        "method": "SDGScenes",
        "role": "close semantic-dependency/constraint baseline",
        "code_status": "no verified runnable same-split implementation on this server",
        "data_status": "reported protocol differs and no same InstructScene split numbers are available locally",
        "blocking_issue": "No shared-protocol reproduction or official same-split result.",
        "fair_comparison_status": "not fair yet",
        "paper_claim": "Discuss as close related work; do not claim superiority.",
    },
    {
        "method": "CommonScenes",
        "role": "scene-graph diffusion baseline family",
        "code_status": "repo cloned on remote; not executed as same text-instruction baseline",
        "data_status": "requires SG-FRONT/CommonScenes preprocessing/checkpoints; not same prompt-conditioned InstructScene protocol",
        "blocking_issue": "Different input modality and benchmark target; full setup requires additional processed data/checkpoints.",
        "fair_comparison_status": "not same-protocol",
        "paper_claim": "Cite as related scene-graph generation family, not as direct text-instruction baseline.",
    },
]


def write_csv():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(ROWS)


def write_doc():
    lines = [
        "# Strong Baseline Feasibility Status",
        "",
        "This note separates fair same-protocol baselines from close related systems that cannot yet be used for an outperforming claim.",
        "",
        "| Method | Status | Fairness | Paper use |",
        "|---|---|---|---|",
    ]
    for row in ROWS:
        status = row["code_status"]
        if row["blocking_issue"]:
            status += f"; blocker: {row['blocking_issue']}"
        lines.append(f"| {row['method']} | {status} | {row['fair_comparison_status']} | {row['paper_claim']} |")
    lines.extend([
        "",
        "## Bottom Line",
        "",
        "- The current fair baseline is InstructScene under the same official validation prompts and checkpoints.",
        "- Direct y-fixed repair and collision-gated repair are valid internal baselines/ablations.",
        "- ReSpace, SDGScenes, and CommonScenes should be treated as close related work until a shared protocol is actually executed.",
        "- Do not write that this method outperforms ReSpace or SDGScenes based on the current evidence.",
    ])
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    write_csv()
    write_doc()
    print(OUT)
    print(DOC)
    print(f"rows={len(ROWS)}")


if __name__ == "__main__":
    main()
