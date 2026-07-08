# Relation-Aware InstructScene 实验总报告

日期：2026-05-30

## 一句话结论

我们当提出一个训练自由的关系验证与修复层，显著提升 instruction 中显式空间关系在最终 3D layout 中的实现率，同时通过 floor-prior、y-height 保持和 collision-gated verifier 控制几何副作用。

最安全的主 claim：

> Relation-Aware InstructScene identifies and repairs a graph-to-layout grounding gap in instruction-guided 3D indoor scene generation. On existing InstructScene validation splits, the floor-prior verifier-repair layer improves explicit spatial relation realization with bounded x/z movement, unchanged object height, and mesh-collision-controlled outputs.

不要 claim：

- 不是 first relation-aware 3D scene generation。
- 不能说全面超过 ReSpace / SDGScenes。
- 不能说视觉质量普遍更好。
- 不能说处理所有隐式 commonsense relation。
- 不能把 collision-gated fallback 隐藏成纯生成能力。

## 创新点

### 1. 从 graph-level relation 转向 realized layout relation

InstructScene 的 scene graph 可以表达关系，但最终连续布局不一定真正实现这些关系。我们的核心观察是：relation correctness 不能只在图层面评估，必须在最终 layout 几何层面验证。

创新价值：

- 明确提出并量化 graph-to-layout grounding gap。
- 直接评估最终 3D layout 中的空间关系是否成立。
- 让 text-to-scene 的关系一致性从“生成了关系符号”变成“最终物体位置满足关系”。

### 2. 不构建新 benchmark，不新增标注

方法使用现有 InstructScene validation prompts、官方 checkpoint 和已有关系/evaluator。我们没有自己构建新的 benchmark，也没有新增人工标注。

创新价值：

- 更容易被 reviewer 接受为 fair comparison。
- 复现成本低。
- 避免“自己造数据自己赢”的问题。

### 3. Plug-in verifier-repair 层

我们不是替换 InstructScene 生成模型，而是在生成后插入轻量模块：

1. 从 instruction 解析显式空间关系。
2. 将 relation triples 匹配到生成物体类别。
3. 验证 layout 是否满足关系。
4. 对 x/z 平面做 bounded repair。
5. 保持 y 高度不变，避免家具腾空。
6. 可选 collision-gated fallback，避免 mesh collision 增加。

创新价值：

- 不需要 retraining。
- 可作为 pretrained scene generator 的后处理控制层。
- 能清楚拆分 language parsing、geometry verification、repair selection 三个责任。

### 4. Floor-prior 关系修复

早期 direct repair 虽然 relation gain 更高，但移动幅度大，并且在部分房间会轻微增加 mesh collision。floor-prior 版本加入了更保守的候选选择：

- 只移动 x/z，不改变 y。
- 使用 `max_repair_move` 限制位移。
- 在候选中考虑 relation satisfaction 和 overlap penalty。
- 用 collision-gated variant 控制 mesh pair rate。

创新价值：

- 从“硬推到满足关系”升级为“满足关系且尽量不破坏场景几何”。
- 能解释为什么 benchmark 提升很多但真实 mesh 渲染一开始不好：原始 repair 混淆了垂直轴和地面轴，导致家具高度被错误修改。

### 5. 评估拆解：parser、layout、mesh、visual diagnostics 分层

我们不只报一个 relation accuracy，而是拆成：

- 原始 InstructScene layout relation accuracy。
- direct y-fixed repair。
- floor-prior repair。
- collision-gated repair。
- multi-seed stability。
- mesh-level FCL collision pair rate。
- y-height movement diagnostics。
- real mesh visual diagnostics。
- strong baseline feasibility。

创新价值：

- 让贡献更像一篇严谨的系统/方法论文，而不是单指标刷分。
- 能明确说明哪些 claim 被支持，哪些还不能说。

## 相关工作定位

### 直接 baseline：InstructScene

InstructScene 是我们的直接对比对象。它使用 instruction-driven scene graph 和 layout generation 生成 3D indoor scenes。我们的实验复用其官方 validation split 和 checkpoint，只改变 relation-aware post-processing。

论文中应写：

- InstructScene 是 direct same-protocol baseline。
- 我们不是替换 InstructScene，而是修复其 instruction relation 在 layout realization 阶段的失真。

### Scene graph / commonsense 相关：CommonScenes

CommonScenes 使用 scene graph diffusion 生成 commonsense 3D indoor scenes，是 scene-graph-conditioned generation 方向的重要相关工作。

但它不是我们的直接 baseline：

- 输入协议不同。
- 不是同一个 text-instruction validation protocol。
- 远端已有 repo，但未完成同协议运行。

论文中应作为 related work，而不是 claim outperform。

### Text-driven / structured scene representation：ReSpace

ReSpace 是非常强的相关方法，支持 text-driven indoor scene synthesis/editing，使用 structured scene representation、specialized spatial reasoning model 和 geometry violation metric。

当前状态：

- 远端已 clone ReSpace repo。
- 但没有 HuggingFace token，官方 released model 访问未验证。
- 需要 SSR-3DFRONT 协议、vLLM、单独环境和数据 cache。
- 与当前 InstructScene validation prompts 不同协议。

论文中应写：

- ReSpace 是 close related system。
- 当前没有 fair same-split result。
- 不 claim outperform ReSpace。

### Semantic dependency / constraint optimization：SDGScenes

SDGScenes 与我们的 broad idea 很接近：它使用 Semantic Dependency Graph、VLM-derived constraints 和 nonlinear constrained optimization 处理 object placement。

风险：

- 不能说我们是 first relation-aware。
- 不能说我们第一个把 user intent 转成 placement constraints。

差异化写法：

- 我们不是提出完整新 generator，而是针对 existing InstructScene pipeline 的 graph-to-layout grounding gap。
- 我们使用原 InstructScene benchmark，不构建新 benchmark。
- 我们强调 verifier-repair layer 和 final realized relation evaluation。

### Layout / indoor scene synthesis 背景

可放在 related work 中的背景方法：

- ATISS：autoregressive transformer indoor scene synthesis。
- SceneFormer：transformer-based scene synthesis。
- DiffuScene：diffusion-based indoor scene generation。
- LayoutGPT / Holodeck：language-driven layout planning 或 3D environment generation。

这些方法构成背景，不是当前同协议强 baseline。

## 我们的方法

### 输入与输出

输入：

- InstructScene 生成的 layout boxes。
- 原始 text instruction。
- 物体类别、translation、size、rotation。
- 可选 3D-FUTURE mesh，用于 FCL collision evaluation。

输出：

- repaired layout。
- relation satisfaction metrics。
- mesh collision diagnostics。
- per-scene repair evidence。
- before/after visualizations。

### Step 1：显式关系解析

我们从 instruction 中解析显式空间关系，例如：

- left of / right of
- in front of / behind
- close left / close right
- near / far 等 explicit spatial phrases

当前 parser 是规则式 parser。它不是完美语言理解模块，但实验显示即使 parser 不完美，也能提供足够结构信号，让 verifier-repair 提升最终 layout relation。

需要诚实说明：

- 当前主要处理 explicit spatial relation。
- 不能 claim implicit commonsense relation。

### Step 2：关系验证

对每个 selected relation triple，系统在生成 layout 中寻找对应类别物体，并基于 x/z floor-plane 几何判断关系是否成立。

关键修复：

- 早期版本把垂直轴处理错了。
- 当前代码确认：该 InstructScene 坐标系中 `y` 是高度轴，`x/z` 是地面平面。
- pair selection 和 repair movement 都使用 x/z。
- repair 不改变 y。

### Step 3：direct y-fixed repair

direct y-fixed repair 直接沿 x/z 平面移动对象，使关系更容易满足，同时保持 y 高度不变。

优点：

- relation gain 最大。

缺点：

- 平均移动幅度较大。
- 部分房间 mesh pair rate 轻微上升。
- 因此不适合作为最终 paper-facing 主方法。

### Step 4：floor-prior repair

floor-prior repair 是当前主方法版本。

核心策略：

- 候选移动只发生在 x/z 平面。
- `max_repair_move` 控制最大移动范围。
- 多个 candidate alpha 中选择关系满足且 overlap 更好的候选。
- 保持 y 不变。
- 用 mesh collision 和 movement diagnostics 约束 claim。

推荐主配置：

- `floor_prior_max1.8_mesh_p2_close0.75_far1.6`

### Step 5：collision-gated verifier

collision-gated variant 会比较 repair 前后 FCL mesh collision pairs：

- 如果 repaired scene 的 collision pairs 不增加，则保留 repaired layout。
- 如果 collision pairs 增加，则 fallback 到 baseline layout。

论文中必须说明：

- 这是 verifier-selection / fallback layer。
- 它不是纯 generator 本身自动学会了 collision-free synthesis。

## 实验设置

### 数据与 benchmark

使用现有 InstructScene validation splits：

- Bedroom
- Living room
- Dining room

使用官方 checkpoint：

- Bedroom：epoch 1999
- Living room：epoch 1459
- Dining room：epoch 1239

没有构建新 benchmark。

### 主要评价指标

- Baseline relation accuracy
- Repair relation accuracy
- Relation gain
- Average repair movement
- Mesh collision pair rate
- Collision-gated relation accuracy
- y_changed_rate
- Visual diagnostics：CLIP delta、SSIM、mesh pair delta

## 实验结果

### 1. Main relation result：floor-prior 有稳定提升

| Room | Baseline acc | Floor-prior repair acc | Gain | Avg movement | Mesh pair delta |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8408 | +0.1020 | 0.7837 | +0.0029 |
| Dining room | 0.5948 | 0.7286 | +0.1338 | 0.7315 | +0.0008 |
| Living room | 0.5510 | 0.6939 | +0.1429 | 0.8808 | +0.0008 |

解释：

- 三个房间都显著提升 explicit relation satisfaction。
- 直接 repair 提升更大，但移动更激进；floor-prior 是更适合论文主方法的折中。
- 未 gated 的 floor-prior mesh pair delta 仍有轻微正值，所以 mesh claim 应以 gated 结果为准。

### 2. Direct y-fixed baseline：提升大但不够稳

| Room | Baseline acc | Direct y-fixed acc | Gain | Avg movement | Mesh pair delta |
|---|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8735 | +0.1347 | 2.2101 | +0.0034 |
| Dining room | 0.5948 | 0.7844 | +0.1896 | 1.9694 | +0.0019 |
| Living room | 0.5510 | 0.7483 | +0.1973 | 2.2834 | +0.0004 |

解释：

- direct y-fixed 是强 internal baseline。
- 说明 relation repair 本身有效。
- 但移动幅度约 2m 左右，比 floor-prior 大很多。
- 因此 direct y-fixed 更适合放 ablation，而不是主方法。

### 3. Conservative max_move ablation：max0.8 更稳但收益较低

| Room | Baseline acc | max0.8 repair acc | Gain | Avg movement |
|---|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.7959 | +0.0571 | 0.4233 |
| Dining room | 0.5948 | 0.6729 | +0.0781 | 0.3881 |
| Living room | 0.5510 | 0.6156 | +0.0646 | 0.3797 |

解释：

- `max_move=0.8` 几何扰动更小。
- 但 relation gain 明显下降。
- `max_move=1.8` 更适合作为主配置，`max0.8` 可作为 conservative ablation。

### 4. Collision-gated result：mesh claim 的核心证据

| Room | Baseline acc | Repair acc | Gated acc | Gated gain | Baseline mesh pair rate | Gated mesh pair rate | Fallback scenes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bedroom | 0.7388 | 0.8408 | 0.8163 | +0.0776 | 0.0702 | 0.0683 | 6 |
| Dining room | 0.5948 | 0.7286 | 0.6729 | +0.0781 | 0.0342 | 0.0336 | 15 |
| Living room | 0.5510 | 0.6939 | 0.6395 | +0.0884 | 0.0313 | 0.0310 | 14 |

解释：

- collision-gated 后，relation gain 仍然为正。
- gated mesh pair rate 低于 baseline。
- 这支持更安全的 claim：在控制 mesh collision 不增加的情况下，仍能提升显式关系满足率。

### 5. Multi-seed 稳定性

floor-prior `max1.8` 三个 seed 的 repair gain：

| Room | N | Mean repair gain | Std |
|---|---:|---:|---:|
| Bedroom | 3 | +0.1061 | 0.0058 |
| Dining room | 3 | +0.1462 | 0.0093 |
| Living room | 3 | +0.1270 | 0.0125 |

collision-gated 后：

| Room | N | Mean gated gain | Std | Mean gated mesh delta |
|---|---:|---:|---:|---:|
| Bedroom | 3 | +0.0803 | 0.0069 | -0.0020 |
| Dining room | 3 | +0.0867 | 0.0098 | -0.0008 |
| Living room | 3 | +0.0703 | 0.0153 | -0.0003 |

解释：

- 多 seed 下 relation gain 稳定为正。
- gated 后 mesh delta 平均为负，说明不是单 seed 偶然现象。

### 6. Height / support diagnostic

`floor_prior_support_movement_diagnostics.csv` 显示：

- 所有主结果 `y_changed_rate = 0.0`
- `max_abs_y_delta = 0.0`

解释：

- 当前 repair 不再改变高度轴。
- 可以支撑“解决家具腾空问题”的 claim。
- 但这不等于完整 support/contact reasoning，不能说解决所有物理支撑问题。

### 7. Per-relation breakdown

`floor_prior_per_relation_breakdown.csv` 共 319 行，按 room、variant、relation 拆分。

用途：

- 可用于 appendix 展示哪些 relation 类型提升最大。
- 可用于定位方法边界：显式 left/right/front/behind 更适合当前方法，隐式 commonsense relation 不在当前 claim 范围内。

### 8. Visual diagnostics：新 floor-prior 展示更适合论文

真实 3D-FUTURE mesh showcase 结果：

| Showcase | Examples | Mean relation gain | Mean mesh-pair delta | Mean CLIP delta | Mean SSIM |
|---|---:|---:|---:|---:|---:|
| Old direct y-fixed showcase | 3 | +1.333 | 0.000 | -0.0165 | 0.8358 |
| New floor-prior showcase | 15 | +1.400 | -0.267 | +0.0027 | 0.9065 |

解释：

- 新 floor-prior showcase 有 15 个样例，比旧 3 个 direct 展示更可靠。
- 平均 relation gain 为正。
- mesh pair 平均下降。
- CLIP delta 略正，但幅度很小。
- SSIM 较高，说明 before/after 结构变化温和。

论文写法：

- 可以说 selected floor-prior real-mesh examples show improved relation consistency without obvious visual degradation。
- 不要说 visual quality universally improves。
- 不要把 CLIP delta 当成强视觉质量证明。

## 强 baseline 状态

| Method | 当前状态 | 是否公平可比 | 论文用法 |
|---|---|---|---|
| InstructScene | 已执行，同协议 | 公平 | 主 baseline |
| Direct y-fixed repair | 已执行 | 公平 internal ablation | 证明直接 repair 有效但副作用大 |
| Collision-gated repair | 已执行 | 公平 internal variant | 支撑 mesh-validity claim |
| ReSpace | repo 已 clone，但无同协议结果 | 暂不公平 | close related work，不能 claim 超过 |
| SDGScenes | 无可运行同 split 结果 | 暂不公平 | close related work，不能 claim 超过 |
| CommonScenes | repo 已 clone，但输入协议不同 | 非同协议 | scene-graph generation related work |

## 当前可以支持的 claim

### Strongly supported

- Relation-aware verifier-repair 能显著提升 existing InstructScene validation splits 上的 explicit spatial relation realization。
- floor-prior repair 比 direct repair 更适合作为主方法，因为移动更受控。
- collision-gated variant 可以在 mesh collision pair rate 不增加的前提下保留正 relation gain。
- 当前实现保持 y 高度不变，修复了早期家具腾空问题。
- 多 seed 结果显示提升稳定。

### Partially supported

- 视觉展示更好看：新 floor-prior showcase 确实更稳，但它只是 selected examples 和 automatic diagnostics。
- 几何更合理：FCL mesh pair rate 和 y-height 诊断支持这一点，但还不是完整物理合理性。

### Not supported

- 超过 ReSpace / SDGScenes。
- 视觉质量全面优于 baseline。
- 处理所有隐式 commonsense relation。
- first relation-aware 3D scene generation。
- 完整 mesh-level physical support / accessibility reasoning。

## 论文 storyline 建议

### 标题候选

Relation-Aware InstructScene: Verifying and Repairing Spatial Relations in Instruction-Guided 3D Indoor Scene Generation

### Abstract 逻辑

Instruction-guided 3D indoor scene generation needs faithful realization of spatial relations, not only plausible object selection. Existing scene-graph pipelines may generate symbolic relations that are lost during continuous layout decoding. We propose a training-free relation verifier-repair layer that parses explicit spatial relations, verifies final layout realization, and applies bounded floor-plane repair while preserving object height. On existing InstructScene validation splits, our method improves explicit relation satisfaction across bedroom, living-room, and dining-room scenes, and the collision-gated variant preserves positive gains while controlling FCL mesh collision pair rate.

### Introduction 逻辑

1. Text-to-3D indoor scene generation 对游戏、仿真、embodied AI 有价值。
2. 空间关系是硬约束，不是装饰性描述。
3. Scene graph 不能保证最终 layout 实现关系。
4. 我们发现并量化 InstructScene 的 graph-to-layout grounding gap。
5. 提出 training-free verifier-repair 层。
6. 在现有 benchmark 上证明有效，并诚实报告几何与视觉边界。

### Method 逻辑

1. Baseline InstructScene pipeline。
2. Explicit relation parsing。
3. Geometry verifier。
4. Direct y-fixed repair。
5. Floor-prior repair。
6. Collision-gated selection。
7. Metrics and diagnostics。

### Experiment 逻辑

1. Main relation accuracy。
2. Direct vs floor-prior ablation。
3. max_move / repair_pass / overlap weight ablation。
4. Multi-seed stability。
5. Mesh collision gated evaluation。
6. y-height diagnostics。
7. Real mesh visual showcase。
8. Strong related baseline feasibility and claim boundary。

## 已归档数据

本地归档目录：

`E:/research_worldmodel/experiment_archive/relation_aware_instructscene_20260530`

归档内容：

- `remote_eval_outputs/`：远端原始 eval JSON/TXT，170 个文件，约 318.5 MB。
- `remote_floor_prior_showcase/`：远端渲染的 floor-prior 真实 mesh 素材，46 个文件。
- `local_results/`：本地汇总表和同步结果。
- `local_visuals/`：HTML 展示页、渲染图、paper figures。
- `docs/`：论文实验报告、baseline 状态、claim 边界说明。
- `scripts/`：分析、渲染、同步、表格生成脚本。
- `ARCHIVE_README.md`、`manifest.json`、`checksums_sha256.txt`、`table_summary.csv`。

关键入口：

- `visual/floor_prior_showcase.html`
- `visual/a_conf_visual_quality.html`
- `visual/a_conf_floor_prior_results.html`
- `results/tables/floor_prior_results.csv`
- `results/tables/floor_prior_gated_results.csv`
- `results/tables/floor_prior_mesh_results.csv`
- `results/tables/visual_quality_real_mesh.csv`
- `results/tables/strong_baseline_feasibility.csv`

## 最终总结

当前工作已经具备一篇有潜力的 paper seed。最强的贡献不是“更大模型”或“新 benchmark”，而是一个针对 instruction-guided 3D indoor scene generation 的 relation realization 问题诊断与修复框架。

最值得强调的是：

- 我们发现了 graph-to-layout grounding gap。
- 我们用现有 benchmark 证明了这个 gap 可以被 training-free verifier-repair 明显缓解。
- floor-prior 和 collision-gated 版本让方法从“关系刷分”变成“关系提升且几何副作用受控”。
- 新真实 mesh showcase 让展示素材比早期版本更可信。

投稿时最安全的定位：

> A relation-consistency verifier-repair module for existing instruction-guided 3D indoor scene generators, validated on InstructScene splits with relation, mesh-collision, height-preservation, multi-seed, ablation, and visual-diagnostic evidence.

最需要继续补强的方向：

- 若要 claim SOTA，需要 ReSpace / SDGScenes 的 fair shared-protocol comparison。
- 若要 claim visual quality，需要 human study 或更正式的 perceptual evaluation。
- 若要 claim physical realism，需要 support/contact/accessibility 等更完整物理指标。
