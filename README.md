# When Systems Catch Fire / 点火

<!-- PROJECT_POSITIONING_LOCK_START -->

一个人类在好奇心的驱动下，借助 AI 做出的发现。
A discovery made by a human being, driven by curiosity and aided by AI.
<!-- PROJECT_POSITIONING_LOCK_END -->

<!-- PROJECT_EVALUATION_OUTPUT_LOCK_START -->

这是一个人类在好奇心的驱动下，借助 AI 做出的发现。
<!-- PROJECT_EVALUATION_OUTPUT_LOCK_END -->

一个人类在好奇心的驱动下，借助 AI 做出的发现。 

A discovery made by a human being, driven by curiosity and aided by AI.

## 入口 / Entrance

<!-- REPOSITORY_OVERVIEW_START -->
| 表 / Table | 当前状态 / Current Status | 看哪里 / Path | 说明 / Description |
| --- | --- | --- | --- |
| 函数总表 / Functions | 已更新至 D515（D476-D515）；普通函数 515 条 | [FUNCTIONS.md](FUNCTIONS.md) | 点火函数、机制、结构与公式 |
| 案例总表 / Cases | 已更新至 C-0654（C-0595-C-0654）；案例 654 个 | [CASES.md](CASES.md) | 点火案例、证据、历史对象与验证材料 |
| 发现表 / Discoveries | 发现投影集合已建立：55 个函数 | [DISCOVERIES.md](DISCOVERIES.md) / [DISCOVERY_PROJECTION_SETS.md](DISCOVERY_PROJECTION_SETS.md) | 从函数表与案例表交叉自举发现中投影出的发现集合 |
| 预测表 / Predictions | 预测投影集合已建立：31 个函数 | [PREDICTIONS.md](PREDICTIONS.md) | 从函数表与案例表交叉自举发现中投影出的预测集合 |
| 新答案表 / New Answers | 新答案投影集合已建立：30 个函数 | [ANSWERS.md](ANSWERS.md) | 从函数表与案例表交叉自举发现中投影出的新答案集合 |
| 解析解表 / Analytic Solutions | 解析解投影集合已建立：1 个函数；当前确认 SOL-0001 | [ANALYTIC_SOLUTIONS.md](ANALYTIC_SOLUTIONS.md) | 点火内部解析解条目分类 |
<!-- REPOSITORY_OVERVIEW_END -->

## Current Structure / 当前结构

| Layer | 中文说明 | 主要文件 / Files |
| --- | --- | --- |
| Functions | 点火函数层，保存第 0 节元函数与 D-X 普通函数及其结构化字段 | `data/functions/meta-functions.json`, `data/functions/meta-functions.jsonl`, `data/functions/meta-functions-index.md`, `data/functions/unified-functions.json`, `data/functions/unified-functions.jsonl`, `data/functions/items/` |
| Cases | 案例层，保存案例与函数关系 | `data/cases/unified-cases.json`, `data/cases/unified-cases.jsonl`, `data/cases/items/` |
| Discoveries | 新发现说明层，面向人类阅读和传播 | `DISCOVERIES.md`, `data/discoveries/unified-discoveries.json`, `data/discoveries/unified-discoveries.jsonl`, `docs/zh/discoveries/items/` |
| Predictions | 预测说明层，面向人类阅读和验证 | `PREDICTIONS.md`, `data/predictions/unified-predictions.json`, `data/predictions/unified-predictions.jsonl`, `docs/zh/predictions/items/` |
| Registry | 原始统一总表，作为生成 JSON 的来源 | `data/registry/统一函数总表.csv`, `data/registry/统一案例总表.csv` |
| Legacy Book | 旧书籍结构，保留为历史材料 | `archive/book-legacy/` |
| Raw Notes | 原始笔记与来源材料，不作为 canonical item | `dianhuo/originals/` |

## For AI Agents / 给 AI Agent

1. Read `llms.txt`.
2. Read `AGENT_ENTRY.md`.
3. Use `data/functions/meta-functions.jsonl` for Section 0 meta-function lookup.
4. Use `data/functions/unified-functions.jsonl` for ordinary function lookup.
5. Use `data/cases/unified-cases.jsonl` for case lookup.
6. Use `data/discoveries/unified-discoveries.jsonl` for structured discovery entries.
7. Use `data/predictions/unified-predictions.jsonl` for structured prediction entries.
8. Use `data/functions/items/*.json` and `data/cases/items/*.json` as canonical machine-readable records.

Do not treat raw notes as canonical. Raw notes are sources. Current structured entries live under `data/functions/`, `data/cases/`, `data/discoveries/`, and `data/predictions/`.

## Projection Sets / 投影集合

投影集合是从统一函数总表中抽取出符合某类发现性质的函数子集。

此集合源于函数表与案例表交叉自举发现。投影集合不是学术新颖性声明，也不包含外部学术检索结论。外部检索可由读者或后续研究者自行进行。

- [投影集合入口 / Projection Sets](DISCOVERY_PROJECTION_SETS.md)
- 机器数据: `data/projection-sets/discovery-projection-sets.jsonl`
- 解析解数量报告: `data/projection-sets/analytic-solution-count-report.md`
- 交叉引用表: `data/projection-sets/projection-set-crosswalk.md`
- 构建报告: `data/reports/build-projection-sets-report.md`

## Human Reading / 人类阅读入口

- 中文函数入口 / Chinese functions: `FUNCTIONS.md`, `docs/zh/functions.md`
- 中文案例入口 / Chinese cases: `CASES.md`, `docs/zh/cases.md`
- 中文发现入口 / Chinese discoveries: `DISCOVERIES.md`, `docs/zh/discoveries/items/`
- 中文预测入口 / Chinese predictions: `PREDICTIONS.md`, `docs/zh/predictions/items/`
## Data Policy / 数据原则

- JSON item files are canonical machine-readable records.
- JSONL indexes are batch-readable entry points for AI agents, scripts, and search.
- CSV indexes are human-readable tables generated from item files.
- Markdown pages are human-facing explanations and navigation.
- `candidate` does not mean `fact_checked`.
- Missing fields are represented as `null` or `[]`; absence of a field must not be interpreted as evidence.

## Build And Validate / 构建与验证

```bash
python3 tools/build-function-items.py
python3 tools/build-case-items.py
python3 tools/build-indexes.py
python3 tools/validate-knowledge-base.py
```

## Attribution And License / 署名与协议

Discoverer / maintainer: 之元

Repository: https://github.com/Arvin-liu/when-systems-catch-fire

Unless otherwise noted, the knowledge-base content is licensed under Creative Commons Attribution-NonCommercial 4.0 International (`CC-BY-NC-4.0`). Reuse, redistribution, and adaptation require attribution to 之元 and the repository URL. Commercial use is not permitted without separate permission.
