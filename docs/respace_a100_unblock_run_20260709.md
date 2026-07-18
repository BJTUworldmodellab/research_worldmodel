# ReSpace A100 Unblock Run - 2026-07-09

## Result

The A100 environment can now run the ReSpace engineering smoke path end to end when using an explicitly marked smoke-only bypass for the gated Llama command-decomposition model.

This is not an official ReSpace baseline result. It proves that the GPU, SG-LLM checkpoint, vLLM, rebuilt asset cache, dataset split, scene JSON path, asset sampler, and JSON output path are usable.

## Execution Command

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export RESPACE_SKIP_GATED_LLAMA=1
/root/RelationAwareInstructScene/server_setup/run_respace_skip_llama_smoke_after_envfix.sh
```

The script runs:

```bash
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_smoke_bedroom_vllm" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 1 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --icl-k 1 \
  --bon-llm 1
```

## Logs And Artifacts

| Item | Path |
|---|---|
| Final smoke log | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409.log` |
| Final smoke output dir | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409` |
| Summary JSON | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409/summary.json` |
| Seed 1234 output | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409/respace_smoke_bedroom_vllm/1234/0_1234.json` |
| Seed 3456 output | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409/respace_smoke_bedroom_vllm/3456/0_3456.json` |
| Seed 5678 output | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409/respace_smoke_bedroom_vllm/5678/0_5678.json` |

## Key Metrics

| Metric | Value |
|---|---|
| GPU | NVIDIA A100-PCIE-40GB |
| CUDA compute capability | 8.0 |
| vLLM backend | Flash Attention |
| SG-LLM checkpoint | `gradient-spaces/respace-sg-llm-1.5b` |
| Model weights loaded | 2.8875 GB |
| vLLM KV cache | 4.68 GiB |
| vLLM max concurrency, 3000 tokens | 58.47x |
| Asset cache | rebuilt locally, 174 MB |
| Asset embeddings loaded | `(38529, 1152)` |
| Smoke return code | 0 |
| Seeds completed | 1234, 3456, 5678 |
| Success rate | 1.00 (+/- 0.00) |
| Objects per generated scene | 5 |
| Generation time | 5.81 s, 5.57 s, 5.58 s |
| Per-object latency | 1.16 s, 1.11 s, 1.12 s |

## Blockers Fixed

1. Google Drive official asset cache download timed out.
   - Fixed by rebuilding `data/metadata/model_info_3dfuture_assets_embeds.pickle` with the official `src/preprocessing/3d-front/06_compute_embeds.py`.
   - The rebuilt file is 174 MB, matching the README expectation.
2. `.env.baseline` lacked `PTH_STAGE_2_DEDUP`.
   - Fixed on the remote machine by setting it to `/root/autodl-tmp/RelationAwareInstructScene/respace_data/dataset-ssr3dfront/scenes`.
3. The output seed directories were not created before writing.
   - Fixed in the smoke script by pre-creating `1234`, `3456`, and `5678`.
4. Hugging Face gated Llama access still blocks the official command-decomposition model.
   - For smoke only, `src/respace.py` uses `RESPACE_SKIP_GATED_LLAMA=1` to install a dummy command-decomposition pipeline returning five fixed bedroom add commands.

## Git Diff Summary

Remote ReSpace diff:

```text
src/respace.py | 33 +++++++++++++++++++++++++++++----
1 file changed, 29 insertions(+), 4 deletions(-)
```

The diff is smoke-only and should not be merged into official ReSpace code as a research result. It exists only to prove that the rest of the pipeline runs without the gated Llama component.

Local Git diff is unavailable because the local `.git` directory is not a valid Git repository.

## Reproduction Steps

1. SSH to the A100 machine.
2. Activate the `respace` conda environment.
3. Ensure the rebuilt asset cache exists:

```bash
ls -lh /root/RelationAwareInstructScene/repos/respace/data/metadata/model_info_3dfuture_assets_embeds.pickle
```

4. Ensure `.env.baseline` contains:

```bash
PTH_STAGE_2_DEDUP=/root/autodl-tmp/RelationAwareInstructScene/respace_data/dataset-ssr3dfront/scenes
```

5. Run the smoke script:

```bash
/root/RelationAwareInstructScene/server_setup/run_respace_skip_llama_smoke_after_envfix.sh
```

## Still Unreliable

1. This is not an official ReSpace baseline because `meta-llama/Meta-Llama-3.1-8B-Instruct` is still gated and was bypassed.
2. The dummy command decomposition uses fixed commands, so it does not test Llama prompt understanding.
3. Mesh checks reported repeated `string is not a file: ... raw_model.glb` warnings, so geometry-based metrics and rendering remain questionable until the raw 3D-FUTURE asset paths are repaired.
4. The smoke used only one bedroom test scene per seed. It is enough for environment validation, not paper-level comparison.
5. Strong baseline comparison still needs an official run with a valid HF token and repaired mesh assets.

## Upload Recommendation

Upload:

```text
docs/respace_a100_unblock_run_20260709.md
visual/respace_a100_unblock_run_20260709.html
docs/strong_baseline_comparison_run_20260708.md
docs/relation_aware_strong_baseline_status.md
results/tables/multiseed_floorprior_mesh_20260708_134245.csv
results/tables/multiseed_floorprior_gated_20260708_134245.csv
visual/relation_aware_plain_conclusion_and_next_experiments.html
```

Archive separately if desired:

```text
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409.log
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409/summary.json
```

Do not upload model weights, raw 3D-FRONT/3D-FUTURE data, SSH credentials, AutoDL passwords, or Hugging Face tokens.
