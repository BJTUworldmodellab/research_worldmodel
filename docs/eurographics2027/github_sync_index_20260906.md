# Eurographics 2027 文章与实验内容同步索引

日期：2026-09-06。当前阶段：文章内容开发；作者信息和 SRMv2 投稿按作者决定暂缓。

## 主要入口

| 内容 | 文件 |
|---|---|
| 当前匿名论文，6 页 | [PDF](../../paper/eurographics2027_submission/build/EGauthorGuidelines-conf-sub.pdf) |
| 可编辑论文 | [TeX 正文](../../paper/eurographics2027_submission/EGauthorGuidelines-conf-sub.tex) · [参考文献](../../paper/eurographics2027_submission/references.bib) |
| 人类可读实验报告 | [HTML](../../artifacts/eurographics2027/eg13_validation_report/report.html)（下载后在浏览器中打开） |
| 机器可读结果 | [JSON](../../artifacts/eurographics2027/eg13_validation_report/query_results.json) · [SQLite](../../artifacts/eurographics2027/eg13_validation_report/report_source.sqlite) · [SQL](../../artifacts/eurographics2027/eg13_validation_report/report_queries.sql) |
| 匿名复现压缩包 | [ZIP](../../artifacts/eurographics2027/eg13_anonymous_repro.zip) |
| 复现说明及逐文件指纹 | [README](../../artifacts/eurographics2027/eg13_anonymous_repro/README.md) · [MANIFEST](../../artifacts/eurographics2027/eg13_anonymous_repro/MANIFEST.json) |
| EG11–EG16 交接与状态 | [交接文档](eg11_eg16_team_handoff_20260825.md) · [状态 JSON](../../results/independent_eval/eg2027/eg11_eg16_readiness_20260825/status.json) |
| SDGScenes 历史实验与文档 | [实验目录](../../experiments/sdgscenes_baseline/) |
| 协议边界说明 | [证据验证记录](paper_content_extension_validation_20260901.md) |

## 科研结果边界

正式比较使用 531 个场景、808 个目标关系。主方法 relation accuracy 为 0.639851；原始 InstructScene 为 0.634901；三个精确移动量匹配随机对照的均值为 0.625413。主方法相对随机均值提高 1.4439 个百分点，配对 95% CI 为 [0.7453, 2.2005] 个百分点。与原始 baseline 和 generic optimizer 的比较仍不显著。

SDGScenes-inspired 历史 smoke run 使用 708 个目标关系及不同指标，保留原始留痕，未并入正式 808 关系排名表。当前论文不主张超过 ReSpace 或 SDGScenes。

## 同步核验

- EG09 claims freeze、EG10 内容完整性检查通过。
- 仓库及匿名包的 evaluator smoke 和三张结果表复现通过。
- 匿名包清单内 28 个文件的 SHA-256 与字节数逐一匹配。
- 完整回归测试：20 tests，OK；Shapely 2.1.2 仅放在本地临时依赖目录。
- PDF SHA-256：`f418b82977664d40f786b8788e541b895effcfd8bcb58de89456fc91fb01157d`。
- ZIP SHA-256：`9315e98e2dd4d7035097e91561aaf1469f71da1960eb07bc3f8ebb68c1d41002`。
- [本次同步内容清单](../../manifests/eurographics2027/github_sync_manifest_20260906.json)记录本次提交的交付文件及 Git 对象指纹。

Git 同步包括文章、图表、实验结果、原始实验留痕、复现代码、报告和交接材料。本机 TeX Live、临时 Python 依赖、重复克隆与编译缓存留在本地。第三方完整数据集和模型权重仍按各自许可证与原始获取说明管理，轻量复现包已包含本文结果复算所需的布局和逐关系数据。
