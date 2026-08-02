# 任务 112 出版成果 accounting

## 主要人类作品

| 成果 | 路径 | 字符数 | 汉字数 | 记录/条目 | SHA-256（最终待合并版本） |
| --- | --- | ---: | ---: | ---: | --- |
| 第一卷 | `PUBLICATIONS/volumes/001-pointfire-after-one-hundred-iterations.md` | 38,775 | 30,226 | 10 个概念章节 + 开场/尾声 | `2a3668cdfe901cf0e28705906286aa061d995849e7d42535e4ca92ad0cebcb4b` |
| 研究笔记第一辑 | `PUBLICATIONS/notes/001-pointfire-research-notes.md` | 24,503 | 14,558 | 60 | `f4a3a6dd31705750ed7c3053a4cbe688aae000a7ac10bbb99cb952377a9da0a5` |
| 一页全景 | `PUBLICATIONS/what-pointfire-knows-now.md` | 5,724 | 3,175 | 20/20/20/10 = 70 | `8cd4781d87bde988cc627c16c2df5987ac28e04cd6af75af30c74b8ece105e31` |
| 百轮成果台账 | `PUBLICATIONS/hundred-iteration-achievement-ledger.md` | 44,180 | 14,560 | 80 | `b2a46a4933095810d491f6c98c7378e84de1468ddb553d9f24ec561a2bada298` |

字符数按 UTF-8 解码后的 Unicode code point 计；汉字数只计中文 Unicode 区段，不用它代表质量。第一卷超过约 30,000 汉字的最低完整作品 guard，但篇幅不是成果等级。

## 审计和审查 accounting

| 项目 | 数量/状态 | 说明 |
| --- | --- | --- |
| R0 冻结记录 | 80 | 可恢复成果/资产记录，不是 80 个独立实验 |
| 独立 claim audit | 160 | 全景 70 + 笔记核心认识 60 + 第一卷承重句 30 |
| 笔记独立性 | 60/60 | 五字段齐全；0 个与 R0 二稿整段精确重合；5 个针对性重写后保留 |
| 全景结构 | PASS | 20 支持 / 20 纠正撤回降级 / 20 未知 / 10 方向 |
| 三重独立审查发现 | 48（不去重） | 事实 15、反方 18、编辑 15 |
| 审查处置 | 22 修订、24 保留绑定、2 开放 | 精确矩阵见 `REVIEW_DISPOSITION_MATRIX.md` |
| R0 三重审查 | 不计入 112 | 只作为 intake 历史材料，不冒充本阶段独立审查 |
| evidence binders | 10 | 作为 R0 immutable evidence index；不是十项外部真理 |

## R0 材料处理

- 80 条台账记录：保留记录主体，重写输出类别、当前有效性、结论、边界、纠正/取代和 claim ceiling。
- 第一卷二稿：主要重写，未按段落复制；保留问题骨架和有界事实，新增读者入口、统计冲突、生命周期分层、修订尾声。
- 60 条研究笔记：55 条直接保留结构，N42/N47/N48/N49/N50 目标性重写；最终 60 条均进入主题化卷和 index。
- 70 项全景：保留四块结构，逐项重新检查边界、metadata-only、target absent 和 111 lifecycle 状态。
- R0 原有审查和修订清单：保存在 `r0-original/`，不作为 112 final review。

## 入口与基础设施

- 直接阅读路径：root `README.md` → `PUBLICATIONS/README.md` → 第一卷，最多 2 次点击。
- 支持文件：`PUBLICATION_MANIFEST.json`、`PUBLICATIONS/notes/index.jsonl`、最终证据地图/来源附录/术语表、一个 deterministic validator 和 R0 immutable intake。
- 没有新增网站、CMS、数据库、搜索引擎或大型应用。
- 人类作品是主体；JSONL、manifest、validator、CI/生命周期材料只承担可追溯、验证和交接责任。

## 尚未完成但没有被隐藏的义务

外部同行评议、claim-level 全文审查、统计快照统一、现实干预、复杂函数独立 oracle、苹果历史反事实、领域专家/受影响主体参与和 fresh-clone merge/terminal checks 仍需各自的证据。它们不能因为本 accounting 的产量而被标为完成，具体清单见 `UNRESOLVED_PUBLICATION_OBLIGATIONS.md`。
