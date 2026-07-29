# SCFP v0.4 × Eurographics 2027 统一投稿任务清单

> 更新日期：2026-07-29
>
> 清单版本：`2026-07-29-b-submission-overlay-v1`
>
> 目标：Eurographics 2027 Full Papers / Computer Graphics Forum（CCF-B）
>
> 摘要截止：2026-09-25 23:59 UTC
>
> 全文截止：2026-10-01 23:59 UTC
>
> 官方投稿系统：[Eurographics 2027 Full Papers](https://srmv2.eg.org/COMFy/Conference/EG_2027)
>
> 当前投稿状态：**NO-GO**
>
> 当前论文主方法：**Collision-gated Floor-Prior**
>
> 条件晋级候选：**SCFP v0.4 — Safety-Certified Feasible Projection**

本文件把既有投稿任务、最新 SCFP v0.4 方法协议和投稿工程任务合并为一份
版本化执行清单。旧任务文档保留为历史记录；本文件提交远端后，任务状态以
本文件为主，方法身份以 `configs/paper_main.yaml` 为准，算法契约以
`configs/scfp_v04_protocol.yaml` 为准。

本文件同时冻结一层**比 SCFP 基础协议更严格的 B 会证据 overlay**：
confirmatory cohort 至少 500 个新 source clusters / 700 条关系、主方法提升
至少 +1.5 pp、20,000 次 source-cluster bootstrap、movement ratio ≤ 1.05，
且至少选择一个非 anchor 候选。这些阈值继承自
`configs/cwgcp_v03_protocol.yaml` 的 paper-main gates 和既有 B 会任务，
只允许加严，不允许放松。任何修改都必须在查看新 cohort 结果前发布新的
overlay version、commit 和 hash；否则 SCFP 自动 NO-GO。

## 1. 当前决策与执行原则

### 1.1 双轨执行

1. **投稿主线：** 不等待算法继续调参。以 Collision-gated Floor-Prior 为
   默认主方法，优先关闭独立 evaluator、公平控制、统计、论文和 artifact。
2. **SCFP 快速晋级线：** SCFP 已完成实现和合成性质验证，但尚无论文晋级
   证据。只有全部晋级门通过，才允许替换默认主方法。
3. **截止规则：** `configs/paper_main.yaml` 已冻结方法升级截止为
   **2026-08-01**。截止时任一 SCFP 晋级门未通过，投稿主线自动保留
   Floor-Prior；SCFP 降为 exploratory method、消融或 future work。
4. **禁止事后延长：** 如确需延长方法升级截止，必须先提交版本化协议，说明
   新截止、资源、风险和对论文计划的影响；不得看完新结果后再改门槛。

### 1.2 状态定义

- `DONE`：所有验收项都有可检查证据。
- `IN PROGRESS`：已有产物，但至少一项验收未通过。
- `PARTIAL`：只完成了任务的一部分，或现有结果与最终协议尚未对齐。
- `TODO`：尚未开始或没有可检查产物。
- `BLOCKED`：依赖项或外部资源未满足。
- `OPTIONAL`：删除相应 claim 后可裁剪，不阻塞投稿。

“代码已写”“实验已启动”或“论文已描述”均不等于 `DONE`。

### 1.3 建议责任分工

- **A — 方法与评测：** M-01、M-02、M-05、M-08；
- **B — 数据、实验与远程安全：** M-03、M-04、M-06、M-07、E-01、E-02；
- **C — 论文与 artifact：** E-03、E-04、P-01~P-04、R-01、S-01~S-03；
- **D — 独立审计：** 人工标注仲裁、R-02 两轮内审、最终双人提交复核。

实际姓名由项目负责人填写；D 不应由主要方法实现者单独承担。

## 2. 已完成基础

| ID | 状态 | 已完成事项 | 验收证据 |
|---|---|---|---|
| F-01 | DONE | 冻结 SCFP v0.4 方法定义与协议 | `docs/scfp_v04_method_spec.md`、`configs/scfp_v04_protocol.yaml` |
| F-02 | DONE | 实现 certified feasible selection、anchor identity projection、严格 relation dominance 和 fail-closed 逻辑 | 冻结提交 `adf5ef54cc7c90706c6121b1bd2a770a051d856c` |
| F-03 | DONE | 加入 aggregate 与 pairwise exact OBB contact monotonicity | 无新 collision pair；已有 pair overlap 不允许增加 |
| F-04 | DONE | 输出 constraint residuals、proof obligations、hash/provenance 字段 | SCFP certificate contract tests |
| F-05 | DONE | 保持论文默认方法不变 | `default_main_method: collision_gated_floor_prior` |
| F-06 | DONE | 本地回归验证 | `python -m pytest -q`：49 passed；`yaml.safe_load` 解析两份配置；`git diff --check` 通过 |
| F-07 | PARTIAL | 小型无调参 smoke 验证 | 3 个房间各 1 个场景，但产物仅在临时目录且未形成持久 manifest；不作为论文证据 |

这些完成项只证明 SCFP 的**实现契约和安全回退逻辑**，不证明它在新数据上
优于 Floor-Prior。

## 3. 总任务看板

| ID | 优先级 | 状态 | 任务 | 目标 | 主要交付物 | 最晚完成 | 依赖 |
|---|---|---|---|---|---|---|---|
| M-01 | P0 | IN PROGRESS | 统一方法身份与证据链 | 消除 Floor-Prior、Direct Repair 和历史候选的数字混用 | variant manifest、claim-to-table map、结果哈希 | 2026-07-31 | 无 |
| M-02 | P0 | TODO | 冻结独立 evaluator 与人审协议 | 避免优化器自评估和事后改阈值 | protocol、标注表、抽样 manifest | 2026-07-31 | M-01 |
| M-03 | P0 | TODO | 冻结 SCFP confirmatory cohort | 获得与已见数据零重叠的新证据 | cohort manifest、overlap audit、hash | 2026-07-31 | M-02 |
| M-04 | P0 | BLOCKED | 建立 per-candidate remote FCL 链路 | 让 mesh collision claim 有真实证据 | FCL runner、receipt、逐候选结果 | 2026-07-31 | 远程环境、M-03 |
| M-05 | P0 | TODO | 实现并审计独立 evaluator | 生成独立的主关系指标 | evaluator、tests、scene-level CSV、人审报告 | 07-31（晋级）/ 08-06（投稿） | M-02 |
| M-06 | P0 | PARTIAL | 冻结并实现同预算强控制 | 排除“移动本身”或“任意 optimizer”解释 | random、generic optimizer、oracle 配置与脚本 | 07-31（晋级）/ 08-10（投稿） | M-01、M-05 |
| M-07 | P0 | BLOCKED | SCFP one-shot confirmatory run | 在冻结新 cohort 上决定是否晋级 | manifest、summary、paired CSV、certificates | 2026-08-01 | M-03~M-06 |
| M-08 | P0 | BLOCKED | SCFP 晋级 GO/NO-GO | 形成不可歧义的主方法决策 | 一页 decision record、冻结 commit/config | 2026-08-01 | M-07 |
| E-01 | P0 | TODO | 最终主方法冻结重跑 | 从同一提交生成全部论文主数字 | 全量结果、日志、manifest、自动表格 | 2026-08-15 | M-01、M-05、M-06、M-08 |
| E-02 | P0 | TODO | 配对统计与不确定性分析 | 证明主增益不是抽样噪声 | bootstrap 脚本、CI/效应量表 | 2026-08-18 | E-01 |
| E-03 | P0 | IN PROGRESS | 关闭 claim-to-evidence 映射 | 让每个论文 claim 可追溯 | reviewed claim map、数字一致性检查 | 2026-08-22 | E-01、E-02 |
| E-04 | P1 | TODO | 失败模式、边界与负结果分析 | 主动回答适用范围和失败原因 | taxonomy、数量、案例、limitations | 2026-08-22 | E-01 |
| P-01 | P1 | TODO | 重写方法、实验和 limitations | 论文叙述只使用最终方法与证据 | 更新后的主文和 supplementary | 2026-08-27 | M-08、E-01~E-04 |
| P-02 | P1 | TODO | 冻结主表、Pareto 图和案例图 | 以最少图表支撑全部核心 claim | 自动主表、矢量图、figure manifest | 2026-08-27 | E-02~E-04 |
| P-03 | P1 | BLOCKED | 迁移 Eurographics 官方模板 | 形成合规的双盲 PDF | 官方模板源文件、PDF、编译日志 | 2026-08-31 | 官方模板、P-01 |
| P-04 | P1 | TODO | 相关工作与引用核验 | 准确划清与 ReSpace、SDGScenes 等工作的边界 | citation audit、更新后的 related work | 2026-09-05 | P-01 |
| R-01 | P0 | TODO | 匿名 artifact 与干净环境复现 | 让未参与开发者复现至少一张核心表 | 匿名包、环境文件、一键脚本、复现记录 | 2026-09-10 | E-01、P-02 |
| R-02 | P0 | TODO | 两轮独立内部审稿 | 关闭技术、claim、复现和写作风险 | review reports、response table、修订 PDF | 2026-09-15 | P-01~P-04、R-01 |
| S-01 | P0 | TODO | 冻结标题、摘要、作者与材料 | 提前锁定提交系统必填信息 | frozen metadata、材料清单 | 2026-09-24 | R-02 |
| S-02 | P0 | TODO | 完成摘要注册 | 保存 paper ID 和成功回执 | 系统记录、时间戳回执 | 2026-09-24 | S-01 |
| S-03 | P0 | TODO | 完成全文与附件提交 | 提交可审、可打开、可追溯的最终包 | PDF、supplement、artifact、回执 | 2026-10-01 | S-02 |

## 4. P0 详细任务与验收标准

### M-01 — 统一方法身份与证据链

**目标：** 所有核心数字都能从方法名追溯到 variant、配置、结果和提交。

**交付物：**

- 唯一主方法 manifest；
- reviewed `docs/method_variant_matrix.md`；
- reviewed `docs/claim_to_table_map.md`；
- 自动数字一致性检查；
- 主表原始 CSV 和 SHA256。

**验收清单：**

- [ ] `Collision-gated Floor-Prior` 行只使用对应的 frozen Floor-Prior 结果；
- [ ] collision-gated Direct Repair 只作为消融，不再误标为 Floor-Prior；
- [ ] SCFP、FA-PSP、AGRP、CW-GCP 的开发结果不混入最终主方法行；
- [ ] `docs/method_variant_matrix.md` 加入 SCFP 的 candidate role、允许 claim、
      禁止 claim 和 promotion status；
- [ ] 每个核心数字记录 method ID、evaluator version、movement 定义、seed、
      config hash、input hash 和 commit；
- [ ] 主文、supplement、Markdown 表、LaTeX 表和 CSV 数字一致；
- [ ] 一致性脚本退出码为 0，`git diff --check` 无错误。

**NO-GO：** 任一主结果无法追溯，或不同方法/评测口径仍被混写。

### M-02 — 冻结独立 evaluator 与人审协议

**目标：** 在看最终结果前固定评测规则。

**交付物：**

- `evaluation/independent_protocol.md`；
- evaluator version/hash；
- 分层抽样 manifest 和双人标注表；
- 冲突处理、缺失对象和多实例规则。

**验收清单：**

- [ ] evaluator 不 import 修复器的 relation predicate、candidate score 或
      acceptance logic；
- [ ] 冻结 relation 定义、距离/方向阈值、对象匹配和分母规则；
- [ ] 预声明人审至少 90 条关系，覆盖 bedroom、dining room、living room 和
      主要谓词；
- [ ] 预声明双人标注、方法身份盲化和 Cohen's kappa ≥ 0.70 的通过门槛；
- [ ] 预声明 kappa 不达标时修订协议并重新标注的处理规则；
- [ ] protocol、样本和 evaluator 均记录 hash，并在 one-shot 前冻结。

**NO-GO：** 使用优化器内部 surrogate 作为唯一主指标，或协议在看结果后改动。

### M-03 — 冻结零重叠 confirmatory cohort

**目标：** 彻底隔离已见 531 records / 500 source clusters 的调参信息。

**交付物：**

- `configs/scfp_v04_seen_source_manifest.json`；
- 新 cohort input manifest；
- source UID、normalized instruction、source graph/content hash overlap audit；
- 房型和谓词分布报告。

**验收清单：**

- [ ] 以 `scripts/run_cwgcp_pilot.py` 的 `CANONICAL_PATTERN` 匹配到的三房间
      full canonical JSON 为源，并用 `configs/cwgcp_v031_input_manifest.json`
      的 `inputs` 数组核对路径和 SHA256；
- [ ] 生成 seen-source manifest 时读取上述 JSON 的全部 531 records，
      **不得应用** `cwgcp_v031_input_manifest.json` 的 `split.name: dev` 过滤；
- [ ] seen-source manifest 恰含 dev 209 + locked 291 = 500 个 unique source
      clusters，并为每个 cluster 记录 source UID、normalized-instruction hash
      和 source-graph/content hash；
- [ ] 记录 manifest 生成脚本、输入 SHA256、规范化规则和输出 SHA256；
- [ ] 至少 500 个新的 unique source clusters；
- [ ] 至少 700 条 target relations，三房间近似均衡；
- [ ] 与已见 500 clusters 的 source UID 交集为 0；
- [ ] normalized instruction 交集为 0；
- [ ] source graph/content hash 交集为 0；
- [ ] 在首次运行前冻结 input manifest 和 SHA256；
- [ ] 任何结果后算法修改都必须换新的 confirmatory cohort。

**NO-GO：** 把现有 531 records 的任意切分重新命名为 untouched validation。

### M-04 — 建立 per-candidate remote FCL 链路

**目标：** 对 SCFP 新候选重新计算真实 mesh collision，而不是复用 anchor 缓存。

**交付物：**

- 远程 FCL 环境 manifest；
- 每个 selected candidate 的输入 hash、mesh hash、命令、日志和 receipt；
- candidate 与 anchor 的 collision pair 对照表。

**验收清单：**

- [ ] 用至少一个真实 changed layout 和对应 anchor 完成端到端 FCL smoke；
- [ ] 缓存只允许在 provenance 完全匹配时使用，不能把 anchor 结果复制给 candidate；
- [ ] FCL 不可用、报错或 receipt 不匹配时 fail closed；
- [ ] receipt schema 能记录 input、mesh、commit、environment 和 command hash；
- [ ] one-shot 时每个 selected candidate 的结果可从 receipt 复核；
- [ ] OBB 只能标为 oriented-footprint proxy，不能代替 mesh FCL。

**NO-GO：** 任一被接受新候选缺少 fresh FCL 结果。

### M-05 — 实现并审计独立 evaluator

**目标：** 让论文主关系指标独立于优化器实现。

**交付物：**

- 独立 evaluator 和单元测试；
- `results/independent_eval/per_scene.csv`；
- `results/independent_eval/summary.csv`；
- 人审一致性报告。

**验收清单：**

- [ ] 与优化器只共享数据格式，不共享 relation 判定实现；
- [ ] 覆盖边界距离、旋转对象、缺失对象、重复实例和冲突关系测试；
- [ ] 对同一输入重复运行结果完全一致；
- [ ] 每行包含 scene/source cluster、分子、分母、失败原因和 evaluator version；
- [ ] 完成至少 90 条关系的分层双人标注，Cohen's kappa ≥ 0.70；
- [ ] evaluator 在冻结人审集上通过 M-02 预声明的准确性/错误率门槛；
- [ ] 同一 evaluator 用于 baseline、Floor-Prior、SCFP 和控制方法。

### M-06 — 补齐同预算强控制

**目标：** 排除任意移动和通用优化器对增益的解释。

**交付物：**

- movement-matched random baseline；
- same-budget generic optimizer；
- oracle-parser diagnostic upper bound；
- 统一 scene/source-cluster paired table。

**验收清单：**

- [ ] 所有方法使用同一 cohort、关系输入、独立 evaluator、编辑数和位移预算；
- [ ] random 使用 seeds `0, 1, 2`；
- [ ] movement-matching 逻辑有单元测试和固定样本 smoke；
- [ ] generic optimizer 不读取额外标签或 evaluator 反馈；
- [ ] oracle 只替换 relation source，并明确标为非部署上界；
- [ ] 所有控制的 config、seed、命令和输出 schema 在 one-shot 前冻结。

### M-07 / M-08 — SCFP one-shot 与晋级决策

**目标：** 只运行一次冻结协议，并作不可歧义的 GO/NO-GO。

**运行前冻结：**

- [ ] SCFP code commit；
- [ ] `configs/scfp_v04_protocol.yaml`；
- [ ] input manifest；
- [ ] evaluator version；
- [ ] FCL environment/receipt schema；
- [ ] SCFP、Floor-Prior 和控制方法的 fixed method seeds 均为 `0, 1, 2`；
- [ ] 统计方法和所有阈值。

**必需输出：**

- `summary.json`；
- `summary.md`；
- `paired_scene_metrics.csv`；
- `certificates.jsonl`；
- SCFP、Floor-Prior 和控制方法的 per-seed metrics 与 pooled paired metrics；
- 20,000 次 source-cluster paired bootstrap；
- 一页 promotion decision record。

**SCFP 晋级必须同时满足：**

- [ ] confirmatory cohort 相对 Floor-Prior 的独立 evaluator 提升 ≥ +1.5 pp；
- [ ] pooled paired 95% CI 下界严格 > 0；
- [ ] bedroom、dining room、living room 点估计全部 > 0；
- [ ] movement-matched random 与 SCFP 的平均移动差异 ≤ 5%；
- [ ] 相对 movement-matched random 的 95% CI 下界 > 0；
- [ ] 若 generic optimizer 等价或更好，主动降低算法 novelty claim；
- [ ] mean movement ≤ 1.05 × Floor-Prior；若超过，只能在预注册的
      candidate-movement-matched Pareto control 支持下另行评估；
- [ ] 每个场景 exact OBB collision pairs 和 total overlap non-worse；
- [ ] 无新 OBB collision pair，无已有 pair overlap 增加；
- [ ] fresh remote FCL 对所有 selected candidates non-worse；
- [ ] 至少一个新候选被选中，SCFP 不是全量 anchor identity；
- [ ] 证书 100% 可解析，无 NaN/Inf，hash/provenance/receipt 完整；
- [ ] 人审门通过；
- [ ] 没有看结果后改参数、挑房型或替换 evaluator。

**决策：**

- 全部通过：`GO`，发布 versioned `paper_main.yaml`，将 SCFP 设为唯一主方法，
  随后从 E-01 重新生成全部论文证据。
- 任一失败：`NO-GO`，保持 Collision-gated Floor-Prior；SCFP 只能作为
  exploratory/ablation/failure analysis，不再占用投稿关键路径。

### E-01 / E-02 — 最终冻结重跑与统计

**目标：** 无论最终选择 Floor-Prior 还是 SCFP，都只保留一条提交证据链。

**验收清单：**

- [ ] 531 个 InstructScene 场景完整：bedroom 162、living room 192、
      dining room 177；
- [ ] 无重复、缺失、NaN、Inf、静默跳过或未声明回退；
- [ ] 所有运行记录 commit、config、input、evaluator、seed、环境和耗时；
- [ ] CommonScenes 339 scenes 只作为跨生成器诊断，官方指标与 generic metric
      分开报告；
- [ ] 若最终主方法为 Floor-Prior，历史 cached FCL 只有在 layout、mesh、
      FCL config 和 provenance receipt 全部精确匹配时才可使用，否则 fresh rerun；
- [ ] 若最终主方法为 SCFP，所有 selected new candidates 必须 fresh FCL；
- [ ] 所有主表由脚本从最终结果自动生成，不手改数字；
- [ ] 通用主分析至少 5,000 次 scene/source-cluster paired bootstrap；
- [ ] 报告总体和分房间 point estimate、95% CI、effect size、样本数；
- [ ] 主 claim 相对 frozen generator 和 movement-matched random 的
      95% CI 下界均 > 0；
- [ ] 多重比较、缺失值和失败处理规则预先冻结。

### R-01 / R-02 — Artifact 与内部审稿

**验收清单：**

- [ ] 干净环境一条命令运行最小示例；
- [ ] 干净环境一条命令重建至少一张核心表；
- [ ] 未参与开发者不经口头指导完成 smoke reproduction；
- [ ] 不含密钥、用户名、私人路径、内部服务器地址、作者身份或未授权数据；
- [ ] 主稿和 supplementary 双盲；
- [ ] 第一轮覆盖 novelty、技术正确性、实验公平性和复现；
- [ ] 第二轮由未参与主要写作的人完成；
- [ ] 所有 Major issue 均被修复、降级 claim 或写入明确限制；
- [ ] 内部推荐达到 Weak Accept 或更高。

## 5. 论文 Claim 边界

### 5.1 当前允许

- training-free final-layout constraint projection；
- bounded XZ floor-plane edits；
- explicit class-level spatial-relation repair；
- Collision-gated Floor-Prior 是当前论文主方法；
- SCFP 是 implementation-complete、safety-certified exploratory candidate；
- exact OBB 是 XZ oriented-footprint proxy；
- SCFP 无严格改善时返回可认证的 Floor-Prior anchor。

### 5.2 晋级前禁止

- SCFP 已在 untouched cohort 上证明优于 Floor-Prior；
- mesh-safe，而没有每个新候选的 fresh remote FCL；
- true room-boundary、support-aware、walkability-aware，而没有相应输入/证书；
- mention-level instance grounding，而没有实例级标注；
- human-perceived visual quality 更好，而没有人类偏好实验；
- outperform ReSpace/SDGScenes，而没有 same-protocol 公平复现；
- CommonScenes official score improvement；
- state of the art、全局最优、解决所有语言约束或通用 world model。

如果不完成 human visual-preference study，就删除视觉偏好 claim；该研究不再是
投稿硬门槛。

## 6. 四个放行门

### Gate M — 方法冻结门（2026-08-01）

**GO：**

- M-01、M-02 完成；
- 默认主方法唯一；
- 如果 M-03~M-08 未全部通过，明确冻结 Floor-Prior 并停止 SCFP 晋级；
- 所有后续实验只允许修 bug，不允许追结果调参。

**当前状态：NO-GO。**

### Gate E — 证据门（2026-08-22）

**GO：**

- M-05、M-06、E-01、E-02、E-03 完成；
- 独立 evaluator 下总体增益 95% CI 下界 > 0；
- 优于 movement-matched random；
- mesh FCL 不恶化；Floor-Prior 允许使用精确匹配且可审计的 frozen receipt，
  SCFP 新候选必须 fresh recomputation；
- 所有最终数字来自同一冻结提交。

**当前状态：NO-GO。**

### Gate P — 论文与复现门（2026-09-15）

**GO：**

- P-01~P-04、R-01、R-02 完成；
- 官方模板合规、双盲、页数合规；
- 所有 claim 有证据；
- 干净环境独立复现通过；
- 无未关闭 Major issue。

**当前状态：NO-GO。**

### Gate S — 提交门（2026-10-01）

**GO：**

- S-01~S-03 完成；
- 2026-09-24 前完成摘要表单首次提交；
- 最终 PDF、supplement、artifact 均可打开且与冻结 manifest 对应；
- 至少两人下载并复核系统中的最终文件；
- 保存 paper ID、摘要回执和全文回执。

**当前状态：NO-GO。**

## 7. 关键路径与时间安排

### 2026-07-29 至 2026-08-01

- [ ] 关闭 M-01、M-02；
- [ ] 尝试关闭 M-03、M-04；资源不具备时立即记录 blocker；
- [ ] 按 M-08 作方法决策；
- [ ] 默认动作：保持 Floor-Prior，停止在已见 531 records 上继续调 SCFP。

### 2026-08-02 至 2026-08-15

- [ ] 完成 M-05、M-06；
- [ ] 从冻结主方法执行 E-01；
- [ ] 自动生成主表原始数据。

### 2026-08-16 至 2026-08-31

- [ ] 完成 E-02~E-04；
- [ ] 完成 P-01、P-02；
- [ ] 迁移官方模板；
- [ ] 冻结论文主表、Pareto 图和失败案例。

### 2026-09-01 至 2026-09-15

- [ ] 完成引用审计；
- [ ] 完成匿名 artifact 和独立复现；
- [ ] 完成两轮内部审稿；
- [ ] 关闭全部 Major issue。

### 2026-09-16 至 2026-09-24

- [ ] 冻结标题、摘要、作者顺序、关键词和材料清单；
- [ ] 双盲、页数、字体嵌入、引用和附件检查；
- [ ] 2026-09-24 前完成摘要注册首次提交并保存回执。

### 2026-09-25 至 2026-10-01

- [ ] 只修提交问题和确认过的 bug，不新增实验主线；
- [ ] 至少提前 12 小时上传最终全文；
- [ ] 双人从系统下载复核；
- [ ] 保存最终回执。

## 8. 可裁剪项与未来工作

以下任务不应拖延本次 B 会投稿：

| 优先级 | 项目 | 处理规则 |
|---|---|---|
| OPTIONAL | 人类视觉偏好 | 删除“视觉更好”claim 后可不做 |
| OPTIONAL | ReSpace 完整同协议复现 | 环境/协议不可公平对齐时只写 related-work boundary |
| OPTIONAL | 官方 SDGScenes 全量复现 | 无稳定 runnable release 时只保留 protocol discussion |
| P2 | 第三个生成器 | CommonScenes 只作有限 transfer evidence；不扩大战线 |
| P2 | true room polygon / door / window / walkability | 作为 SCFP 下一版约束输入 |
| P2 | vertical support graph / support-aware editing | 需要新标注与 3D 支撑建模 |
| P2 | 无实例关系的 object insertion | 当前方法只移动已有对象 |
| P2 | learned prior 或端到端训练 | 不进入本次投稿关键路径 |

## 9. 每日更新与 DONE 规则

每日只更新以下内容：

1. 今日关闭的 task ID；
2. 对应 commit、结果目录、manifest 或 review 证据；
3. 未通过的验收项；
4. 新 blocker、负责人和解除日期；
5. Gate M/E/P/S 当前状态。

任务只有在**所有验收复选框均有可追溯证据**时才能改为 `DONE`。任何门失败
都必须选择以下之一并记录：

1. 修复后重新验收；
2. 降级或删除对应 claim；
3. 明确 NO-GO，并切回投稿安全主线。
