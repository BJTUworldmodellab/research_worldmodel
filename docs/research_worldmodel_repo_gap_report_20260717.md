# BJTUworldmodellab/research_worldmodel Difference Audit and Experiment Report

Date: 2026-07-17

## 1. What Was Compared

I compared three places:

1. GitHub code repository: `BJTUworldmodellab/research_worldmodel`
   - Public repository.
   - Default branch: `master`.
   - Last push observed through GitHub API: 2026-07-14.
   - Repository size reported by GitHub API: about 39 MB.
2. Local workspace: `C:\Users\14754\Desktop\research_worldmodel`
3. Remote AutoDL workspace:
   - Code and small results: `/root/RelationAwareInstructScene`
   - Large data/checkpoints/results: `/root/autodl-tmp/RelationAwareInstructScene`

The GitHub code repository currently contains the early Relation-Aware InstructScene experiment package, but it does not yet contain the later CommonScenes comparison package or the AutoDL reproduction/setup scripts.

## 2. High-Level Difference

In plain language:

- The GitHub repository already has the original method evidence: InstructScene relation repair, floor-prior repair, mesh/collision sanity checks, visual figures, and a paper draft.
- The local workspace has newer experiment materials: CommonScenes comparison, no-official-search results, parameter ablation, bootstrap uncertainty, qualitative panels, and remote setup scripts.
- The remote AutoDL machine has the runnable full environment: datasets, checkpoints, model caches, CommonScenes output tensors, rendered meshes, and logs.
- The separate data repository `bghind/experiment-data` already stores an archived small-data package from AutoDL, including CommonScenes comparison summaries and original InstructScene evidence.

So the main code repository is missing the newest CommonScenes experiment layer and the scripts needed to reproduce it cleanly.

## 3. GitHub Repository Current Structure

Observed top-level directories/files in `BJTUworldmodellab/research_worldmodel`:

```text
docs/
experiment_archive/
paper/
results/
scripts/
visual/
.omx/
.playwright-mcp/
cinematic-3d-showcase.png
real-mesh-showcase.png
real-mesh-showcase-v2.png
relation_aware_complete_report.png
```

Important contents already present:

- `docs/`: original Relation-Aware InstructScene reports and paper planning notes.
- `results/`: original evaluation JSON/TXT files, floor-prior remote results, tables, and logs.
- `visual/`: original HTML reports, qualitative SVGs, floor-prior showcase PNGs, and paper figures.
- `experiment_archive/relation_aware_instructscene_20260530/`: archived original experiment package.
- `paper/neurips_ra_instructscene/`: paper draft files.

Important missing directory:

```text
server_setup/
```

The GitHub repo does not currently have the AutoDL setup scripts or the CommonScenes reproduction scripts.

## 4. Local Workspace Extra Content Not Reflected In GitHub

The local workspace contains all of the GitHub-level original files plus newer materials.

Most important local-only additions:

```text
docs/commonscenes_experiment_pack_20260713/
docs/commonscenes_generic_no_official_search/
docs/commonscenes_environment_audit_20260710.md
docs/commonscenes_reproduction_comparison_20260713.md
server_setup/
server_setup/commonscenes_experiments/
visual/commonscenes_paper_panels/
scripts/compute_commonscenes_bootstrap_ci.py
scripts/compare_common_layout_metrics.py
scripts/evaluate_semantic_relation_respace.py
```

The CommonScenes package currently has 55 files locally, about 0.99 MB in total for the compact report/data/scripts/panel package checked here. This excludes remote large tensors, model checkpoints, datasets, and rendered mesh folders.

## 5. Remote AutoDL Extra Content

Remote code/small-result workspace:

```text
/root/RelationAwareInstructScene
```

Key contents:

```text
repos/InstructScene
repos/respace
repos/commonscenes
results/commonscenes_repair_compare_20260713
results/commonscenes_ours_repair_compare_epoch195_bedroom
results/commonscenes_ours_gated_t3_compare_epoch195_bedroom
logs/commonscenes
logs/strong_baseline_a100_compare
scripts/
server_setup/
docs/
```

Remote large data/checkpoint/result workspace:

```text
/root/autodl-tmp/RelationAwareInstructScene
```

Important retained directories:

```text
raw_data/3D-FRONT                              55G
hf_cache                                      26G
commonscenes_assets                           15G
commonscenes_models                           13G
results_archive_rootfs                        16G
results_generic_repair                        14G
datasets/InstructScene                        6.7G
commonscenes_FRONT                            6.1G
instructscene_out                             3.9G
respace_ckpts                                 2.9G
```

These are not suitable for normal GitHub because they are too large. They should stay on AutoDL or be moved to a data host / Git LFS / release assets only if necessary.

Current remote disk status from the audit:

```text
/root/autodl-tmp: 200G total, 155G used, 46G available, 78%
/root:          30G total, 15G used, 16G available, 48%
```

## 6. Data Already Uploaded Elsewhere

The separate data repository was previously populated:

```text
bghind/experiment-data
branch: master
commit: 6649dd46583ef6e3ad71a80b222a37966792abe8
```

It contains:

```text
experiment_archive/remote_autodl_20260714/
experiment_archive/remote_autodl_20260714/commonscenes_comparison/
```

This is the right place for compact experiment data and logs. The code repository should point to this data archive instead of duplicating everything.

## 7. What Should Be Uploaded To BJTUworldmodellab/research_worldmodel

Upload these to the code repository:

```text
docs/commonscenes_experiment_pack_20260713/
docs/commonscenes_generic_no_official_search/
docs/commonscenes_environment_audit_20260710.md
docs/commonscenes_reproduction_comparison_20260713.md
docs/common_layout_comparison_20260710.md
docs/common_layout_comparison_n54_20260710.md
docs/official_strong_baseline_attempt_20260709.md
docs/qwen_open_reproducible_baseline_20260709.md
docs/qwen_respace_addonly_20260710.md
docs/qwen_seq_baseline_partial_20260710.md
docs/respace_a100_unblock_run_20260709.md
docs/semantic_relation_accuracy_n54_20260710.md
docs/strong_baseline_comparison_run_20260708.md
docs/strong_baseline_model_selection_20260710.md
server_setup/
scripts/compare_common_layout_metrics.py
scripts/compute_commonscenes_bootstrap_ci.py
scripts/evaluate_semantic_relation_respace.py
visual/commonscenes_paper_panels/
visual/common_layout_comparison_20260710.html
visual/common_layout_comparison_n54_20260710.html
visual/official_strong_baseline_attempt_20260709.html
visual/qwen_open_reproducible_baseline_20260709.html
visual/qwen_respace_addonly_20260710.html
visual/qwen_seq_baseline_partial_20260710.html
visual/respace_a100_unblock_run_20260709.html
visual/semantic_relation_accuracy_n54_20260710.html
visual/strong_baseline_comparison_run_20260708.html
visual/relation_aware_plain_conclusion_and_next_experiments.html
```

Upload or update this audit report too:

```text
docs/research_worldmodel_repo_gap_report_20260717.md
visual/research_worldmodel_repo_gap_report_20260717.html
```

Do not upload these to the code repository:

```text
raw_data/3D-FRONT
hf_cache
commonscenes_models
instructscene_out/checkpoints
respace_ckpts
*.pth
*.pt
*.safetensors
large GLB/OBJ/PLY render folders
```

Reason: they are too large, mostly reproducible/downloadable, and would make the code repo hard to clone.

## 8. Human-Readable Experiment Report

### What We Tried To Prove

The project is about a simple but important question:

> If a 3D indoor scene generator puts objects in positions that violate spatial relations, can we repair the layout after generation without breaking the scene?

For example: if the instruction says one object should be close to another, far from another, or supported correctly, the generated layout may not satisfy that relation. The method tries to move only the relevant objects, by a controlled amount, and then checks whether the relation improves while the visual/geometry quality remains acceptable.

### Original InstructScene Results

On the original InstructScene setting, the method has strong evidence.

| room | scenes | baseline relation accuracy | repaired relation accuracy | gain |
|---|---:|---:|---:|---:|
| bedroom | 162 | 0.7388 | 0.8735 | +0.1347 |
| livingroom | 192 | 0.5510 | 0.7415 | +0.1905 |
| diningroom | 177 | 0.5948 | 0.7844 | +0.1896 |

Plain interpretation:

- The original generated scenes often miss spatial relations.
- The repair step consistently improves relation satisfaction.
- The improvement is not a tiny one in this setting: it reduces many relation errors.

Mesh-validity-safe variant:

| room | baseline acc | direct repair acc | collision-gated acc | gated gain |
|---|---:|---:|---:|---:|
| bedroom | 0.7388 | 0.8735 | 0.8449 | +0.1061 |
| livingroom | 0.5510 | 0.7415 | 0.6871 | +0.1361 |
| diningroom | 0.5948 | 0.7844 | 0.7212 | +0.1264 |

Plain interpretation:

- If we add a safety gate to avoid repairs that may hurt mesh validity, the gain becomes smaller.
- But the method still improves relation accuracy clearly.
- For paper claims, the collision-gated result is safer and more defensible than the direct repair result.

### CommonScenes Comparison Results

CommonScenes was used as an external comparison setting. Here the goal was not to claim a huge win, but to test whether the repair idea still works under another generator/evaluation pipeline.

Main no-official-search result:

| room | scenes | baseline score | repaired score | gain | collision penalty change |
|---|---:|---:|---:|---:|---|
| bedroom | 162 | 0.981312 | 0.984370 | +0.003058 | 164.012 -> 161.487 |
| livingroom | 52 | 0.970915 | 0.973113 | +0.002198 | 54.798 -> 51.841 |
| diningroom | 69 | 0.968892 | 0.970467 | +0.001575 | 103.200 -> 99.130 |
| library | 56 | 0.958588 | 0.964019 | +0.005431 | 72.028 -> 68.498 |

Plain interpretation:

- CommonScenes baseline is already very strong, so there is less room to improve.
- The repair still gives small but consistent gains across all four room types.
- Collision penalty also goes down, which is a good sign.
- This is supportive evidence, not the main dramatic result.

### Parameter Ablation

We tested different repair thresholds on bedroom:

| threshold | accepted scenes | gain | mean SSIM | mean GLB Chamfer |
|---:|---:|---:|---:|---:|
| 0.8 | 3 | +0.000510 | 0.999597 | 0.113173 |
| 1.2 | 13 | +0.002548 | 0.998696 | 0.119049 |
| 1.5 | 16 | +0.003058 | 0.998014 | 0.128786 |

Plain interpretation:

- Smaller threshold means safer but weaker repair.
- Larger threshold fixes more scenes but changes geometry more.
- `t1.2` is the conservative choice.
- `t1.5` is the best-performing choice in the current table.

### Visual and Geometry Stability

Bootstrap confidence intervals for visual/geometric disturbance:

| room | mean SSIM 95% CI | mean changed-pixel ratio 95% CI | mean GLB Chamfer 95% CI |
|---|---:|---:|---:|
| bedroom | [0.996833, 0.999028] | [0.000930, 0.002780] | [0.117874, 0.140710] |
| livingroom | [0.991977, 0.997086] | [0.002128, 0.005893] | [0.117038, 0.146406] |
| diningroom | [0.997836, 0.999543] | [0.000421, 0.001488] | [0.078378, 0.098258] |
| library | [0.993472, 0.998292] | [0.001199, 0.004583] | [0.109945, 0.156314] |

Plain interpretation:

- Rendered images before and after repair remain very similar on average.
- The repair usually changes the layout locally, not the whole scene.
- There are still high-change cases, so the paper should include failure/risk examples instead of hiding them.

### Overall Claim Strength

Strong claim supported:

> The relation-aware repair method improves spatial relation satisfaction on the original InstructScene setting, and the improvement remains visible under a collision-gated safer variant.

Moderate claim supported:

> On CommonScenes, the same repair idea gives small but consistent improvements under a no-official-search setting, while keeping average visual/geometric disturbance low.

Claim that should be written carefully:

> The method improves full 3D visual quality.

Reason: we have rendered similarity and GLB-level Chamfer, but not a full human study or strict object-level mesh quality audit.

## 9. Remaining Gaps

For a stronger paper, the missing optional experiments are:

1. Object-level Chamfer / IoU audit for changed objects.
2. A small human preference or failure-rate inspection.
3. Export per-scene relation gain rows for CommonScenes so bootstrap can cover relation-score uncertainty, not only visual/geometric disturbance.
4. A clean README that tells users exactly where to get compact data (`bghind/experiment-data`) and where to place large datasets/checkpoints.

## 10. Recommended Repository Structure After Upload

Recommended split:

```text
BJTUworldmodellab/research_worldmodel
  docs/
    original InstructScene reports
    CommonScenes experiment reports
  scripts/
    general analysis scripts
  server_setup/
    AutoDL setup and reproduction scripts
  visual/
    small figures and HTML reports
  paper/
    paper draft
  README.md
    link to bghind/experiment-data

bghind/experiment-data
  experiment_archive/remote_autodl_20260714/
    compact data, summaries, logs, selected panels

AutoDL / object storage
  raw datasets, checkpoints, .pt tensors, rendered meshes
```

