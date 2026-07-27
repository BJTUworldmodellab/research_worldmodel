# Claude Code 指挥词：SDGScenes 强 baseline / 防御性对比实验包

你运行在 AutoDL RTX PRO 6000 / 96GB 云端实例上。你的后端模型应通过 DeepSeek Anthropic API 使用 `deepseek-v4-pro[1m]`。请把自己当成一个谨慎的论文实验工程师：先保证可复现和可审稿，再追求数字。

## 不可越界的 claim 边界

1. 只有在找到官方 SDGScenes 代码、官方数据处理流程、并且输入/输出/split/指标与本项目完全对齐时，才可以称为 “SDGScenes direct comparison”。
2. 如果官方 SDGScenes 代码不可获得或复现缺少关键细节，则实验命名为：
   - `SDGScenes-inspired strong baseline`
   - 或 `semantic-dependency-graph constrained-optimization baseline`
3. 不得写 “outperform SDGScenes / ReSpace / SOTA text-driven 3D scene generation”。
4. 本项目主 claim 仍是：在相同 InstructScene validation protocol 下，我们的 final-layout relation grounding repair 相比 official InstructScene output 提升 realized relation accuracy。

## 第一阶段：审计与留痕

先创建分支：

```bash
git checkout -b exp/sdgscenes-strong-baseline-$(date -u +%Y%m%d) || git checkout exp/sdgscenes-strong-baseline-$(date -u +%Y%m%d)
```

必须生成/更新以下文件：

- `experiments/sdgscenes_baseline/README.md`
- `experiments/sdgscenes_baseline/configs/*.yaml`
- `experiments/sdgscenes_baseline/scripts/*.sh`
- `experiments/sdgscenes_baseline/src/`
- `experiments/sdgscenes_baseline/reports/protocol_boundary.md`
- `experiments/sdgscenes_baseline/reports/run_log.md`

每次下载、复制、解压、转换数据，都要在 manifest 中记录：

- source URL 或本地来源
- license/terms
- exact command
- sha256
- byte size
- target path
- timestamp UTC
- split

大文件/受限数据不得提交到 GitHub。GitHub 只提交代码、配置、manifest、指标 CSV、日志摘要、文档。原始数据在云端磁盘/NAS/对象存储保留，并用 sha256 manifest 指向。

## 第二阶段：先找官方 SDGScenes

请先做只读检索：

1. 搜索论文、作者主页、GitHub、arXiv、ScienceDirect landing page、supplementary/code 链接。
2. 若找到官方代码：
   - pin commit hash；
   - 记录 license；
   - 按官方 README 创建隔离环境；
   - 只先跑 bedroom smoke test；
   - 输出 `reports/official_sdgscenes_feasibility.md`。
3. 若没找到：
   - 明确写 `official code not located as of <UTC date>`；
   - 进入 “SDGScenes-inspired baseline” 实现；
   - 把所有结果放入 non-direct comparison 表，不放进 direct ranking 表。

## 第三阶段：实现 SDGScenes-inspired strong baseline

目标：建立一个对审稿人有防御力的强 baseline，而不是伪装官方复现。

输入：

- 使用和 InstructScene 主实验相同的 validation split、seed、关系阈值、mesh evaluator。
- 输入应为 prompt / relation spec / official InstructScene output layout。

输出：

- object category
- translation / orientation / size
- before/after relation satisfaction
- movement
- overlap / mesh collision / OOB
- runtime
- failure reason

建议模块：

1. `relation_parser.py`
   - 读取现有项目的 parser 或 relation JSON。
   - 若存在 oracle relation annotation，则实现 `--parser oracle` 上界。
   - 若使用 LLM/VLM 解析，必须单独标注，不可与 deterministic parser 混为一谈。

2. `semantic_dependency_graph.py`
   - 节点：objects / relations / room boundary / physical constraints。
   - 边：support、near/far、left/right/front/behind、collision、boundary、optional reachability。
   - 输出 graph JSON，便于留痕。

3. `constrained_optimizer.py`
   - 使用 `scipy.optimize.minimize` 或同等透明优化器。
   - objective 至少包含：
     - relation violation penalty
     - movement penalty
     - collision/overlap penalty
     - out-of-boundary penalty
     - optional reachability / support heuristic
   - 所有权重来自 YAML config，不要硬编码在函数里。

4. `mesh_eval_adapter.py`
   - 复用本项目主 evaluator。
   - 如果只能 AABB 而不能 mesh collision，结果列名必须写成 `aabb_overlap`，不要冒充 mesh collision。

5. `run_baseline.py`
   - 支持 `--split bedroom_smoke`
   - 支持 `--split bedroom,living,dining`
   - 支持 `--config configs/sdg_strong.yaml`
   - 输出 CSV/JSONL/raw logs。

## 第四阶段：实验顺序

1. bedroom smoke test：5 到 10 个样本。
2. bedroom full。
3. living / dining full。
4. 与我们的 `floor_prior_max1.8_mesh_p2_close0.75_far1.6` 和 collision-gated variant 统一 evaluator 对齐。
5. 若任何指标/阈值/split 不一致，不得进 direct comparison table。

## 第五阶段：报告和 Notion 草稿

更新 cloud doc 草稿，包含：

- machine info：GPU、CUDA、driver、CPU、RAM、disk
- repo commit
- dataset manifest 摘要
- official SDGScenes feasibility
- direct-comparable / non-direct-comparable 分类
- smoke test 数字
- full run 数字
- failure gallery 索引
- raw log 路径和 sha256
- claim-safe wording

## 第六阶段：提交

提交前运行：

```bash
git status --short
find experiments/sdgscenes_baseline -maxdepth 3 -type f | sort
```

只提交可共享文件。不要提交：

- AutoDL 密码
- DeepSeek API key
- Notion token
- GitHub token
- 3D-FRONT / 3D-FUTURE / SSR-3DFRONT 原始数据
- 大型 mesh / render / checkpoint，除非用户明确确认 license 和 LFS/Release 策略

提交信息建议：

```bash
git add experiments/sdgscenes_baseline cloud_archive
git commit -m "Add SDGScenes defensive strong-baseline experiment package"
git push -u origin HEAD
```

最后输出一句清楚结论：这次是 official SDGScenes reproduction、官方不可复现、还是 SDGScenes-inspired baseline，并说明为什么。
