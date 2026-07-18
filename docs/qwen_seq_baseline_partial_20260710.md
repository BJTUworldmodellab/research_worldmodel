# Qwen/ReSpace Sequential Baseline Partial Run - 2026-07-10

## Bottom Line

I continued the strong-baseline comparison with ReSpace's native sequential editing test, using `Qwen/Qwen2.5-7B-Instruct` as the open command-decomposition model.

This is a stricter test than the previous full-scene non-empty check. It evaluates whether a sequence of add/remove operations succeeds, producing ReSpace-native metrics:

| Metric | Seed 1234 Result |
|---|---:|
| Samples | 10 |
| Mean `acc_seq` | 0.6042 |
| Mean `acc_add` | 0.5440 |
| Mean `acc_rem` | 1.0000 |
| Mean steps per sequence | 5.3 |
| Mean add steps | 4.2 |
| Mean removal steps | 1.1 |

Interpretation: the open Qwen/ReSpace baseline can run and removal can be very strong on the completed seed, but add quality is unstable. This makes it a meaningful baseline, but not yet a clean full comparison against the original relation-aware floor-prior algorithm.

## Executed Command

Script:

```text
server_setup/run_respace_qwen_seq_bedroom_n10.sh
```

Remote command launched:

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export PYTHONPATH=/root/RelationAwareInstructScene/repos/respace:${PYTHONPATH:-}
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export TRANSFORMERS_CACHE=/root/autodl-tmp/RelationAwareInstructScene/hf_cache
export RESPACE_VANILLA_MODEL_ID=Qwen/Qwen2.5-7B-Instruct

python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_qwen_seq_bedroom_n10" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 10 \
  --use-gpu \
  --use-vllm \
  --do-bedroom-testset \
  --do-seq-test \
  --do-icl-for-prompt \
  --do-class-labels-for-prompt \
  --do-prop-sampling-for-prompt \
  --icl-k 2 \
  --bon-llm 1
```

## Logs And Artifacts

| Item | Path |
|---|---|
| Final attempted sequential log | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357.log` |
| Output directory | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357` |
| Seed 1234 metrics | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357/respace_qwen_seq_bedroom_n10/1234_seq_metrics.json` |
| Partial summary | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357/summary_partial_stopped.json` |
| Local script | `server_setup/run_respace_qwen_seq_bedroom_n10.sh` |

## Blocking Points Fixed

1. First run failed before pipeline start because `PYTHONPATH` was missing:

```text
ModuleNotFoundError: No module named 'src'
```

Fix:

```bash
export PYTHONPATH=/root/RelationAwareInstructScene/repos/respace:${PYTHONPATH:-}
```

2. Second run generated the first sequence but failed on saving because the seed output directory did not exist:

```text
FileNotFoundError: .../respace_qwen_seq_bedroom_n10/1234/0_1234.json
```

Fix:

```bash
mkdir -p "$OUT/respace_qwen_seq_bedroom_n10/1234" \
         "$OUT/respace_qwen_seq_bedroom_n10/3456" \
         "$OUT/respace_qwen_seq_bedroom_n10/5678"
```

3. Third run completed seed 1234 and wrote the metric file, then became too slow on seed 3456 due to repeated removal retries on one sample. I stopped it to avoid wasting GPU time.

## Why It Was Stopped

The run reached seed 3456 and got stuck on a removal prompt similar to:

```text
<remove>decorative gold-legged coffee table</remove>
```

The model repeatedly returned a scene where no object was removed. Each retry took roughly 70 seconds, and several retries remained. This is useful evidence: Qwen/ReSpace removal is not uniformly robust even though the completed seed showed `acc_rem=1.0`.

The long run was stopped after preserving:

```text
1234_seq_metrics.json
summary_partial_stopped.json
full log with retry failure
```

## Comparison Status

| Method | Current evidence | What it says |
|---|---|---|
| Original relation-aware floor-prior | 1062 scenes, relation accuracy gain about 0.119 | Stronger and broader evidence |
| ReSpace + Qwen full-scene | 30/30 non-empty bedroom scenes | Generation path works |
| ReSpace + Qwen sequential | seed 1234, 10 samples, `acc_seq=0.6042`, `acc_add=0.5440`, `acc_rem=1.0` | Native ReSpace metric is runnable, add quality is unstable |
| Official ReSpace/Llama | blocked by gated Llama access | Not available without approved HF access |

Important: the sequential ReSpace metric and the original relation-aware metric are not the same metric. This run strengthens the baseline evidence, but a paper-quality comparison still needs a shared evaluator or a clearly separated metric table.

## Recommended Next Step

Do not immediately run the full 3-seed sequential test again. It is too expensive with the current removal retry behavior.

More efficient next steps:

1. Run an add-only ReSpace native benchmark first, because add quality is the weak point and does not suffer from the long removal retry loop.
2. Patch or configure removal retry budget to 1-2 attempts, then rerun sequential n=10 across 3 seeds.
3. Build a shared relation evaluator for ReSpace/Qwen JSON outputs if the goal is to compare directly against relation-aware floor-prior accuracy.

## Upload Recommendation

Upload:

```text
docs/qwen_seq_baseline_partial_20260710.md
server_setup/run_respace_qwen_seq_bedroom_n10.sh
```

Archive remotely if experiment logs are included:

```text
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357.log
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357/summary_partial_stopped.json
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_seq_bedroom_n10_20260710_002357/respace_qwen_seq_bedroom_n10/1234_seq_metrics.json
```

Do not upload credentials, tokens, raw datasets, or model weights.
