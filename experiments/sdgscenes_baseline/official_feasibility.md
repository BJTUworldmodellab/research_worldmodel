# Official SDGScenes Feasibility

Updated: 2026-07-11 Asia/Shanghai

## Current status

Official SDGScenes reproduction is not claimed at this time.

First-pass searches did not locate an official repository or an immediately runnable official release. Therefore, SDGScenes must not be placed into the same direct numerical ranking table as our InstructScene-protocol results.

## Cloud audit evidence

Cloud audit path:

`/root/autodl-tmp/rg-sota-cloud/experiments/sdgscenes_defensive_baseline`

GitHub repository search artifacts:

- `raw_search/github_repos_sdgscenes.json`
- `raw_search/github_repos_sdg_scenes_3d.json`
- `raw_search/github_repos_semantic_dependency_graph_3d_scene.json`
- `reports/github_search_summary.txt`
- `reports/raw_search_sha256.txt`
- `reports/search_audit.tsv`

Observed first-pass GitHub API repository counts:

| Query | Total count |
|---|---:|
| `SDGScenes` | 0 |
| `"SDG Scenes" 3D` | 0 |
| `"semantic dependency graph" 3D scene` | 0 |

## Interpretation

This does not prove that SDGScenes has no code anywhere. It means no no-friction official repository was located in the current audit pass. The correct experimental handling is:

- no official reproduction claim;
- no “outperform SDGScenes” claim;
- no direct ranking-table comparison;
- use SDGScenes as a related-system / reported-results context if official paper numbers are found;
- optionally implement a clearly labeled `SDGScenes-inspired strong baseline`.

## Upgrade path to official reproduction

Move SDGScenes from “protocol reference” to “direct comparison candidate” only if:

1. an official repository or author-confirmed code is found;
2. license permits local research use;
3. dependencies install without private assets or undocumented manual steps;
4. data split and input protocol can be aligned with our InstructScene validation setup;
5. output representation can be converted to the same evaluator;
6. a bedroom smoke test succeeds.

