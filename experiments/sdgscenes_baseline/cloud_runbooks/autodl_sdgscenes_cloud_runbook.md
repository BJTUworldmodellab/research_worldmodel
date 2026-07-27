# AutoDL 云端执行 Runbook：SDGScenes 强 baseline 对比

目标：在 AutoDL RTX PRO 6000 / 96GB 上运行 SDGScenes 相关强 baseline，对主论文的 InstructScene 同协议 claim 做防御性补强。所有结果必须可复现、可审稿、可追踪。

## 当前边界

- AutoDL：可以登录和选择 PRO6000-96G，但创建/租赁实例属于扣费动作，需要最终确认。
- DeepSeek：Claude Code 可按 DeepSeek 官方 Claude Code 配置使用 `deepseek-v4-pro[1m]`，但还需要你的 DeepSeek API Key；不要把 key 放进 GitHub/Notion/聊天明文。
- GitHub：当前 Codex 未绑定 GitHub 账号。云端建议用 `gh auth login` 设备码登录。
- Notion：当前插件未完成授权。先用 Markdown 草稿，授权后再同步到 Notion。
- SDGScenes：若找不到官方代码，不做 “官方 SDGScenes 复现” claim，只做 “SDGScenes-inspired strong baseline”。

## 1. AutoDL 实例建议配置

优先：

- GPU：`PRO6000-96G` / `NVIDIA RTX PRO 6000`
- API 规格 ID：`pro6000-p`
- GPU 数量：1
- 系统盘扩容：建议 200–500 GB
- 镜像：优先 CUDA 11.8 / PyTorch 2.x 或 Miniconda CUDA 镜像
- 长任务：必须使用 `tmux` / `screen` / JupyterLab terminal 守护进程

AutoDL API 文档显示，容器实例 Pro API 的 host 为 `https://api.autodl.com`，创建实例接口为 `/api/v1/dev/instance/pro/create`，`PRO6000-96G` 性能型对应 `pro6000-p`。实际价格和库存以创建页面为准。

## 2. 创建实例前检查

在网页或 API 创建前确认：

1. 账号已实名/可创建 Pro 实例。
2. 余额足够。
3. 页面显示 GPU 为 PRO6000-96G / 96GB。
4. 页面显示计费价格。
5. 系统盘扩容足够。
6. 镜像 CUDA/PyTorch 版本适合项目。

我不会在未再次确认的情况下点击最终租赁/创建/支付按钮。

## 3. SSH 后执行 bootstrap

把本地文件上传到 AutoDL：

```bash
scp -P <port> outputs/autodl_bootstrap_sdgscenes.sh root@<connect-host>:/root/
scp -P <port> outputs/claude_code_sdgscenes_deepseek_prompt.md root@<connect-host>:/root/
```

SSH 登录：

```bash
ssh -p <port> root@<connect-host>
```

运行：

```bash
chmod +x /root/autodl_bootstrap_sdgscenes.sh
export PROJECT_REPO="https://github.com/<owner>/<repo>.git"
export PROJECT_BRANCH="main"
export WORK_ROOT="/root/autodl-tmp/rg-sota-cloud"
bash /root/autodl_bootstrap_sdgscenes.sh
```

bootstrap 会创建：

- `/root/autodl-tmp/rg-sota-cloud/logs/`
- `/root/autodl-tmp/rg-sota-cloud/manifests/`
- `/root/autodl-tmp/rg-sota-cloud/data/raw/`
- `/root/autodl-tmp/rg-sota-cloud/runs/`
- `/root/autodl-tmp/rg-sota-cloud/notion/`
- `/root/autodl-tmp/rg-sota-cloud/.secrets/deepseek_claude.env`

## 4. DeepSeek + Claude Code

加载密钥配置：

```bash
source /root/autodl-tmp/rg-sota-cloud/.secrets/deepseek_claude.env
```

官方推荐的关键环境变量是：

```bash
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<your DeepSeek API Key>
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
export CLAUDE_CODE_EFFORT_LEVEL=max
```

进入项目：

```bash
cd /root/autodl-tmp/rg-sota-cloud/repos/project
cp /root/claude_code_sdgscenes_deepseek_prompt.md /root/autodl-tmp/rg-sota-cloud/prompts/
```

启动受保护会话：

```bash
/root/autodl-tmp/rg-sota-cloud/scripts/start_traced_session.sh sdgscenes
```

在 tmux 内：

```bash
source /root/autodl-tmp/rg-sota-cloud/.secrets/deepseek_claude.env
cd /root/autodl-tmp/rg-sota-cloud/repos/project
claude
```

然后把 `claude_code_sdgscenes_deepseek_prompt.md` 的内容交给 Claude Code 执行。若当前 Claude Code 支持非交互参数，也可以先看：

```bash
claude --help
```

## 5. GitHub 同步策略

推荐同步到 GitHub 的内容：

- 代码
- 配置
- 小型 CSV 指标
- manifest
- run log 摘要
- protocol boundary 文档
- Notion Markdown 草稿

不推荐/默认禁止同步：

- 原始 3D-FRONT / 3D-FUTURE / SSR-3DFRONT 数据
- 大型 mesh / render / checkpoint
- 任何 license 不允许再分发的数据
- 密钥、密码、token

云端登录 GitHub：

```bash
gh auth login
gh auth status
```

安全同步：

```bash
/root/autodl-tmp/rg-sota-cloud/scripts/sync_safe_artifacts_to_github.sh
```

如果你坚持把数据集同步到 GitHub，需要先确认数据 license 和 Git LFS/Release 配额；GitHub LFS 对单文件大小有计划限制，免费/Pro 为 2GB、Team 为 4GB、Enterprise Cloud 为 5GB。

## 6. Raw data 留痕规范

每个原始文件登记：

```bash
WORK_ROOT=/root/autodl-tmp/rg-sota-cloud \
/root/autodl-tmp/rg-sota-cloud/scripts/register_raw_file.sh \
  "3D-FRONT" \
  "source-url-or-local-source" \
  "license-or-terms" \
  "validation-bedroom" \
  "/root/autodl-tmp/rg-sota-cloud/data/raw/path/to/file.zip" \
  "notes"
```

每次实验保留：

- exact command
- stdout/stderr transcript
- config yaml
- git commit
- Python env freeze
- GPU info
- raw metrics CSV
- failure list
- rendered gallery index

## 7. 实验进入 direct comparison 表的条件

必须全部满足：

1. 相同 split。
2. 相同 seed。
3. 相同 relation threshold。
4. 相同 mesh evaluator。
5. 相同输入/输出语义。
6. 可复现命令和原始输出已归档。

否则只能进入 protocol comparison / feasibility 表。

## 8. 最终交付结构

云端：

```text
/root/autodl-tmp/rg-sota-cloud/
  logs/
  manifests/
  data/raw/
  data/processed/
  runs/
  artifacts/
  notion/
  prompts/
  repos/project/
```

GitHub：

```text
experiments/sdgscenes_baseline/
cloud_archive/
```

Notion：

- 云端实例配置
- SDGScenes official feasibility
- 数据集留痕摘要
- smoke/full 实验表
- direct vs non-direct comparison 判断
- failure gallery
- claim-safe wording
