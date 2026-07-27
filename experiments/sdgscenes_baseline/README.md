# SDGScenes Defensive Baseline Package

Updated: 2026-07-11 Asia/Shanghai

## Verdict

This package treats SDGScenes as a strong non-direct SOTA reference unless an official, same-protocol reproduction becomes available.

Current feasibility status:

- Official SDGScenes repository: not located in the first-pass web/GitHub audit.
- Official data/split pipeline: not verified.
- Same-protocol numeric comparison: not allowed yet.
- Paper claim policy: do not claim to outperform SDGScenes.

The safe framing is:

> SDGScenes is a stronger, broader user-intent / constraint-system reference. Our method targets a narrower setting: fixed pretrained InstructScene outputs under the existing InstructScene validation protocol, where we repair final-layout relation grounding.

## What this package is for

Use these files to answer reviewer questions such as “why not compare with SDGScenes?” without overclaiming:

- `official_feasibility.md` records what was checked and why official reproduction is not currently claimed.
- `protocol_boundary.md` states the requirements for a fair direct comparison.
- `sota_protocol_comparison.csv` provides the protocol comparison table for the paper.
- `related_work_wording.md` gives claim-safe related-work / experiment-table language.
- `reported_results_context.md` defines how to mention official reported results if a result table is later found.
- `sdgscenes_inspired_baseline_config.yaml` is a transparent config skeleton for a non-official SDGScenes-inspired constrained-optimization baseline.

## Direct-comparison gate

SDGScenes can enter the same numerical ranking table only if all of the following are true:

1. Official code is available or author-approved implementation details are sufficient.
2. Official model/data dependencies can be obtained without hidden manual steps.
3. Input matches our setting: same prompts / relation specs / InstructScene outputs as applicable.
4. Output can be converted to the same object category + translation + size + orientation representation.
5. Same validation split, seeds, thresholds, and mesh evaluator are used.
6. Failure cases are logged with the same policy as our method.

If any item fails, SDGScenes stays in protocol comparison / reported-results context only.

## Cloud paths

Recommended cloud archive location:

`/root/autodl-tmp/rg-sota-cloud/experiments/sdgscenes_defensive_baseline`

Existing environment:

- Python venv: `/root/autodl-tmp/rg-sota-cloud/venvs/relation-sdg`
- Torch CUDA smoke: passed on RTX PRO 6000 Blackwell
- Claude Code wrapper: `/root/autodl-tmp/rg-sota-cloud/scripts/run_claude_deepseek.sh`
- DeepSeek env: configured by user in `/root/autodl-tmp/rg-sota-cloud/.secrets/`

## tmux usage

For download/search tasks:

```bash
tmux new -s sdg_defensive
cd /root/autodl-tmp/rg-sota-cloud
source /etc/network_turbo
```

For Claude Code / DeepSeek tasks, avoid proxy interference:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
/root/autodl-tmp/rg-sota-cloud/scripts/run_claude_deepseek.sh /root/autodl-tmp/rg-sota-cloud/repos
```

