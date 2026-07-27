# SDGScenes Defensive Baseline Smoke Report

Generated: 2026-07-20T08:25:24Z UTC

## Status

This is a **non-official SDGScenes-inspired constrained-optimization baseline**. It uses the same archived InstructScene validation layouts and parsed relation targets available in this repository, then applies a deterministic final-layout optimizer with:

- explicit horizontal relation penalties,
- movement regularization,
- footprint-overlap penalty,
- out-of-bounds center penalty.

It is intentionally not reported as an official SDGScenes reproduction. SDGScenes should remain in the SOTA/protocol comparison table unless official code, assets, prompts, split, output representation, and evaluator can be aligned.

## Protocol boundary

- Input layouts: `layout_boxes` from `relation_aware_parsed_p2_close0.75_far1.6_eval.json`.
- Target relations: `repair_target_relations` from the same archived JSON.
- Optimized variables: object x/z translations only; size, class, y translation, and yaw are preserved.
- Unsupported vertical relations (`above`/`below`) are passed through from the archived baseline relation set and are not optimized.
- Collision check here is lightweight AABB footprint overlap, not the paper's FCL mesh evaluator.
- Therefore the numeric rows below are a defensive internal optimizer baseline, not a direct SOTA ranking against SDGScenes.

## Same-protocol archived references + smoke optimizer

| room | InstructScene baseline archived | direct repair archived | floor-prior archived | collision-gated archived | optimizer before simple | optimizer after simple | optimizer gain simple | move/scene | AABB overlap area Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bedroom | 0.7388 | 0.8735 | 0.8408 | 0.8449 | 0.5885 | 0.8765 | 0.2881 | 0.9224 | -1.6298 |
| livingroom | 0.5510 | 0.7415 | 0.6939 | 0.6871 | 0.3319 | 0.7686 | 0.4367 | 0.9685 | -2.8688 |
| diningroom | 0.5948 | 0.7844 | 0.7286 | 0.7212 | 0.3305 | 0.7288 | 0.3983 | 0.9328 | -2.3227 |

## Smoke optimizer details

| room | scenes | targets | horizontal targets | before horiz acc | after horiz acc | horiz gain | edits | move/edit | OOB Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bedroom | 162 | 243 | 209 | 0.5407 | 0.8756 | 0.3349 | 72 | 2.0754 | 0 |
| livingroom | 192 | 229 | 209 | 0.2967 | 0.7751 | 0.4785 | 101 | 1.8411 | 0 |
| diningroom | 177 | 236 | 223 | 0.2960 | 0.7175 | 0.4215 | 120 | 1.3759 | 0 |

## Recommended paper wording

Use this row as: "SDGScenes-inspired constrained optimizer (ours-run defensive smoke)". Do not call it SDGScenes. The safe claim is:

> Under the same archived InstructScene final-layout protocol, a generic constrained optimizer improves explicit horizontal relation satisfaction, but it lacks SDGScenes' SDG/VLM commonsense modules and uses a lightweight overlap proxy. We therefore keep official SDGScenes as a non-direct SOTA reference and avoid ranking our method against it.

## Artifact index

- Summary CSV: `experiments/sdgscenes_baseline/results/sdgscenes_inspired_smoke_20260720/summary.csv`
- Per-scene CSV: `experiments/sdgscenes_baseline/results/sdgscenes_inspired_smoke_20260720/per_scene.csv`
- Optimized layouts JSON: `experiments/sdgscenes_baseline/results/sdgscenes_inspired_smoke_20260720/optimized_layouts.json`
- Run metadata JSON: `experiments/sdgscenes_baseline/results/sdgscenes_inspired_smoke_20260720/run_metadata.json`

## Run metadata

```json
{
  "timestamp_utc": "2026-07-20T08:25:24Z",
  "cwd": "/root/autodl-tmp/rg-sota-cloud/repos/research_worldmodel",
  "python": "3.10.8 (main, Nov 24 2022, 14:13:03) [GCC 11.2.0]",
  "platform": "Linux-5.15.0-140-generic-x86_64-with-glibc2.35",
  "argv": [
    "experiments/sdgscenes_baseline/scripts/run_sdgscenes_defensive_smoke.py"
  ],
  "git_commit": "0e809f01775499b423c62c2666b25d023f55ba31",
  "git_branch": "exp/sdgscenes-defensive-baseline-20260711",
  "nvidia_smi": "NVIDIA H800 PCIe, 81559 MiB, 570.124.04",
  "torch_cuda": {
    "torch": "2.11.0+cu128",
    "cuda_available": true,
    "device_count": 1,
    "device_0": "NVIDIA H800 PCIe",
    "capability_0": [
      9,
      0
    ]
  },
  "input_files": {
    "bedroom": {
      "path": "experiment_archive/relation_aware_instructscene_20260530/local_results/full/bedroom/relation_aware_parsed_p2_close0.75_far1.6_eval.json",
      "sha256": "df9951e81d4eff4940af7f20fb7670ed0744e21d3448cc8c6f12b564b7a67154"
    },
    "livingroom": {
      "path": "experiment_archive/relation_aware_instructscene_20260530/local_results/full/livingroom/relation_aware_parsed_p2_close0.75_far1.6_eval.json",
      "sha256": "6471b562934c552f067576dcf0c1c5bedd38aed58aa3f3ebbf692577bdf3faad"
    },
    "diningroom": {
      "path": "experiment_archive/relation_aware_instructscene_20260530/local_results/full/diningroom/relation_aware_parsed_p2_close0.75_far1.6_eval.json",
      "sha256": "0e18bef82bef9eba3fa568a12ccbd30ead609edd7a8b42ceb8eab14108c81e3c"
    }
  },
  "source_note": "Non-official SDGScenes-inspired optimizer; no official SDGScenes reproduction claim."
}
```
