# SDGScenes Strong Baseline Cloud Run Log

Status: draft  
Owner: user  
Cloud: AutoDL  
Target GPU: RTX PRO 6000 / 96GB  
Claim policy: defensive, protocol-aware, non-SOTA unless direct reproducibility is proven

## 1. Objective

Run a strong SDGScenes-related baseline package for relation grounding experiments. The main paper claim remains under the existing InstructScene validation protocol: our final-layout repair improves realized relation accuracy over official InstructScene output.

SDGScenes/ReSpace/CommonScenes are treated as SOTA references with protocol boundaries unless same-split, same-input, same-output, same-metric reproduction succeeds.

## 2. Machine Provenance

To be filled from:

- `/root/autodl-tmp/rg-sota-cloud/manifests/machine_fingerprint_*.txt`
- `/root/autodl-tmp/rg-sota-cloud/manifests/nvidia_smi_*.txt`
- `/root/autodl-tmp/rg-sota-cloud/manifests/gpu_query_*.csv`
- `/root/autodl-tmp/rg-sota-cloud/manifests/disk_*.txt`
- `/root/autodl-tmp/rg-sota-cloud/manifests/pip_freeze_relation_sdg_*.txt`
- `/root/autodl-tmp/rg-sota-cloud/manifests/project_git_head_*.txt`

## 3. Data Provenance

Raw data manifest:

- `/root/autodl-tmp/rg-sota-cloud/manifests/raw_data_manifest.tsv`

Rules:

- raw licensed data remains on cloud disk/NAS/object storage;
- GitHub stores code/config/manifests, not restricted raw datasets;
- every dataset artifact has SHA256, source, license/terms, split, and timestamp.

## 4. SDGScenes Feasibility

Official code status:

- [ ] official repo located
- [ ] official license checked
- [ ] official setup reproduced
- [ ] official smoke test complete
- [ ] same protocol verified

If any item is unchecked, results are labeled:

`SDGScenes-inspired strong baseline`, not official SDGScenes reproduction.

## 5. Experiment Matrix

| Track | Method | Comparable status | Split | Metrics | Notes |
|---|---|---:|---|---|---|
| Main | official InstructScene | direct | same val split | relation acc / collision / movement / OOB / runtime | primary baseline |
| Main | Ours Floor-Prior | direct | same val split | same evaluator | primary result |
| Main | Ours collision-gated | direct | same val split | same evaluator | mesh-validity claim |
| Control | random/local move | direct | same val split | same evaluator | sanity control |
| Control | constraint optimization | direct if same input | same val split | same evaluator | local optimizer baseline |
| Upper bound | oracle parser | direct upper bound | same val split | same evaluator | parser ceiling |
| SOTA ref | SDGScenes official | pending | unknown | protocol analysis | only direct if reproduced |
| SOTA ref | SDGScenes-inspired | non-direct or defensive direct-control | same val split if implemented | same evaluator | not official |
| SOTA ref | ReSpace | pending | SSR-3DFRONT / own protocol | feasibility | no superiority claim |

## 6. Smoke Test Results

Bedroom smoke test:

| Run ID | Commit | Config | N | Relation Acc | Movement | Collision | Overlap | OOB | Runtime | Failure Notes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## 7. Full Results

| Method | Split | N | Relation Acc | Movement | Mesh Collision | Overlap | OOB | Runtime | Direct Comparable? |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| official InstructScene | bedroom | TBD | TBD | TBD | TBD | TBD | TBD | TBD | yes |
| Ours Floor-Prior | bedroom | TBD | TBD | TBD | TBD | TBD | TBD | TBD | yes |
| Ours collision-gated | bedroom | TBD | TBD | TBD | TBD | TBD | TBD | TBD | yes |
| SDGScenes-inspired baseline | bedroom | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## 8. Failure Gallery

Gallery roots:

- `/root/autodl-tmp/rg-sota-cloud/artifacts/renders/success/`
- `/root/autodl-tmp/rg-sota-cloud/artifacts/renders/failure/`

Failure taxonomy:

- parser miss
- impossible relation
- collision introduced
- OOB introduced
- excessive movement
- mesh evaluator mismatch
- missing category/asset mapping

## 9. Claim-safe wording

Allowed:

> Compared with official InstructScene output under the same validation protocol, our method improves final realized relation accuracy.

Allowed:

> SDGScenes and ReSpace are stronger related systems under different protocols; we report them as non-direct SOTA references unless same-protocol reproduction succeeds.

Allowed:

> Our verifier-repair can serve as a final-layout grounding layer for generators that expose object layouts.

Not allowed:

> We outperform SDGScenes / ReSpace.

Not allowed:

> We are SOTA on text-driven 3D scene generation.

Not allowed:

> We provide universal visual quality improvement or complete commonsense reasoning.

## 10. Open Blockers

- DeepSeek API key required for Claude Code backend.
- Notion plugin/workspace authorization required for direct cloud doc writing.
- GitHub authorization required for push.
- Official SDGScenes code availability unknown; if unavailable, use protocol analysis + inspired baseline only.
