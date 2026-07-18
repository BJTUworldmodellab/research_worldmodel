# Strong Baseline Comparison Run

Updated: 2026-07-08 23:40

## Executive Summary

The A100 machine is suitable for ReSpace: the official vLLM path initializes successfully, uses BF16, selects Flash Attention, loads the ReSpace 1.5B checkpoint, and completes CUDA graph capture. However, the official ReSpace baseline comparison is still not complete or reliable because the run stops on a gated Hugging Face dependency and one required asset cache is missing.

Do not claim that our method outperforms ReSpace yet. The reliable comparison evidence remains the same-protocol InstructScene baseline plus our internal repair/gating variants.

## Claude Code Execution

Requested executor:

`C:\Users\14754\AppData\Roaming\npm\claude.cmd --print "... remote ReSpace strong baseline ..."`

Claude Code result:

Claude Code did not execute the remote experiment because it could not get SSH approval for the remote root login. It returned that SSH access was blocked by approval/permission handling. I therefore continued with the already approved SSH session and recorded all concrete commands and remote logs below.

Reliability note:

Claude Code was invoked as requested, but it did not perform the remote operations. The actual remote experiment execution was performed through the active SSH/tmux session.

## Remote Execution Command

Remote login target:

```bash
ssh -p 36010 root@region-9.autodl.pro
```

Audit script created and executed remotely:

```bash
cd /root/RelationAwareInstructScene
mkdir -p logs/strong_baseline_a100_compare results/strong_baseline_a100_compare server_setup
chmod +x server_setup/run_strong_baseline_a100_audit.sh
tmux new-session -d -s strong-baseline-a100-audit '/root/RelationAwareInstructScene/server_setup/run_strong_baseline_a100_audit.sh'
```

The script runs:

```bash
nvidia-smi --query-gpu=name,memory.total,compute_cap,driver_version --format=csv,noheader
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
python src/pipeline.py \
  --env .env.baseline \
  --pth-output /root/RelationAwareInstructScene/results/strong_baseline_a100_compare/20260708_233225/respace_smoke_bedroom_vllm \
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

## Remote Logs And Artifacts

Primary log:

`/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/audit_20260708_233225.log`

Primary artifact directory:

`/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/20260708_233225`

Summary JSON:

`/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/20260708_233225/summary.json`

Smoke output directory:

`/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/20260708_233225/respace_smoke_bedroom_vllm`

No valid ReSpace scene output was produced because initialization fails before generation.

## Key Metrics

### A100 ReSpace Smoke

| Metric | Value |
|---|---:|
| GPU | NVIDIA A100-PCIE-40GB |
| GPU memory | 40960 MiB |
| compute capability | 8.0 |
| driver | 550.107.02 |
| ReSpace model weights loaded | 2.8875 GB |
| vLLM GPU memory utilization setting | 0.23 |
| vLLM usable memory | 9.06 GiB |
| vLLM KV cache reserved | 4.68 GiB |
| max concurrency at 3000 tokens | 58.47x |
| CUDA graph capture | completed |
| vLLM status | initialized successfully |
| official smoke return code | 1 |

Final blocker:

`403 Forbidden` for `meta-llama/Meta-Llama-3.1-8B-Instruct`, because the server has no authorized Hugging Face token for that gated repository.

Missing cache:

`data/metadata/model_info_3dfuture_assets_embeds.pickle`

### Reliable Same-Protocol Results Already Available

Source tables:

`results/tables/multiseed_floorprior_mesh_20260708_134245.csv`

`results/tables/multiseed_floorprior_gated_20260708_134245.csv`

Across bedroom, diningroom, and livingroom with seeds 1 and 2:

| Metric | Value |
|---|---:|
| total evaluated mesh scenes | 1062 |
| floor-prior average relation gain | 0.1193 |
| floor-prior average mesh-pair delta | +0.00146 |
| gated average relation gain | 0.0702 |
| baseline average mesh-pair rate | 0.0441 |
| gated average mesh-pair rate | 0.0430 |
| gated fallback scenes | 73 / 1062 |

Interpretation:

The same-protocol InstructScene comparison remains usable: our repair improves relation satisfaction. The collision-gated variant gives a smaller relation gain but keeps the average mesh-pair rate slightly below baseline.

## Git Diff Summary

`git diff` is not available locally because `C:\Users\14754\Desktop\research_worldmodel\.git` exists but is not a valid Git repository; `git rev-parse --show-toplevel` fails with:

```text
fatal: not a git repository (or any of the parent directories): .git
```

File-level changes made in this working folder:

| File | Change |
|---|---|
| `docs/relation_aware_strong_baseline_status.md` | Updated ReSpace status after A100 verification. |
| `docs/strong_baseline_comparison_run_20260708.md` | Added this run report. |
| `visual/strong_baseline_repro_status_20260708.html` | Added readable HTML status page. |

Remote-only generated artifacts:

| Remote path | Purpose |
|---|---|
| `/root/RelationAwareInstructScene/server_setup/run_strong_baseline_a100_audit.sh` | Reproducible A100 audit script. |
| `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/audit_20260708_233225.log` | Full execution log. |
| `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/20260708_233225/summary.json` | Machine-readable summary. |

## Reproduction Steps

1. Start an AutoDL A100-PCIE-40GB instance with the same data disk.
2. SSH into the machine:

```bash
ssh -p 36010 root@region-9.autodl.pro
```

3. Activate ReSpace:

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
```

4. Verify the environment:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))
import transformers, datasets, vllm, trimesh, shapely, clip, xformers, nltk
print("imports ok")
PY
```

5. Run the audit:

```bash
cd /root/RelationAwareInstructScene
tmux new-session -d -s strong-baseline-a100-audit '/root/RelationAwareInstructScene/server_setup/run_strong_baseline_a100_audit.sh'
```

6. Inspect:

```bash
tail -n 240 /root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/audit_20260708_233225.log
cat /root/RelationAwareInstructScene/results/strong_baseline_a100_compare/20260708_233225/summary.json
```

7. To complete ReSpace later, first provide:

```bash
huggingface-cli login
# token must have access to meta-llama/Meta-Llama-3.1-8B-Instruct
```

and place:

```bash
/root/RelationAwareInstructScene/repos/respace/data/metadata/model_info_3dfuture_assets_embeds.pickle
```

8. Rerun the same audit script.

## Unreliable Or Incomplete Parts

1. ReSpace generated no valid comparison scenes because it stops before generation.
2. Missing HF authorization prevents loading `meta-llama/Meta-Llama-3.1-8B-Instruct`.
3. Missing asset embedding cache prevents official asset sampling.
4. ReSpace and our method are not yet compared under a shared final sample set.
5. Local Git diff cannot be produced until the local `.git` directory is repaired or the project is recloned.
6. Claude Code did not execute the remote operations because it could not pass SSH approval.

## Upload Plan For `jomify/research_worldmodel.git`

Upload these local files:

```text
docs/respace_a100_unblock_run_20260709.md
docs/official_strong_baseline_attempt_20260709.md
docs/relation_aware_strong_baseline_status.md
docs/strong_baseline_comparison_run_20260708.md
visual/respace_a100_unblock_run_20260709.html
visual/official_strong_baseline_attempt_20260709.html
visual/strong_baseline_repro_status_20260708.html
results/tables/multiseed_floorprior_mesh_20260708_134245.csv
results/tables/multiseed_floorprior_gated_20260708_134245.csv
visual/multiseed_floorprior_mesh_summary_20260708_134245.html
visual/relation_aware_plain_conclusion_and_next_experiments.html
```

Also upload or archive these remote artifacts if the repository accepts experiment logs:

```text
server_setup/run_strong_baseline_a100_audit.sh
logs/strong_baseline_a100_compare/audit_20260708_233225.log
results/strong_baseline_a100_compare/20260708_233225/summary.json
logs/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409.log
results/strong_baseline_a100_compare/skip_llama_smoke_envfix_20260709_002409/summary.json
logs/strong_baseline_a100_compare/official_min_smoke_20260709_005144.log
results/strong_baseline_a100_compare/official_min_smoke_20260709_005144/summary.json
```

Do not upload:

```text
ReSpace model weights
raw 3D-FRONT / 3D-FUTURE data
Hugging Face tokens
SSH credentials
AutoDL passwords
```
