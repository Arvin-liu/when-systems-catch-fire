# 知识体验入口与探索层

状态：任务 102 候选，只有普通合并、`main` 精确验证和全新克隆复验后才成为 Current 仓库能力。

## 要解决的缺口

任务 101 建立了仓库 Markdown 人类阅读层、历史结果台账和机器/人类双输出门禁，但读者仍要知道文件路径、结果页名称或资产编号。台账按文件类别排列，不能直接回答“最近改变了什么”“这个主题有哪些结论”“旧称后来怎样修正”或“谁依赖这项结论”。

本层把现有来源、函数身份卡和非函数断言 registry 投影为统一入口。它不新增真值层，不重新裁决资产，也不把摘要、搜索命中或图关系升级为证明、外部证据、现实因果或同构。

## 人类入口

- `KNOWLEDGE/README.md`：无需预知路径的统一起点；
- `WHATS-NEW.md`：按知识变化而非 commit 排列的时间线；
- `MAP.md`：按研究问题和主题组织的知识地图；
- `ASSET-CARDS.md`：结果/文章、重点函数和重点断言的统一卡片；
- `READING-LAYERS.md`：每份恢复来源的 1 分钟、5 分钟和完整阅读；
- `SEARCH.md` 与主题索引：标题、自然语言词、旧称和 ID 的全量检索入口；
- `EVOLUTION.md`：撤回、纠正、旧称和 supersession；
- `COVERAGE.md`：当前、人类重点、机器-only、中间材料、撤回与缺失来源的覆盖审计。

重要内容不使用默认折叠容器。README 到上述核心入口均不超过两次点击。

## 机器合同

`data/governance/knowledge-experience/config.json` 声明主题、重点资产、历史别名、时间线变化和 canonical 页面。生成器读取任务 101 的 result ledger、任务 99 的 function identity cards 和任务 100 的 non-function claim registry，确定性生成：

知识体验层、任务 101 自我纠错输出、人类结果时间线、任务 99/100 注册表输出与迁移汇总，都是 canonical 输入的派生投影。函数发现器仍直接读取正式对象和人工纠正输入，非函数发现器仍显式导入 canonical claims；语料扫描本身排除这些生成路径，避免“生成结果再次成为上游发现源”的循环回灌。回归测试同时约束该边界。

- `changes.jsonl`；
- `asset-cards.jsonl`；
- `layered-reading.jsonl`；
- `search-index.jsonl`；
- `alias-index.jsonl`；
- `coverage.json` 与 `manifest.json`。

全量搜索索引与详细资产卡按固定上限分片；CI 会阻断任何达到 500 KB 的人类 Markdown 页面，保证普通 GitHub 文件视图仍可渲染。机器 JSONL 不受该展示预算限制。

`manifest.json` 锁定四个 authoritative 输入摘要、每个生成输出摘要、计数和机器/人类配对。生成物不得手工漂移。

`KNOWLEDGE/` 与 `data/governance/knowledge-experience/` 是由既有来源和 registry 派生的投影，函数 census 与非函数断言 discovery 显式排除它们，防止“registry → 搜索页 → 被当成新资产 → registry 膨胀”的循环登记。原始来源、生成器代码和非生成治理文档仍进入各自现行扫描范围；投影本身由任务 102 validator 与自我纠错规则审计。

## 资产重要性与全量覆盖

每份恢复的研究、文章、复算、审计、架构与 Foundation 来源都获得统一卡片和三层阅读。函数重点卡覆盖任务 98 明确纠偏的 T2、D127、D182—D190、D260。断言重点卡只记录具名回弹谱系与当前公共表面中的高风险断言；历史不可能性结论保持撤回，跨域、因果、预测、定理和经验条目保持各自现行上限，不因被收录而恢复或升级。

其余函数和断言不被删除：它们进入全量搜索索引，继续回链 canonical machine registry。重点卡 materiality policy 只控制人类详细卡片，不代表未入选资产不重要或已被否定。

## 分层摘要边界

1 分钟层使用来源台账摘要和原有局限字段；5 分钟层从来源标题、段落和列表确定性恢复最多六个要点；完整层始终回到原文件。三层均保存来源 SHA-256。自动摘要不得改变 M/E、final disposition、claim ceiling、supersession 或公开上限；冲突时以完整来源和现行裁决为准。

## 未来变更门禁

任何有意义的新结论、纠正、文章、实验、审计或资产变化必须同时声明：

1. 人类目的地；
2. What's New 条目；
3. 知识地图主题；
4. 统一资产卡；
5. 需要时的三层阅读；
6. 标题、自然语言别名、历史旧称和 supersession；
7. 来源、依赖、反向依赖和证据谱系；
8. 当前状态与不得推出的结论。

CI 会阻断缺失或过期的人类/机器配对、断链/断锚、孤儿卡片、无来源摘要、缺少长文层级、缺少别名替代、撤回结论回弹、隐藏重要内容、Pages 残留和生成漂移。

## 断言上限

本层只能建立 repository navigation、source-faithful summary 和 governance projection。它不能证明任何数学、物理、经验、因果、价值或生命周期结论。
