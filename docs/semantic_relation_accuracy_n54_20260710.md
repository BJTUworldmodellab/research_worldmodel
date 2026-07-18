# 语义关系满足率评估 - 2026-07-10

## 结论

这轮完成了语义关系满足率评估。为了公平比较，我没有直接拿 ReSpace 的 162 个输出去对齐原算法完整 162 条不同文本，而是按 ReSpace 文件名里的 scene index 匹配原算法 `per_scene` 的前 54 个目标关系，并对 3 个 seed 重复评估。因此 matched 版本中，原算法和 ReSpace 都评估同一组 `258` 条目标关系。

结果需要拆成两层理解。原算法 repaired floor-prior 在 matched 目标集合上达到 `0.849`。Qwen/ReSpace full-scene 的总体准确率为 `0.209`，但它的目标类别覆盖率只有 `0.341`；在目标类别已经同时出现的关系里，条件关系准确率是 `0.614`。Qwen/ReSpace add-only 的总体准确率为 `0.105`，类别覆盖率只有 `0.143`，但条件关系准确率是 `0.730`。

所以，上一版把 `0.209` 直接解释为“模型语义能力差”是不严谨的。更准确的说法是：当前评估把 ReSpace 输出强行对齐到原算法测试文本，主要测到了“目标类别覆盖不足/任务不对齐”，只有 `conditional_relation_acc` 才更接近“给定目标物体都存在时，关系是否摆对”。

## 方法

| 方法 | 评估口径 |
|---|---|
| 原始 baseline layout | 使用原结果 JSON 内保存的 `layout_relations` 与 `selected_relations` 精确匹配 |
| 原算法 repaired floor-prior | 使用原结果 JSON 内保存的 `repair_relations` 与 `selected_relations` 精确匹配 |
| matched n54x3 原算法 | 使用 ReSpace 的 54 个 scene index × 3 seed 的同一目标集合重复评估 |
| Qwen/ReSpace | 用文件名 scene index 匹配原目标关系；用 `prompt/desc/sampled_asset_desc` 关键词映射类别；再用中心点坐标判断 left/right/front/behind/above/below |

## 执行命令

```powershell
$py='C:\Users\14754\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$orig=(Get-ChildItem results\floor_prior_remote -File | Where-Object { $_.Name -like 'bedroom*floor_prior_max1.8_mesh_p2*.json' } | Select-Object -First 1 -ExpandProperty FullName)
& $py scripts\evaluate_semantic_relation_respace.py `
  --original-json "$orig" `
  --respace-full-dir results\respace_remote\qwen_fair_bedroom_n54_20260710_123802\full_scene `
  --respace-add-dir results\respace_remote\qwen_fair_bedroom_n54_20260710_123802\add_only `
  --out-summary-csv results\tables\semantic_relation_accuracy_n54_20260710.csv `
  --out-predicate-csv results\tables\semantic_relation_by_predicate_n54_20260710.csv `
  --out-detail-csv results\tables\semantic_relation_details_n54_20260710.csv `
  --out-json results\tables\semantic_relation_accuracy_n54_20260710.json
```

## 整体结果

| 方法 | 场景数 | 目标关系数 | 正确数 | 总体准确率 | 类别覆盖率 | 条件关系准确率 | missing class | 方向/距离错误 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 原始 baseline layout | 162 | 245 | 181 | 0.739 | 1.000 | 0.739 | - | - |
| 原算法 repaired floor-prior | 162 | 245 | 206 | 0.841 | 1.000 | 0.841 | - | - |
| 原始 baseline matched n54x3 | 162 | 258 | 198 | 0.767 | 1.000 | 0.767 | - | - |
| 原算法 repaired matched n54x3 | 162 | 258 | 219 | 0.849 | 1.000 | 0.849 | - | - |
| Qwen/ReSpace full-scene n54 | 162 | 258 | 54 | 0.209 | 0.341 | 0.614 | 170 | 34 |
| Qwen/ReSpace add-only n54 | 162 | 258 | 27 | 0.105 | 0.143 | 0.730 | 221 | 10 |

## 按谓词结果

| 方法 | above | left | front | below | right | behind |
|---|---:|---:|---:|---:|---:|---:|
| 原算法 repaired matched n54x3 | 0.833 | 0.765 | 0.929 | 1.000 | 0.773 | 0.909 |
| Qwen/ReSpace full-scene n54 | 0.056 | 0.235 | 0.262 | 0.200 | 0.182 | 0.227 |
| Qwen/ReSpace add-only n54 | 0.167 | 0.235 | 0.024 | 0.067 | 0.061 | 0.091 |

## 通俗解释

ReSpace full-scene 并不是完全不能生成卧室物体，它确实生成了床、床头柜、衣柜、灯等。问题在于：我们现在拿原算法的目标文本去评估 ReSpace，而 ReSpace 并没有被强制生成同一对目标类别。258 条目标关系中，full-scene 有 170 条失败是因为目标物体类别没有同时出现；add-only 有 221 条 missing class。

所以，这张表不能单独证明“ReSpace 模型语义能力很差”。它能证明的是：在没有严格给 ReSpace 同一批目标关系输入的情况下，ReSpace 输出与原算法测试目标不对齐。比较模型摆放关系能力时，应优先看条件关系准确率：full-scene `0.614`，add-only `0.730`，仍低于原算法 repaired `0.849`，但差距没有总体准确率看起来那么夸张。

## 可靠性限制

1. 原算法使用的是原 JSON 保存的官方关系输出；ReSpace JSON 没保存目标三元组，因此 ReSpace 只能通过透明的启发式 adapter 评估。
2. ReSpace 类别匹配依赖关键词，例如 `bed` 映射到 `double_bed`，`bookcase` 映射到 `bookshelf`。这可能低估或高估少量样本。
3. front/behind 使用全局 z 轴判断；如果某些数据集定义了局部朝向关系，这个 adapter 会有误差。
4. 因为主要失败来自 missing class，`relation_acc` 更应该叫“目标覆盖后关系满足率”或“端到端目标满足率”，不能直接等同于模型关系推理能力。

## 产物

```text
scripts/evaluate_semantic_relation_respace.py
results/tables/semantic_relation_accuracy_n54_20260710.csv
results/tables/semantic_relation_by_predicate_n54_20260710.csv
results/tables/semantic_relation_details_n54_20260710.csv
results/tables/semantic_relation_accuracy_n54_20260710.json
docs/semantic_relation_accuracy_n54_20260710.md
visual/semantic_relation_accuracy_n54_20260710.html
```
