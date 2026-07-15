# When Systems Catch Fire / 点火

> 这是点火项目的首页。它先回答三个问题：这是什么、为什么存在、从哪里开始读。

点火是一套面向跨领域材料的、证据可追溯、对象类型明确、推理过程可检查、结论等级可审计的形式化机制发现与建模系统。它不是现成的统一数学理论、物理理论、万能证明器，也不是纯文学或纯哲学知识库。

If you prefer English first: this repository is an evidence-traceable, object-typed, inference-checkable and audit-graded mechanism discovery and modelling system. It is not a unified mathematical theory, physical theory or universal prover.

本项目采用 MIT License。详情见 [LICENSE](LICENSE)。

未来版本的分层许可、商业互惠和维护者可持续性方案仍处于候选阶段，尚未替换根 LICENSE。商业生产使用和项目支持入口见 [COMMERCIAL-LICENSING.md](./COMMERCIAL-LICENSING.md) 与 [SUSTAINABILITY.md](./SUSTAINABILITY.md)。

## 先从哪里进入

- 想先看全貌，请读 [人类导航页](./SUMMARY.md)。
- 想给 AI / Agent 一个机器可读入口，请读 [llms.txt](./llms.txt)。
- 想让 AI 从零背景接手，请读 [AI-START-HERE.md](./AI-START-HERE.md) 与 [AI-HANDOFF.md](./AI-HANDOFF.md)。
- 想知道当前架构与边界，请读现行权威 [ARCHITECTURE.md](./ARCHITECTURE.md)、双地基 [FOUNDATION.md](./FOUNDATION.md) 和 [版本规范](./docs/VERSIONING.md)；[旧架构路径](./docs/PROJECT-ARCHITECTURE.md) 仅为稳定兼容入口。
- 想知道怎么用，请读 [使用说明](./docs/USAGE.md)。
- 想按 Agent 方式操作，请读 [Agent 指南](./docs/AGENT-GUIDE.md)。
- 想理解 Get 笔记如何进入这套系统，请读 [得到大脑协作流程](./docs/GET-BRAIN-WORKFLOW.md)。

## 致谢

感谢提供推理、检索、编程、执行、校验和长程协作能力的 AI 系统；感谢提供问题、材料、验证、纠错、贡献与批评的人类参与者；感谢提供独立审查、红队反馈、规范约束和缺口暴露的外部治理。

外部反馈不是“攻击/防御”叙事的一部分。经验证后，它进入“缺口发现 -> 结构修正 -> 再验证”的系统输入链。上述致谢不表示任何个人、AI 系统或机构对项目全部结论背书，也不声称 AI 具有法律人格或独立 ratification 权限。

## 这套仓库在做什么

点火采用七层正式架构：L0 来源与证据、L1 受控语义命题、L2 形式对象、L3 逻辑论证、L4 数学模型与证明、L5 验证与有效性、L6 解释应用与出版。数学与逻辑互相约束；workflow、semantic、formal、logic、proof、evidence、scope、provenance、migration 九个状态轴彼此独立，任何一轴不能自动推出另一轴。

data/foundation/ 下的对象、命题、论证、来源、证据、映射、证明、验证和迁移注册表承担新架构的状态权威。统一函数总表和统一案例总表完整保留为 legacy source / compatibility view：零删除、零重编号、不得独立生长，也不得用案例或工作流收口替代数学证明、逻辑有效性或经验真实性。

## 生命共同体价值宪章

> **长瞻一宇同叩月，此心相契共今宵。**

> 点火项目以生命共同体作为最高层规范性边界，而不是外围宣言。这里的生命共同体不限于人类，也不限于地球；它包括现实存在或未来可能发现、具有生命性、主体性、感受能力、独立利益、自我维持能力或其他足以构成道德地位的存在者及其相互依存系统。
>
> 价值宪章决定什么值得做；Ψ₀ 与元协议决定怎样合理判断；Function OS 决定怎样运行；验证与现实反馈负责发现错误、修正函数和更新价值冲突。
>
> 任何局部系统的延续、效率、创新、稳定、商业化或扩张，都不得以对更大生命共同体造成不可逆、不可补偿、非自愿的重大伤害为代价。项目优先维护长期共存、持续再生、多样性、主体尊严、代际责任、风险可逆性、维护者可持续性和未来选择空间。

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

先看 [AI-START-HERE.md](./AI-START-HERE.md)、[llms.txt](./llms.txt)、[AI-HANDOFF.md](./AI-HANDOFF.md) 和 [docs/AGENT-GUIDE.md](./docs/AGENT-GUIDE.md)。这些文件会告诉你该先读什么、哪些东西不能混、哪里需要写审计。

### 如果你关心证据和反例

先看 [断言等级说明](./docs/claim_levels.md)、[反证模板](./docs/falsifiability/README.md) 和 [失败案例库](./case_failures/README.md)。

### 如果你关心正式资产

先看 [项目状态](./data/foundation/project-state.json)、[注册表清单](./data/foundation/registry-manifest.json) 和 [迁移摘要](./data/foundation/migration-summary.json)。[统一函数索引表](./统一函数总表/INDEX.md) 与 [统一案例索引表](./统一案例总表/INDEX.md) 是历史兼容入口，不是新状态权威。

## 关键参考

- [现行架构权威](./ARCHITECTURE.md)
- [数学与逻辑双地基](./FOUNDATION.md)
- [Foundation 文档入口](./docs/foundation/README.md)
- [AI 冷启动入口](./AI-START-HERE.md)
- [AI 交接契约](./AI-HANDOFF.md)
- [机器注册表状态](./data/foundation/project-state.json)
- [项目定位](./docs/project_positioning.md)
- [项目架构兼容入口](./docs/PROJECT-ARCHITECTURE.md)
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
- [Ψ₀ 历史表达（legacy source）](./docs/phi_meta_law.md)
- [两张表的写入规范](./docs/two-tables-entry-writing-standard-20260709.md)

## 说明

- 详细方法、函数定义、案例故事、反例工作流和历史路线图都保留在各自的专门页面里。
- 这页尽量只做“前言 + 导航”，避免把读者一开始就带进过多防御性说明。

## 元协议规范性审核（外部治理记录，非 canonical 改动）

- 12 个元协议均依据《生命共同体价值宪章》完成条件接受（CONDITIONAL_ACCEPTANCE）的规范性审核，外部治理记录见 [docs/governance/meta-protocol-reviews/](./docs/governance/meta-protocol-reviews/)。
- 该记录回答“协议应受到什么价值边界约束”，不等于数学形式化、经验验证、独立人类复核、治理批准或正式协议晋级；canonical 协议状态未修改，V2、V3 保留事实度量 pending。
