# When Systems Catch Fire / 点火

《点火》不是一本固定成书，而是一个开放维护的函数、案例、发现与预测知识库。
When Systems Catch Fire is not a fixed book, but an open and maintained knowledge base of functions, cases, discoveries, and predictions.

## 入口 / Entrance

<!-- REPOSITORY_OVERVIEW_START -->
| 区域 / Area | 当前数量 / Current Count | 说明 / Description |
| --- | ---: | --- |
| [发现 / Discoveries](DISCOVERIES.md) | 0 curated discoveries, 83 leads | 从函数、案例与自举循环中产生的新发现。 / New discoveries generated from bootstrap cycles between functions and cases. |
| [预测 / Predictions](PREDICTIONS.md) | 8 predictions, 8 inconclusive novelty | 由函数、案例、发现与自举循环推出的可检验未来判断。 / Testable future judgments derived from functions, cases, discoveries, and bootstrap cycles. |
| [新答案 / New Answers](ANSWERS.md) | 0 answers, 12 leads, 12 inconclusive novelty | 对既有问题、经典问题、未解问题或已有答案的新回答。 / New answers to existing, classic, unresolved, or previously answered questions. |
| [函数表 / Functions](FUNCTIONS.md) | 1 meta-function, 5 bootstrap items, 470 ordinary functions | 函数、机制、结构与公式。 / Functions, mechanisms, structures, and formulas. |
| [案例表 / Cases](CASES.md) | 578 cases | 案例、证据、历史对象与验证材料。 / Cases, evidence, historical objects, and verification materials. |
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
