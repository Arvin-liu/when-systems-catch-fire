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

## 生命共同体价值宪章

> **长瞻一宇同叩月，此心相契共今宵。**

> 点火项目以生命共同体作为总体规范性价值前提。这里的生命共同体不限于人类，也不限于地球；它包括现实存在或未来可能发现、具有生命性、主体性、感受能力、独立利益、自我维持能力或其他足以构成道德地位的存在者及其相互依存系统。
>
> 任何局部系统的延续、效率、创新、稳定或扩张，都不得以对更大生命共同体造成不可逆、不可补偿、非自愿的重大伤害为代价。项目优先维护长期共存、持续再生、多样性、主体尊严、代际责任、风险可逆性和未来选择空间。

> 本宪章是项目的规范性出发点，不是经验性证据，不替代数学证明、实验验证、案例核验、外部学科审查或治理批准。

[阅读全文：生命共同体价值宪章](docs/governance/life-community-value-charter.md)

<details>
<summary>展开十项核心原则</summary>

1. 生命共同体：价值边界不限于人类、地球或当前已知生命。
2. 反局部掠夺：局部系统不得通过伤害更大共同体实现延续或扩张。
3. 长期与再生：优先维护长期共存、再生能力和未来选择空间。
4. 整体不无限压倒个体：共同体利益不能成为无限牺牲个体的理由。
5. 非人类生命：其他生命与生态系统不应被默认视为纯工具。
6. 代际责任：当前世代不得无限向未来转嫁代价。
7. AI 审慎纳入：依据实际主体性、利益和可受损性判断其道德地位。
8. 预防原则：面对可能不可逆的重大风险，应采取审慎行动。
9. 纠错、退出与恢复：重大决策应尽量保持可逆、可复核、可退出。
10. 停止条件：损害更大生命共同体的局部系统必须受限、转型或停止。

</details>

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
- [生命共同体价值宪章](./docs/governance/life-community-value-charter.md)
- [12 元协议规范性审核矩阵（外部治理记录）](./docs/governance/meta-protocol-reviews/12-meta-protocol-normative-review.md)
- [跨协议红队结果（外部治理记录）](./docs/governance/meta-protocol-reviews/cross-protocol-red-team.md)
- [事实 pending 总表（外部治理记录）](./docs/governance/meta-protocol-reviews/factual-pending-register.md)
- [64 组合矩阵](./docs/meta-protocols/meta-protocol-64-combination-matrix.md)
- [22 个书籍验证候选](./docs/meta-protocols/book-validation-22-cases-20260709.md)
- [元协议迭代说明](./docs/meta-protocols/version-iteration-note-20260709.md)
- [Φ 元统一律完整定义](./docs/phi_meta_law.md)
- [两张表的写入规范](./docs/two-tables-entry-writing-standard-20260709.md)
- [生命共同体价值宪章](./docs/governance/life-community-value-charter.md)

## 说明

- 详细方法、函数定义、案例故事、反例工作流和历史路线图都保留在各自的专门页面里。
- 这页尽量只做“前言 + 导航”，避免把读者一开始就带进过多防御性说明。

## 元协议规范性审核（外部治理记录，非 canonical 改动）

- 12 个元协议均依据《生命共同体价值宪章》完成条件接受（CONDITIONAL_ACCEPTANCE）的规范性审核，外部治理记录见 [docs/governance/meta-protocol-reviews/](./docs/governance/meta-protocol-reviews/)。
- 该记录回答“协议应受到什么价值边界约束”，不等于数学形式化、经验验证、独立人类复核、治理批准或正式协议晋级；canonical 协议状态未修改，V2、V3 保留事实度量 pending。
