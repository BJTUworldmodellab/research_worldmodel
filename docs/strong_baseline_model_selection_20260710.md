# 强 Baseline 模型选择 - 2026-07-10

## 选择标准

强 baseline 必须满足四个条件：

1. 输入同一批物体类别和同一组目标关系三元组。
2. 输出同一格式的 3D boxes/layout。
3. 能用同一个 relation evaluator 计算语义关系满足率。
4. 不依赖 gated model 或难以复现的数据权限。

之前 Qwen/ReSpace 不适合作为主 baseline，原因不是模型弱，而是它没有被严格喂入同一组目标物体和目标关系。

## 候选方法

| 候选 | 是否适合主强 baseline | 理由 |
|---|---:|---|
| 原始 layout / no repair | 是，已有 | 同输入同 evaluator，是最基础 baseline |
| No-floor-prior relation optimizer | 是，最推荐马上做 | 同一目标关系，同一初始布局，只去掉 floor prior，可直接证明 floor-prior 是否有用 |
| Rule-based relation repair | 是，推荐 | 容易解释、可复现；审稿人能理解 |
| CommonScenes / scene graph diffusion | 潜在强模型 baseline | 输入是 scene graph，任务概念接近，但代码/数据/类别映射成本较高 |
| Graph-to-3D / scene graph VAE | 潜在强模型 baseline | 也是 graph-conditioned，但训练和数据适配成本较高 |
| InstructScene original layout decoder | 是，如果当前方法基于它 | 可作为“未加 relation-aware repair”的模型 baseline |
| ATISS / DiffuScene / SceneFormer | 不适合作主语义 baseline | 多为 room/floorplan/text-conditioned，关系多是隐式建模，不能保证同目标关系 |
| Qwen/ReSpace 直接生成 | 不适合作主 baseline | 任务不一致，只能放 failure analysis 或 appendix |

## 最推荐的主 Baseline 组合

### Baseline A: No-floor-prior relation optimizer

这是最强、最公平、最应该马上做的 baseline。

输入：

```text
layout_boxes + selected_relations
```

输出：

```text
repaired_boxes_no_floor_prior
```

优化目标：

```text
relation_hinge_loss
+ collision_penalty
+ room_bounds_penalty
+ movement_penalty
```

与当前方法唯一差别：

```text
不使用 floor prior / support prior / floor-plane heuristic
```

它能回答的问题：

```text
提升到底来自关系优化本身，还是来自 floor-prior 设计？
```

### Baseline B: Rule-based deterministic repair

对每个目标关系直接移动 subject/object 到满足 left/right/front/behind/above/below 的位置，再做简单碰撞处理。

优点：

```text
不需要训练，不依赖模型权限，逻辑清楚，审稿人容易接受。
```

它能回答的问题：

```text
我们的 learned/optimized repair 是否优于朴素规则修复？
```

### Baseline C: InstructScene no-repair / original decoder

如果当前实验本身基于 InstructScene 输出，那么原始 layout 就是最自然的模型 baseline。

它能回答的问题：

```text
在同一个生成模型输出上，加 relation-aware repair 是否带来稳定收益？
```

## 可作为补充的外部强模型

### CommonScenes

CommonScenes 是 scene graph diffusion，概念上最接近“给关系图生成 3D 场景”。适合作为外部模型 baseline，但落地成本比 A/B 高很多：需要 SG-FRONT/3D-FRONT 类别、关系和输出格式适配。

### Graph-to-3D / End-to-End Optimization of Scene Layout

这些方法也接受 scene graph 条件，理论上公平，但大概率需要重新训练或做较重的数据转换。适合写进 related work 或 future baseline，不建议作为当前最先跑的实验。

## 最终决定

主实验不再使用 Qwen/ReSpace 作为强 baseline。

接下来应该跑：

```text
1. original layout
2. rule-based repair
3. no-floor-prior relation optimizer
4. current floor-prior repair
5. floor-prior 参数消融
```

这样才是同任务、同输入、同 evaluator 的强 baseline 对比。

## 文献依据

- InstructScene: Instruction-Driven 3D Indoor Scene Synthesis with Semantic Graph Prior, 2024.
- CommonScenes: Generating Commonsense 3D Indoor Scenes with Scene Graph Diffusion, 2023.
- Graph-to-3D: End-to-End Generation and Manipulation of 3D Scenes Using Scene Graphs, 2021.
- End-to-End Optimization of Scene Layout, 2020.
- ATISS: Autoregressive Transformers for Indoor Scene Synthesis, 2021.
- DiffuScene: Denoising Diffusion Models for Generative Indoor Scene Synthesis, 2023.
