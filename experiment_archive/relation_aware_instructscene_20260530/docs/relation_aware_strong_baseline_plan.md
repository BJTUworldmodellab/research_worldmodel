# Strong Baseline Plan and Feasibility Notes

Date: 2026-05-29

This note records what was checked for strong related baselines while the mesh-collision and visual-quality experiments were running.

## ReSpace

Repository checked on the remote server:

- Path: `/root/RelationAwareInstructScene/repos/respace`
- Commit: `1eccb69`
- Size after shallow clone: about `202M`
- Official source: https://arxiv.org/abs/2506.02459
- Model/repository pointer: https://huggingface.co/gradient-spaces/respace-sg-llm-1.5b

Why it is a strong baseline:

- Text-driven 3D indoor scene generation/editing.
- Uses a structured scene representation and spatial reasoning.
- Provides official eval scripts for full-scene and instruction-following settings.
- Reports fine-grained geometry violation metrics.

Why it is not plug-and-play comparable to the current InstructScene split:

- Official scripts target SSR-3DFRONT protocol, not the InstructScene validation prompts used here.
- The official eval scripts default to `N_TEST_SCENES=500` and room categories `bedroom`, `livingroom`, and `all`; there is no direct dining-room split matching our InstructScene setting.
- The code imports `vllm` unconditionally and initializes `meta-llama/Meta-Llama-3.1-8B-Instruct` for zero-shot prompting, which is a gated model dependency.
- It requires its own `.env` data paths, asset metadata, render/eval cache, and separate environment. The current machine has only about `1.8G` free under `/root/autodl-tmp`, although root overlay has more space.

Fair comparison path:

1. Create a separate `respace` environment, not inside `relation_scene`.
2. Point ReSpace `.env` to existing 3D-FRONT and 3D-FUTURE assets:
   - `PTH_3DFRONT_SCENES=/root/RelationAwareInstructScene/raw_data/3D-FRONT`
   - `PTH_3DFUTURE_ASSETS=/root/RelationAwareInstructScene/raw_data/3D-FRONT/3D-FUTURE-model`
3. Run a small ReSpace pilot only after confirming gated model access and vLLM imports.
4. For paper comparison, either:
   - run ReSpace under its native SSR-3DFRONT protocol and report separately, or
   - build a shared prompt/asset protocol where both methods consume the same prompts and are evaluated with the same relation, collision, and visual metrics.

Current paper-safe statement:

ReSpace is a strong related baseline, but no fair same-split result has been obtained yet. Do not claim superiority over ReSpace.

## SDGScenes

Source checked:

- ScienceDirect: https://www.sciencedirect.com/science/article/pii/S0031320326006394

Why it is a strong baseline:

- Uses Semantic Dependency Graphs.
- Targets implicit user intent.
- Uses VLM-derived commonsense constraints.
- Optimizes object placement with semantic and physical constraints.

Current status:

- No directly runnable same-split code path has been verified on the server.
- Because the method overlaps strongly with relation/constraint-aware placement, it must be treated as a close related method and not hand-waved away.

Current paper-safe statement:

SDGScenes is a close related method. Without a shared protocol reproduction or official same-split numbers, the current work cannot claim to outperform it.

## Recommended Baseline Section Wording

Use:

> We compare directly against the InstructScene generation output under the same official validation prompts and checkpoints. ReSpace and SDGScenes are close related systems with different evaluation protocols; we discuss them as strong related work and leave shared-protocol reproduction as future work unless a fair same-split implementation is completed.

Do not use:

> We outperform ReSpace or SDGScenes.

Do not use:

> Relation-Aware InstructScene is the first relation-aware 3D scene generation method.
