# Generative-AI disclosure — author confirmation required

State: `AI_DISCLOSURE_AUTHOR_INPUT_NEEDED`

Eurographics publication guidance requires transparent disclosure of generative-AI use. The exact tools, model/version labels, purposes, and human-review statement must be confirmed by the authors; they must not be inferred from terminal history alone.

## Tool inventory to confirm

| Candidate tool | Candidate purpose | Include? | Exact product/model/version |
|---|---|---|---|
| OpenAI Codex | code inspection, experiment orchestration, reproducibility scripts, LaTeX/document drafting and review | `PENDING` | `PENDING` |
| Claude Code | cloud environment setup, debugging, code assistance | `PENDING` | `PENDING` |
| DeepSeek V4 Pro accessed through Claude Code/provider endpoint | code/environment assistance | `PENDING` | `PENDING` |
| Any additional generative-AI tool | `PENDING` | `PENDING` | `PENDING` |

## Author declarations to confirm

- `[ ]` All AI-assisted code was reviewed and tested by an author.
- `[ ]` All AI-assisted prose was fact-checked, edited, and approved by an author.
- `[ ]` No AI system is listed as an author.
- `[ ]` The authors retain responsibility for results, citations, claims, and submission compliance.
- `[ ]` The disclosure lists every materially used tool and purpose.

## Draft wording — do not insert until confirmed

> The authors used [exact tools/models and versions] for [confirmed purposes]. All AI-assisted code and text were reviewed, tested or fact-checked, and edited by the authors, who take full responsibility for the submitted work.

If venue guidance requires a dedicated section rather than acknowledgments, move the confirmed wording accordingly. Do not include account identifiers, API endpoints, keys, prompts containing private data, or cloud login details.
