# Qwen/ReSpace Add-Only Baseline - 2026-07-10

## Bottom Line

I attempted to delegate the concrete work to local Claude Code as requested, but two Claude Code runs stayed silent and did not create a remote tmux session, script, or GPU process. I then launched the same narrowly scoped add-only benchmark directly to avoid wasting the GPU rental window.

The first add-only ReSpace/Qwen benchmark completed successfully on seed 1234, and I later extended it to all three standard seeds.

| Metric | Result |
|---|---:|
| Room | bedroom |
| Seed | 1234 |
| Test scenes | 10 |
| Return code | 0 |
| JSON outputs | 10 |
| Non-empty scenes | 10 |
| Empty scenes | 0 |
| Average objects per non-empty scene | 3.9 |
| ReSpace reported success rate | 10.00 |
| Average scene generation time | 1.69 s |

Multi-seed extension:

| Metric | Result |
|---|---:|
| Seeds | 1234, 3456, 5678 |
| Test scenes per seed | 10 |
| Total JSON outputs | 30 |
| Non-empty scenes | 30 |
| Empty scenes | 0 |
| Average objects per non-empty scene | 3.5667 |

## Executed Command

Local script:

```text
server_setup/run_respace_qwen_addonly_bedroom_n10.sh
```

Remote launch:

```bash
tmux kill-session -t respace_compare 2>/dev/null || true
chmod +x /root/RelationAwareInstructScene/server_setup/run_respace_qwen_addonly_bedroom_n10.sh
tmux new-session -d -s respace_compare 'bash /root/RelationAwareInstructScene/server_setup/run_respace_qwen_addonly_bedroom_n10.sh'
```

Pipeline command inside the script:

```bash
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_qwen_addonly_bedroom_n10" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 10 \
  --use-gpu \
  --use-vllm \
  --do-bedroom-testset \
  --seed-only 1234 \
  --do-icl-for-prompt \
  --do-class-labels-for-prompt \
  --do-prop-sampling-for-prompt \
  --icl-k 2 \
  --bon-llm 1
```

## Logs And Artifacts

| Item | Path |
|---|---|
| Log | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_20260710_041303.log` |
| Output dir | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_20260710_041303` |
| Scene JSON dir | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_20260710_041303/respace_qwen_addonly_bedroom_n10/1234` |
| Summary | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_20260710_041303/summary_verified.json` |

## Key Metrics

Object counts per scene:

```text
7, 5, 4, 5, 2, 2, 5, 1, 6, 2
```

Aggregate:

```text
total_json = 10
nonempty = 10
empty = 0
avg_objects_nonempty = 3.9
QWEN_ADDONLY_RC = 0
```

ReSpace log:

```text
Finished seed 1234 - success rate : 10.00 (+/- 0.00)
Average scene generation time for seed 1234: 1.69 s (+/- 0.59 s) over 10 scenes
FINISHED! success rate: 10.00 (+/- 0.00)
```

## Comparison Interpretation

This run is useful because it isolates add-object behavior without the slow repeated removal retry loop seen in the sequential benchmark.

Current evidence:

| Method | Evidence | Interpretation |
|---|---|---|
| Original relation-aware floor-prior | 1062 scenes, relation accuracy gain about 0.119 | Strongest current evidence |
| Qwen/ReSpace full-scene | 30/30 non-empty bedroom scenes | Full-scene generation works |
| Qwen/ReSpace sequential | seed 1234 `acc_seq=0.6042`, `acc_add=0.5440`, `acc_rem=1.0` | Native sequential metric is stricter; add quality unstable |
| Qwen/ReSpace add-only | seed 1234 10/10 non-empty, rc 0 | Add-only pipeline is stable on this small subset |

Important caveat: add-only non-empty success is not the same as relation accuracy. It supports ReSpace/Qwen as a runnable baseline, but it does not yet prove semantic or spatial superiority.

## Still Unreliable

1. Only bedroom seed 1234 was run for add-only.
2. The metric here is ReSpace add success/non-empty output, not the original algorithm's relation-accuracy metric.
3. Logs still include many `raw_model.glb` path warnings, so mesh-based geometry metrics remain suspect.
4. Claude Code did not successfully perform the remote work in this environment; it appeared to hang before creating remote artifacts.

## Upload Recommendation

Upload:

```text
docs/qwen_respace_addonly_20260710.md
visual/qwen_respace_addonly_20260710.html
server_setup/run_respace_qwen_addonly_bedroom_n10.sh
docs/qwen_seq_baseline_partial_20260710.md
server_setup/run_respace_qwen_seq_bedroom_n10.sh
```

Optional remote artifacts to archive:

```text
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_20260710_041303.log
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_20260710_041303/summary_verified.json
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_multiseed_20260710_045939.log
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_addonly_bedroom_n10_multiseed_20260710_045939/summary_verified.json
```

Do not upload passwords, tokens, raw data, or model weights.
