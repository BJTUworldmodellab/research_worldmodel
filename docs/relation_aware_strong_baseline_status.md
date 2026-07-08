# Strong Baseline Feasibility Status

This note separates fair same-protocol baselines from close related systems that cannot yet be used for an outperforming claim.

| Method | Status | Fairness | Paper use |
|---|---|---|---|
| InstructScene | available and executed | fair | Use as primary baseline: our repair improves explicit relation satisfaction over original InstructScene outputs under the same split. |
| Direct y-fixed repair | available and executed; blocker: Higher relation gain can come with larger movement and small mesh-pair increases in some rooms. | fair internal ablation | Use as ablation showing why floor-prior and collision gating are needed. |
| Collision-gated direct/floor-prior repair | available and executed; blocker: Post-hoc verifier fallback should be described explicitly, not hidden as pure generation. | fair internal variant | Use for mesh-validity claim: relation gains remain positive while mesh collision pair rate does not increase. |
| ReSpace | repo cloned on remote; no runnable same-split result; blocker: Requires separate environment, SSR-3DFRONT assets/cache, vLLM, and HuggingFace access for released model; remote has no HF token and low /root/autodl-tmp free space. | not fair yet | Discuss as close related work only unless a shared protocol is built and executed. |
| SDGScenes | no verified runnable same-split implementation on this server; blocker: No shared-protocol reproduction or official same-split result. | not fair yet | Discuss as close related work; do not claim superiority. |
| CommonScenes | repo cloned on remote; not executed as same text-instruction baseline; blocker: Different input modality and benchmark target; full setup requires additional processed data/checkpoints. | not same-protocol | Cite as related scene-graph generation family, not as direct text-instruction baseline. |

## Bottom Line

- The current fair baseline is InstructScene under the same official validation prompts and checkpoints.
- Direct y-fixed repair and collision-gated repair are valid internal baselines/ablations.
- ReSpace, SDGScenes, and CommonScenes should be treated as close related work until a shared protocol is actually executed.
- Do not write that this method outperforms ReSpace or SDGScenes based on the current evidence.
