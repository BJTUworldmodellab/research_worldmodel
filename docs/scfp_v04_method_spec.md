# SCFP v0.4 方法规范

**日期：** 2026-07-29  
**状态：** 草案 / 预注册候选  
**目标：** 为当前主线寻找比 Collision-gated Floor-Prior 更强、但仍可审计的后处理主方法。

> SCFP = Safety-Certified Feasible Projection。
> 这一版的核心变化不是再做更复杂的 proposal 规则，而是把“可行域”本身定义清楚：
> 先把 Floor-Prior 作为 anchor，再只在严格可行域内做数值投影。

## 1. 一句话定义

SCFP v0.4 是一个 training-free 的布局后处理器：它把 Collision-gated Floor-Prior 当作 anchor 和 fallback，把候选生成器降级为数值初始化器，然后在一个统一的可行域里做词典序投影，优先提高关系覆盖，其次压低违反量，再保证 exact OBB、movement 和 edit 代价不退化。

## 2. 为什么要有这一版

前一轮探索已经说明：

- 只修一个局部几何公式，通常只能改变少量记录的选择；
- 继续在已见 531 records 上调参，不会把方法变成可投稿的主方法；
- 真正缺的不是更多启发式，而是一个能被审稿人理解和检查的“统一可行域”。

因此，SCFP v0.4 不再把方法贡献定义为“更聪明的 nudging”，而定义为“更严格的安全投影”。

## 3. 方法边界

SCFP v0.4 只做以下事情：

1. 以 Collision-gated Floor-Prior 布局 \(X^F\) 作为 anchor；
2. 对原始布局 \(X^0\) 和关系提议 \(R\) 做数值初始化；
3. 在统一可行域内优化一个布局候选；
4. 如果没有候选比 anchor 更好，就返回 anchor 本身。

SCFP v0.4 不做以下事情：

- 不重新训练生成器；
- 不引入房型专属规则；
- 不做 relation-specific edit set；
- 不把 evaluator 放进优化循环；
- 不在已见 531 records 上继续调参并声称验证。

## 4. 输入、输出与 anchor

### 输入

- 原始布局 \(X^0\)；
- 关系集合 \(R\)；
- Floor-Prior / Collision-gated Floor-Prior 布局 \(X^F\)；
- 房间边界、对象尺寸、对象类别、朝向；
- 固定的预算、阈值和随机种子。

### 输出

- 修复布局 \(X^\star\)；
- 或者在没有严格改进时输出 \(X^F\)；
- 以及一份可复现证书，记录输入哈希、配置哈希、commit、seed 和门控结果。

### Anchor 语义

Floor-Prior 不再只是比较基线，而是：

- 可行解 anchor；
- 数值初始化的起点；
- 无改进时的回退结果。

这保证了方法的默认行为是保守的。

## 5. 统一可行域

SCFP v0.4 的可行域不是单一阈值，而是以下约束的交集。

### 5.1 movement 与 edit 约束

- 总移动量不超过冻结上限；
- 单物体移动量不超过冻结上限；
- 被编辑对象数不超过冻结 edit cap。

这些约束用于阻止“靠更大位移换提升”。

### 5.2 previously satisfied relation preservation

对 anchor 已满足的关系，SCFP v0.4 不允许候选把它们破坏掉。

这条约束的优先级高于继续挪动对象来追求局部覆盖。

### 5.3 exact OBB non-regression

候选不得增加：

- exact OBB collision pairs；
- exact OBB overlap area。

这里的 OBB 是硬门控，不是 soft regularizer。

### 5.4 boundary constraint

房间边界是可选硬门控：

- 当有可信边界时，候选必须满足边界；
- 当边界不可信时，协议必须 fail closed，而不是偷偷放松阈值。

### 5.5 external safety fail-closed

如果启用外部安全检查，例如远程 FCL，则它和本地几何门控必须合取：

- 任一检查失败，候选直接失败；
- 不允许外部 callback 覆盖本地门控；
- 不允许缓存结果绕过重算。

## 6. 候选生成：只允许数值初始化

SCFP v0.4 不把候选生成看成算法核心，而看成数值初始化。

允许的初始化器只包括：

- Floor-anchored residual projection；
- 保守的随机残差扰动；
- 受约束的连续求解器 warm start。

不允许的初始化器包括：

- relation-specific edit sets；
- room-specific heuristics；
- 多 proposal 拼接式 nudging；
- 依赖 evaluator 反馈的闭环搜索。

这一步的目标不是“更聪明地产生更多候选”，而是“把所有候选投影到同一条可解释轨道上”。

## 7. 词典序目标

候选在可行域内按以下顺序排序：

1. coverage；
2. weighted violation；
3. exact OBB 代价；
4. movement；
5. edit count。

解释如下：

- coverage 先于一切，因为如果覆盖不足，后续代价都没有意义；
- weighted violation 只在 coverage 同级时比较；
- exact OBB 优先于 movement，因为安全非退化比“少动一点”更重要；
- movement 优先于 edit count，因为 edit count 只是在 tie-break 中进一步约束稀疏性。

如果某个候选没有比 anchor 更好的最优前缀，anchor 直接胜出。

## 8. 主方法行为

SCFP v0.4 的决策规则是：

1. 生成一组数值初始化的候选；
2. 把每个候选投影到统一可行域；
3. 只保留严格可行的候选；
4. 按词典序选择最优候选；
5. 如果没有严格改进，返回 Floor-Prior anchor。

这意味着 SCFP v0.4 不是“总能修改布局”的方法，而是“只在能严格改进时修改”的方法。

## 9. 实施门槛

SCFP v0.4 只有在下面这些实现门全部满足时，才允许进入任何正式结果目录：

- 配置文件冻结；
- 输入 manifest 冻结；
- evaluator 版本冻结；
- 代码 commit 冻结；
- 证书包含输入哈希、配置哈希和 commit；
- 任一失败都必须回退到 anchor；
- 任何 NaN / Inf 都视为失败。

## 10. 论文晋级门槛

SCFP v0.4 只有在以下门都通过后，才能考虑替代当前主方法：

1. 新 confirmatory cohort 与当前已见 500 source clusters 零重叠；
2. 独立 evaluator 完成冻结，并通过 human audit；
3. 所有被接受候选完成 remote FCL 重算；
4. 在 confirmatory cohort 上相对 Collision-gated Floor-Prior 的 pooled 提升为正，且 95% CI 下界 > 0；
5. 三个房型的点估计都为正；
6. movement ratio 在冻结区间内；
7. exact OBB 和 external safety 均不劣；
8. 不再依赖已见 531 records 的调参结果来宣称验证。

如果任何一条不满足，SCFP v0.4 只能作为探索性候选或失败分析，不能作为论文默认主方法。

## 11. 允许的论文表述

如果未来晋级成功，论文可以写成：

> SCFP is a safety-certified feasible projection layer that uses Collision-gated Floor-Prior as a conservative anchor and improves relation coverage only when it can do so without degrading exact OBB or external safety checks.

在晋级之前，只能写“proposed design”或“exploratory candidate”，不能写“demonstrated improvement”。

## 12. 当前结论

SCFP v0.4 是下一步值得做的优化方向，但它现在还是规范，不是已验证结果。

它解决的是“怎样把方法做得可审计、可冻结、可复核”，而不是“怎样在同一批已见数据上继续挤出一点分数”。
