# Qwen Open Reproducible ReSpace-Style Baseline - 2026-07-09

## Bottom Line

Because the official ReSpace command-decomposition model `meta-llama/Meta-Llama-3.1-8B-Instruct` is gated and the access request was rejected, I replaced only that command-decomposition LLM with `Qwen/Qwen2.5-7B-Instruct`.

This gives us an open, reproducible, and reasonably strong ReSpace-style baseline. It is not the official ReSpace baseline, so it should be reported as "ReSpace with Qwen2.5-7B command decomposition" rather than "official ReSpace".

The final repaired run succeeded on the new A100 machine:

| Metric | Result |
|---|---:|
| Room type | bedroom |
| Test scenes per seed | 10 |
| Seeds | 1234, 3456, 5678 |
| Total JSON scenes | 30 |
| Non-empty scenes | 30 |
| Empty scenes | 0 |
| Average objects per non-empty scene | 4.70 |
| Return code | 0 |

## Why This Model

`Qwen/Qwen2.5-7B-Instruct` was selected because it is public/non-gated, strong at instruction following, and fits comfortably on the A100-PCIE-40GB together with the ReSpace SG-LLM/vLLM path. A 14B model may be stronger, but it is more likely to create memory and stability pressure under this pipeline. For a convincing first accessible baseline, 7B is the better tradeoff.

## Environment

| Item | Value |
|---|---|
| Server | AutoDL new A100 instance |
| GPU | NVIDIA A100-PCIE-40GB, 40 GB |
| Repo | `/root/RelationAwareInstructScene/repos/respace` |
| Conda env | `respace` |
| SG-LLM | `gradient-spaces/respace-sg-llm-1.5b` |
| Open command LLM | `Qwen/Qwen2.5-7B-Instruct` |
| Asset cache | `/root/RelationAwareInstructScene/repos/respace/data/metadata/model_info_3dfuture_assets_embeds.pickle` |
| Stage-2 dataset env | `.env.baseline`, `PTH_STAGE_2_DEDUP=/root/autodl-tmp/RelationAwareInstructScene/respace_data/dataset-ssr3dfront/scenes` |

## Code Change Summary

Remote diff summary:

```text
src/respace.py | 40 +++++++++++++++++++++++++++++++++++-----
src/utils.py   |  5 +++--
2 files changed, 38 insertions(+), 7 deletions(-)
```

Functional changes:

1. `src/utils.py`: `get_llama_vanilla_pipeline()` now accepts a model id and reads `RESPACE_VANILLA_MODEL_ID`, defaulting back to the official Llama model when unset.
2. `src/respace.py`: the vanilla command-decomposition model is no longer hard-coded; it reads `RESPACE_VANILLA_MODEL_ID`.
3. `src/respace.py`: command parsing now tolerates common Qwen outputs, including fenced JSON, list-only JSON, missing commas between command strings, and plain tagged command text such as `<add>...</add>`.

This keeps the official path available: if `RESPACE_VANILLA_MODEL_ID` is not set, the code still tries to use `meta-llama/Meta-Llama-3.1-8B-Instruct`.

## Executed Commands

Smoke test:

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
export RESPACE_VANILLA_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_qwen_bedroom_vllm" \
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

Final bedroom n=10 comparison run:

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
bash /root/RelationAwareInstructScene/server_setup/run_respace_qwen_open_baseline_bedroom_n10.sh
```

The script uses:

```bash
export RESPACE_VANILLA_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
python src/pipeline.py \
  --env .env.baseline \
  --pth-output "$OUT/respace_qwen_bedroom_vllm_n10" \
  --room-type bedroom \
  --model-id gradient-spaces/respace-sg-llm-1.5b \
  --n-test-scenes 10 \
  --use-gpu \
  --use-vllm \
  --do-full-scenes \
  --do-bedroom-testset \
  --do-icl-for-prompt \
  --do-class-labels-for-prompt \
  --do-prop-sampling-for-prompt \
  --icl-k 2 \
  --bon-llm 1
```

## Logs And Artifacts

| Run | Log path | Output path | Result |
|---|---|---|---|
| Qwen smoke n=1 | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_open_baseline_smoke_20260709_231646.log` | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_smoke_20260709_231646` | 1/1 scene, rc 0 |
| Qwen n=10 before parser repair | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_232428.log` | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_232428` | 23/30 non-empty |
| Qwen n=10 partial parser repair | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_234001.log` | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_234001` | 29/30 non-empty |
| Qwen n=10 final parser repair | `/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431.log` | `/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431` | 30/30 non-empty |

Verified final summary:

```text
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431/summary_verified.json
```

Final output scene directory:

```text
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431/respace_qwen_bedroom_vllm_n10
```

## Key Metrics

Final verified object counts:

| Seed | JSON scenes | Non-empty scenes | Object counts |
|---|---:|---:|---|
| 1234 | 10 | 10 | 3, 5, 5, 6, 6, 4, 6, 6, 9, 5 |
| 3456 | 10 | 10 | 5, 4, 3, 6, 8, 6, 4, 4, 4, 3 |
| 5678 | 10 | 10 | 4, 2, 5, 5, 5, 4, 5, 4, 3, 2 |

Aggregate:

```text
total_json = 30
nonempty = 30
empty = 0
avg_objects_nonempty = 4.70
```

The log also reports successful generation for every seed:

```text
Finished seed 1234 - success rate : 10.00 (+/- 0.00)
Finished seed 3456 - success rate : 10.00 (+/- 0.00)
Finished seed 5678 - success rate : 10.00 (+/- 0.00)
FINISHED! success rate: 10.00 (+/- 0.00)
```

## Comparison With The Original Algorithm

The original relation-aware floor-prior algorithm has stronger current evidence because it has already been evaluated on a larger multi-room, multi-seed set:

| Method | Evidence available now | Current interpretation |
|---|---|---|
| Original relation-aware floor-prior | 1062 mesh scenes, bedroom/dining/living, average relation-accuracy gain about 0.119 | Usable and internally consistent |
| Gated variant | 1062 scenes, average gain about 0.070, 73 fallback scenes | Usable but weaker |
| Official ReSpace | Blocked by gated Llama access | Not runnable without approved HF access |
| ReSpace + Qwen2.5-7B | 30/30 bedroom scenes generated successfully | Reproducible open baseline, but not yet a full metric comparison |

Important: this Qwen run proves the strong baseline pipeline can generate scenes with an accessible model. It does not yet prove that our original algorithm beats ReSpace/Qwen, because the Qwen outputs have not been evaluated with the same relation-accuracy metric used by the original algorithm.

## Reproduction Steps

1. Start an A100-PCIE-40GB AutoDL instance with the existing ReSpace environment.
2. Enter the ReSpace repo:

```bash
cd /root/RelationAwareInstructScene/repos/respace
source /root/miniconda3/etc/profile.d/conda.sh
conda activate respace
```

3. Confirm syntax:

```bash
python -m py_compile src/respace.py src/utils.py
```

4. Set the open command-decomposition model:

```bash
export RESPACE_VANILLA_MODEL_ID=Qwen/Qwen2.5-7B-Instruct
```

5. Run the smoke test first, then the bedroom n=10 script.
6. Verify scene counts:

```bash
python3 - <<'PY'
import json, pathlib, statistics
base=pathlib.Path('/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431/respace_qwen_bedroom_vllm_n10')
rows=[]
for p in sorted(base.glob('*/*.json')):
    data=json.loads(p.read_text())
    objs=data.get('objects') or data.get('object_list') or data.get('scene',{}).get('objects') or []
    rows.append(len(objs))
print('total_json =', len(rows))
print('nonempty =', sum(1 for x in rows if x))
print('avg_objects_nonempty =', statistics.mean([x for x in rows if x]))
PY
```

## What Is Still Unreliable

1. This is not official ReSpace because the official Llama model remains gated.
2. The baseline is bedroom-only and small-scale so far: 30 generated scenes.
3. It has generation success metrics, but not yet the same relation-accuracy metric as the original algorithm.
4. ReSpace logs still show some `raw_model.glb` mesh path warnings, so geometry/rendering-based metrics need a mesh-path audit before being trusted.
5. The parser repair is an engineering compatibility layer for Qwen output format. It is necessary for reproducibility, but it should be disclosed.
6. The local Windows workspace has an invalid `.git` directory, so final upload should be done from a clean Git clone or after repairing local Git metadata.

## Recommended Next Experiments

1. Build or adapt a metric adapter so ReSpace/Qwen outputs can be scored by the same relation-accuracy evaluator used for the original algorithm.
2. Run the same bedroom subset for the original method and ReSpace/Qwen, then compare using exactly the same metric.
3. After the metric is common, expand ReSpace/Qwen to dining room and living room.
4. Only after that, run parameter ablation and stronger/faster open LLM variants if the first comparison is promising.

## Upload Recommendation

Upload these local report files:

```text
docs/qwen_open_reproducible_baseline_20260709.md
visual/qwen_open_reproducible_baseline_20260709.html
docs/official_strong_baseline_attempt_20260709.md
docs/respace_a100_unblock_run_20260709.md
visual/official_strong_baseline_attempt_20260709.html
visual/respace_a100_unblock_run_20260709.html
```

Archive these remote experiment artifacts if logs/results are included in the repository or release assets:

```text
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_open_baseline_smoke_20260709_231646.log
/root/RelationAwareInstructScene/logs/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431.log
/root/RelationAwareInstructScene/results/strong_baseline_a100_compare/qwen_open_baseline_bedroom_n10_20260709_235431/summary_verified.json
```

Do not upload credentials, HF tokens, AutoDL passwords, model weights, or raw 3D-FRONT/3D-FUTURE data.
