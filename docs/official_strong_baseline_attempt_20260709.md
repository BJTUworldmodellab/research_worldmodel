# Official Strong Baseline Attempt And Current Algorithm Check - 2026-07-09

## Bottom Line

The official ReSpace strong baseline still cannot produce valid official comparison scenes because it is blocked by Hugging Face gated access to `meta-llama/Meta-Llama-3.1-8B-Instruct`.

This run is useful because it proves the remaining blocker is not GPU, CUDA, vLLM, ReSpace SG-LLM weights, dataset splits, `PTH_STAGE_2_DEDUP`, or the asset embedding cache. Those parts now work.

The original relation-aware/floor-prior algorithm remains usable based on the existing multi-seed evaluation: 1062 mesh scenes across bedroom, dining room, and living room, with average relation accuracy gain of about 0.119.

## Official ReSpace Attempt

Executed on the A100 machine with official `src/respace.py` restored, no `RESPACE_SKIP_GATED_LLAMA`, rebuilt asset cache present, and `PTH_STAGE_2_DEDUP` set.

Command:

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
/root/RelationAwareInstructScene/server_setup/run_respace_official_min_smoke.sh
```

The script runs:

```bash
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_official_bedroom_vllm" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 1 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --icl-k 1 \
  --bon-llm 1 \
  --seed-only 1234
```

Artifacts:

| Item | Path |
|---|---|
| Official smoke log | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/official_min_smoke_20260709_005144.log` |
| Official smoke output dir | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/official_min_smoke_20260709_005144` |
| Official summary JSON | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/official_min_smoke_20260709_005144/summary.json` |

Result:

| Check | Result |
|---|---|
| A100 GPU | OK: `NVIDIA A100-PCIE-40GB`, compute capability 8.0 |
| SG-LLM checkpoint | OK: `gradient-spaces/respace-sg-llm-1.5b` |
| vLLM | OK: initialized with Flash Attention |
| Model weights | OK: 2.8875 GB loaded |
| KV cache | OK: 4.68 GiB |
| Asset cache | OK: 174 MB rebuilt pickle |
| `PTH_STAGE_2_DEDUP` | OK: points to SSR-3D scene JSON folder |
| Official Llama tokenizer | Blocked: 403 Forbidden |
| Return code | 1 |

Key failure line:

```text
403 Forbidden: Please enable access to public gated repositories in your fine-grained token settings to view this repository.
```

## Original Algorithm Check

The existing multi-seed evaluation tables are readable and internally consistent.

Input tables:

```text
results/tables/multiseed_floorprior_mesh_20260708_134245.csv
results/tables/multiseed_floorprior_gated_20260708_134245.csv
```

Aggregate metrics:

| Metric | Value |
|---|---:|
| Rows | 6 |
| Mesh scenes | 1062 |
| Baseline relation accuracy | 0.6270 |
| Floor-prior relation accuracy | 0.7463 |
| Floor-prior average gain | 0.1193 |
| Gated average gain | 0.0702 |
| Mean mesh-pair delta | 0.00146 |
| Gated fallback scenes | 73 / 1062 |

By room:

| Room | Mesh scenes | Floor-prior gain | Gated gain |
|---|---:|---:|---:|
| Bedroom | 324 | 0.0918 | 0.0653 |
| Dining room | 354 | 0.1283 | 0.0669 |
| Living room | 384 | 0.1378 | 0.0782 |

Interpretation:

1. The original algorithm is currently usable: all six room/seed rows show positive relation-accuracy gain.
2. The improvement is strongest in living room and dining room, weaker but still positive in bedroom.
3. Gated repair is more conservative than the full floor-prior repair: it still improves relation accuracy, but by a smaller margin.
4. Mesh-pair rate changes are small, so the improvement is not obviously coming from a large increase in close mesh pairs.

## Comparison Status

| Method | Status | Evidence |
|---|---|---|
| Original relation-aware floor-prior | Usable | 1062-scene multi-seed table, average gain 0.1193 |
| Gated variant | Usable but weaker | 1062-scene table, average gain 0.0702, 73 fallback scenes |
| ReSpace official baseline | Not yet runnable | Official no-skip run reaches vLLM, then fails on gated Llama 403 |
| ReSpace smoke-only bypass | Engineering validation only | Runs successfully, but uses dummy command decomposition and is not a baseline |

## What Is Still Needed For A Formal Strong Baseline

1. Provide a Hugging Face token that has accepted and enabled access to `meta-llama/Meta-Llama-3.1-8B-Instruct`.
2. Run official ReSpace without `RESPACE_SKIP_GATED_LLAMA`.
3. Start with `bedroom`, `n_test_scenes=10`, `seed_only=1234` to validate official output.
4. Then run the same room/seed coverage as the original algorithm, or at least a matched subset.
5. Repair raw 3D-FUTURE mesh paths before relying on geometry/rendering metrics, because previous smoke logs showed repeated `raw_model.glb` path warnings.

## Upload Recommendation

Add this report and the previous A100 unblock report:

```text
docs/official_strong_baseline_attempt_20260709.md
docs/respace_a100_unblock_run_20260709.md
visual/respace_a100_unblock_run_20260709.html
```

Archive these remote logs if experiment logs are accepted:

```text
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/official_min_smoke_20260709_005144.log
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/official_min_smoke_20260709_005144/summary.json
```

Do not upload credentials, tokens, AutoDL passwords, model weights, or raw 3D-FRONT/3D-FUTURE data.
