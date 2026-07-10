# When Systems Catch Fire / 点火

> 这是点火项目的首页。它先回答三个问题：这是什么、为什么存在、从哪里开始读。

点火是一个跨域结构性推论与理论生成框架。它把现象整理成函数、案例与元协议，让人和 AI 可以在同一套结构里比较、收敛、反证，并在证据不足时保留 `pending`。

If you prefer English first: this repo explores cross-domain structural inference and theory generation. It keeps the front door short and sends the detailed method to dedicated docs.

本项目采用 MIT License。详情见 [LICENSE](LICENSE)。

## 先从哪里进入

- 想先看全貌，请读 [人类导航页](./SUMMARY.md)。
- 想给 AI / Agent 一个机器可读入口，请读 [llms.txt](./llms.txt)。
- 想知道当前架构与边界，请读 [项目架构](./docs/PROJECT-ARCHITECTURE.md) 和 [版本规范](./docs/VERSIONING.md)。
- 想知道怎么用，请读 [使用说明](./docs/USAGE.md)。
- 想按 Agent 方式操作，请读 [Agent 指南](./docs/AGENT-GUIDE.md)。
- 想理解 Get 笔记如何进入这套系统，请读 [得到大脑协作流程](./docs/GET-BRAIN-WORKFLOW.md)。

## 这套仓库在做什么

点火的核心是把一个问题放进可复核的结构里：对象是什么，因果在哪里，系统如何反馈，哪些部分可以比较，分析应该停在哪一层，最后再判断结论是 `true`、`false`、`contradiction` 还是 `pending`。

当前仓库里，已经审核的正式资产放在两张表里，候选材料和理论展开放在专门的文档里。README 不再重复这些细节，只负责把入口摆清楚。

## 阅读路径

### 如果你是第一次接触

先看 [SUMMARY.md](./SUMMARY.md)，再看 [docs/USAGE.md](./docs/USAGE.md)。这两个页面能最快告诉你项目是什么，以及它适合怎么用。

### 如果你是 Agent 或研究助手

先看 [llms.txt](./llms.txt) 和 [docs/AGENT-GUIDE.md](./docs/AGENT-GUIDE.md)。这两个文件会告诉你该先读什么、哪些东西不能混、哪里需要写审计。

### 如果你关心证据和反例

先看 [断言等级说明](./docs/claim_levels.md)、[反证模板](./docs/falsifiability/README.md) 和 [失败案例库](./case_failures/README.md)。

### 如果你关心正式资产

先看 [统一函数索引表](./统一函数总表/INDEX.md) 和 [统一案例索引表](./统一案例总表/INDEX.md)。

## 关键参考

- [项目定位](./docs/project_positioning.md)
- [项目架构](./docs/PROJECT-ARCHITECTURE.md)
- [Get 笔记协作流程](./docs/GET-BRAIN-WORKFLOW.md)
- [版本规范](./docs/VERSIONING.md)
- [断言等级说明](./docs/claim_levels.md)
- [证据机制说明](./docs/evidence_regime_library.md)
- [反证模板](./docs/falsifiability/README.md)
- [失败案例库](./case_failures/README.md)
- [元协议概览](./docs/meta-protocols/README.md)
- [12 个元协议](./docs/meta-protocols/12-meta-protocols.md)
- [64 组合矩阵](./docs/meta-protocols/meta-protocol-64-combination-matrix.md)
- [22 个书籍验证候选](./docs/meta-protocols/book-validation-22-cases-20260709.md)
- [元协议迭代说明](./docs/meta-protocols/version-iteration-note-20260709.md)
- [Φ 元统一律完整定义](./docs/phi_meta_law.md)
- [两张表的写入规范](./docs/two-tables-entry-writing-standard-20260709.md)

## 说明

- 详细方法、函数定义、案例故事、反例工作流和历史路线图都保留在各自的专门页面里。
- 这页尽量只做“前言 + 导航”，避免把读者一开始就带进过多防御性说明。
