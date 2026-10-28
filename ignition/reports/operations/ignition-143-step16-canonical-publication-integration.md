# IGNITION-20260827-143 Step 16 — canonical 出版入口接入

## 结论

Step 16 通过。Task143 的出版组合已经接回正式仓库现有的唯一 `PUBLICATIONS/pointfire-results-book/` 入口，没有新建平行成果系统。

本步更新了：

- 成果册 `README.md`：增加 Task143 R1 的出版组合、三篇文章、Book Project 和两篇样章的可读入口，并明确出版生产不等于外部真值或 `EPISTEMICALLY_ACCEPTED`。
- 成果册 `CHANGELOG.md`：追加本轮阶段封存与成果生产的 append-only 记录。
- 成果册 `RESULT-REGISTRY.jsonl`：新增 6 个 public-safe 出版工作成果登记（3 篇文章、1 个 Book Project、2 个样章），各自保留 provenance、claim ceiling、未决证据和不升级的关系说明。
- `docs/editorial/README.md`：将三篇新文章接入人类阅读入口，说明 Task104 旧质量快照与 Task143 当前编辑证据的区别。
- `docs/editorial/source-manifest.json`：为三篇新文章登记 17 个实际来源路径、SHA-256、审校证据和 `REVIEWED_CURRENT` 状态；`editorial_lifecycle.py` 重新验证 13 篇文章。

成果册仍只有一个权威人类入口。文章是叙事层，`RESULT-REGISTRY.jsonl` 是可独立修订的成果登记，工程状态和开放义务仍由各自 canonical operations registry 与 Current surfaces 承担；本步没有把任何出版工作成果写成现实规律、外部接受或已解决的 executor obligation。

## 接入的成果

| registry result | 人类路径 | 当前出版含义 |
| --- | --- | --- |
| `R1-IGNITION-143-ARTICLE-A` | `docs/editorial/articles/011-terminal-task-open-obligation.md` | Task142 两只生命周期时钟的仓库内方法/系统文章 |
| `R1-IGNITION-143-ARTICLE-B` | `docs/editorial/articles/012-support-becomes-path-control.md` | D600/M3 带反例的内部候选模型文章 |
| `R1-IGNITION-143-ARTICLE-C` | `docs/editorial/articles/013-tree-canopy-temperature-causality.md` | 有界公开来源 replay 的读者价值文章 |
| `R1-IGNITION-143-BOOK-PROJECT` | `PUBLICATIONS/pointfire-results-book/14-书籍项目-R1-还没有被证明的世界.md` | 可供人工继续编辑的完整书籍项目 |
| `R1-IGNITION-143-BOOK-SAMPLE-01` | `PUBLICATIONS/pointfire-results-book/book-project-r1/01-第一章-先别急着宣布完成.md` | 成熟书稿开篇样章 |
| `R1-IGNITION-143-BOOK-SAMPLE-03` | `PUBLICATIONS/pointfire-results-book/book-project-r1/03-第三章-退出不是按钮.md` | 成熟书稿中段样章 |

## 门禁

- `editorial_lifecycle.py --repo ignition`：`EDITORIAL_OK articles=13`。
- `RESULT-REGISTRY.jsonl`：95 行均可作为 JSON 解析，新增 6 行的 `result_id` 唯一。
- 新增 canonical 链接与来源 manifest 通过 JSON、路径存在性和 `git diff --check` 检查。
- 新增 registry 的公共 provenance 只指向仓库内可公开的来源入口或 `PRIVATE_PROVENANCE_WITHHELD`；没有写入私有路径、凭据或可重建私有正文。

Step 17 将把当前状态同步收据更新到本轮 presentation-only 边界；Step 18 再运行 targeted publication/current gates 与自然完整回归。

