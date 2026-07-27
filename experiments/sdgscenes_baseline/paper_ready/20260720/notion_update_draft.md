# Notion 更新稿：SDGScenes Defensive Baseline 结果归档

建议 Notion 属性：

- Title: `2026-07-20 SDGScenes defensive baseline / H800 smoke result lock`
- Type: `Reference` 或 `Decision`
- Category: `Engineering`
- Status: `In Review`
- Tags: `SDGScenes`, `SOTA comparison`, `relation grounding`, `InstructScene`, `defensive baseline`, `H800`
- Last Reviewed: `2026-07-20`

## TL;DR

本轮已经完成 SDGScenes defensive baseline 的可复现实验包、HTML 人类可读报告、机器可读结果包，以及论文可用的实验 section / 三张表草稿。结论边界保持防御性：SDGScenes official 目前不作为直接 numerical ranking baseline；本次只报告 protocol boundary、official reproduction feasibility，以及一个同 evaluator 的 `SDGScenes-inspired` constrained-optimization smoke baseline。

## 当前结论

- 主论文 claim 仍然限定为：在 official InstructScene validation protocol 下，我们的 final-layout verifier-repair 相比 official InstructScene output 改善 realized relation grounding。
- SDGScenes 是更完整的 user-intent / semantic dependency graph / VLM constraints / constrained optimization 系统，但当前没有完成 official reproduction，因此不进入 direct ranking table。
- 本次 H800 上的 SDGScenes-inspired strong baseline 是 defensive control，不是 official SDGScenes reproduction。
- 如果未来找到 official code、official split、output conversion 和 evaluator alignment，再把 SDGScenes 从 protocol/reference table 移到 direct-comparison candidate。

## 关键数字

### Same-protocol main result

数据范围：bedroom + living room + dining room，共 531 scenes / 808 evaluated relations。

- Official InstructScene relation accuracy: 62.3%
- Floor-Prior relation accuracy: 75.0%
- Floor-Prior gain: +12.7 pp
- Collision-gated repair relation accuracy: 74.6%
- Collision-gated gain: +12.4 pp
- Collision-gated mesh-pair collision rate: 4.2%，低于 official baseline 的 4.4%
- Collision-gated mesh-scene collision rate: 70.8%，低于 official baseline 的 71.9%

### SDGScenes-inspired defensive smoke baseline

数据范围：同 531 scenes，共 708 target relations，其中 horizontal relations 641 个。

- Before all-relation accuracy: 41.9%
- After all-relation accuracy: 79.2%
- Gain: +37.3 pp
- Before horizontal accuracy: 38.0%
- After horizontal accuracy: 79.0%
- Horizontal gain: +41.0 pp
- Optimizer edits: 293
- Avg final movement / scene: 0.94
- Overlap pairs: 894 → 833
- OOB centers: 0 → 0
- Missing object-pair cases logged separately: 92

## Claim policy

可以写：

- Compared with the official InstructScene output under the same validation protocol, our method improves final realized relation accuracy.
- SDGScenes and ReSpace are strong related systems under different protocols; we report them as non-direct references unless same-protocol reproduction succeeds.
- Our verifier-repair can potentially serve as a final-layout grounding layer for generators that expose object layouts.

不能写：

- outperform SDGScenes
- outperform ReSpace
- SOTA on text-driven 3D scene generation
- first relation-aware 3D scene generation
- universal visual quality improvement
- complete commonsense / affordance / reachability reasoning

## 产物位置

### 人类可读

- HTML main report: `outputs/sdgscenes_defensive_baseline/exports/20260720_h800_sdgscenes_results/human/index.html`
- Portable HTML report: `outputs/sdgscenes_defensive_baseline/exports/20260720_h800_sdgscenes_results/human/portable_report.html`

### 机器可读

- Result package: `outputs/sdgscenes_defensive_baseline/exports/20260720_h800_sdgscenes_results/machine/results_package.json`
- Machine bundle: `outputs/sdgscenes_defensive_baseline/exports/20260720_h800_sdgscenes_results/machine/sdgscenes_results_machine_20260720.tar.gz`
- Source manifest: `outputs/sdgscenes_defensive_baseline/exports/20260720_h800_sdgscenes_results/machine/source_files_manifest.csv`

### 论文材料

- Experiment section draft: `outputs/paper_ready_sdgscenes_defensive_baseline_20260720/paper_experiment_section.md`
- Markdown tables: `outputs/paper_ready_sdgscenes_defensive_baseline_20260720/paper_tables.md`
- LaTeX tables: `outputs/paper_ready_sdgscenes_defensive_baseline_20260720/paper_tables.tex`

### GitHub fallback

- Full patch: `outputs/sdgscenes_defensive_baseline/github_export_20260720_dual_format_final/sdgscenes_defensive_baseline_final_20260720_full.patch`
- Git bundle: `outputs/sdgscenes_defensive_baseline/github_export_20260720_dual_format_final/sdgscenes_defensive_baseline_final_20260720.bundle`

## Paper placement suggestion

- Main paper: 放 Table 1，同协议 main result；Table 2 用压缩版说明 SOTA protocol boundary。
- Appendix: 放完整 Table 2、Table 3、official feasibility、reported-results context policy。
- Related work: 明确 SDGScenes / ReSpace 是 strong related systems under different protocols，不 claim 超越。

## Follow-up TODO

- 将 paper-ready section 合并进论文实验章节。
- 如果 GitHub 远端可推送，推送 `exp/sdgscenes-defensive-baseline-20260711` 分支或导入 final patch/bundle。
- 如果要继续加强 SOTA 防御，下一步优先做 ReSpace feasibility smoke test；除非 official SDGScenes release 可无障碍跑通，否则不烧卡做 full reproduction。

