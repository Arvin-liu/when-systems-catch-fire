# SUMMARY · 点火项目阅读导航

> 当前版本：PR #56 合并并完成 Q24D 收口后的 2026-07-16 main；数学与逻辑双地基七层架构继续有效，Q12-Q23 操作与建模 overlay 以及 121Q24 迭代操作法已进入当前仓库状态。

## 现行权威

- [README.md](./README.md) — 人类总入口与双前门
- [项目现状](./docs/project-current-state.md) — 版本化、可演化、非终局的当前状态描述
- [点火迭代操作法](./ITERATION.md) — 状态改变任务的远端真相、缺口、claim ceiling、同步矩阵、验证和回执方法
- [ARCHITECTURE.md](./ARCHITECTURE.md) — 现行架构唯一权威
- [FOUNDATION.md](./FOUNDATION.md) — 数学与逻辑双地基权威
- [docs/foundation/README.md](./docs/foundation/README.md) — 架构契约导航
- [data/foundation/project-state.json](./data/foundation/project-state.json) — 机器可读项目状态与动态计数
- [data/foundation/registry-manifest.json](./data/foundation/registry-manifest.json) — 注册表清单
- [docs/PROJECT-ARCHITECTURE.md](./docs/PROJECT-ARCHITECTURE.md) — 稳定兼容入口；冲突时以根 ARCHITECTURE.md 为准
- [docs/VERSIONING.md](./docs/VERSIONING.md) — 版本阶段与升级规范
- [生命共同体价值宪章](./docs/governance/life-community-value-charter.md) — 规范性价值前提
- [许可作用域](./LICENSES/README.md) — 当前分层许可权威
- [商业许可](./COMMERCIAL-LICENSING.md) 与 [可持续性政策](./SUSTAINABILITY.md)

## 当前操作与建模 overlay

- [效果推理行动平面](./docs/architecture/effectual-action-plane.md)
- [机制判断平面](./docs/architecture/mechanism-adjudication-plane.md)
- [注意力吸引子控制](./docs/architecture/attention-attractor-control-plane.md)
- [分布坍缩控制](./docs/architecture/distribution-collapse-control-plane.md)
- [压缩完整性门禁](./docs/architecture/compression-integrity-gate.md)
- [点火地图集](./docs/architecture/ignition-atlas.md)
- [Multiscale Causal Fabric](./docs/architecture/multiscale-causal-fabric.md)
- [Probabilistic System Dynamics](./docs/architecture/probabilistic-system-dynamics.md)
- [Adaptive Relational Network](./docs/architecture/adaptive-relational-network.md)

## 七层正式架构

- L0：来源与证据
- L1：受控语义命题
- L2：形式对象
- L3：逻辑论证
- L4：数学模型与证明
- L5：验证与有效性
- L6：解释、应用与出版

L6 只能引用 L0-L5，不能反向制造数学真实性、逻辑有效性或经验真实性。数学与逻辑双地基见 [FOUNDATION.md](./FOUNDATION.md)。

### L6 公共表达与反馈能力

- [之元写作法](./docs/publication/zhiyuan-writing-method.md) — 当前 `0.3.0` L6 公共表达与 provenance-gated 反馈能力；同源不等于同一，也不增加真值层。
- [之元写作法成果](./docs/publication/zhiyuan-writing-showcase.md) — 当前人类成果总索引；每项回链作品、案例来源、点火分析与方法版本。
- [《当一支军队开始相信自己的背影》](./docs/publication/works/when-an-army-believes-its-own-back.md) — 第一项正式成果正文。
- [内部范例与反例](./docs/publication/zhiyuan-writing-examples.md) — 《永昭·虚遐》、Codex 全文核验的《每日一诗停更说明》、121Q27 基线及 0.1.0→0.3.0 自我修订史。
- [后台规格](./templates/publication/zhiyuan-writing-spec.md) — 记录项目来源、同源对应边界、生成运动和返回点火反馈；不得原样变成正文提纲。

## 核心系统历史与兼容资料

- [Ψ₀ 历史数学表达](./docs/phi_meta_law.md) — legacy source；不独立证明 Ψ₀ 是数学函数
- [旧元协议阶段说明](./docs/meta-protocols/version-iteration-note-20260709.md) — 历史版本材料
- [核心系统重新定性报告](./reports/foundation-architecture/core-system-reclassification-20260712.md)

## 元协议与设计空间

12 元协议默认是规范、启发或治理协议；64 组合是设计与生成空间，不是数学公理或证明空间。

- [元协议导航](./docs/meta-protocols/README.md)
- [12 个元协议](./docs/meta-protocols/12-meta-protocols.md)
- [64 组合矩阵](./docs/meta-protocols/meta-protocol-64-combination-matrix.md)
- [22 个书籍案例候选](./docs/meta-protocols/book-validation-22-cases-20260709.md)
- [规范性审核](./docs/governance/meta-protocol-reviews/12-meta-protocol-normative-review.md)
- [跨协议红队](./docs/governance/meta-protocol-reviews/cross-protocol-red-team.md)
- [事实 pending 总表](./docs/governance/meta-protocol-reviews/factual-pending-register.md)

## 新权威注册表

- [形式对象](./data/foundation/formal-objects/objects.jsonl)
- [命题](./data/foundation/claims/claims.jsonl)
- [论证](./data/foundation/arguments/arguments.jsonl)
- [来源](./data/foundation/sources/sources.jsonl)
- [案例与证据](./data/foundation/evidence/evidence.jsonl)
- [对象—证据映射](./data/foundation/mappings/object-evidence-mappings.jsonl)
- [证明](./data/foundation/proofs/proof-artifacts.jsonl)
- [验证](./data/foundation/validations/validation-records.jsonl)
- [迁移](./data/foundation/migrations/legacy-assets.jsonl)

## 旧两张表兼容入口

- [统一函数总表](./统一函数总表/INDEX.md)
- [统一案例总表](./统一案例总表/INDEX.md)
- [生成兼容视图](./views/README.md)

旧表是 legacy source / compatibility view：零删除、零重编号、不得独立生长，计数以机器生成的 project-state 和 migration-summary 为准。

## 模板、数据与历史审计

- [模板目录](./templates/)
- [元协议机器数据](./data/meta-protocols/README.md)
- [书籍碰撞候选](./outputs/book-collisions/20260709-22-book-validation/book-case-candidates.md)
- [历史审计目录](./outputs/audit/)
- [076 架构报告](./reports/foundation-architecture/)

## Agent 使用入口

- [llms.txt](./llms.txt)
- [Agent 指南](./docs/AGENT-GUIDE.md)
- [得到大脑协作流程](./docs/GET-BRAIN-WORKFLOW.md)
- [使用说明](./docs/USAGE.md)
