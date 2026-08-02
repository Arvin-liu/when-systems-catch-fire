# Chapter 09 Evidence Binder：从研究基础设施走向研究机构

## 章节核心问题

当研究系统拥有注册表、传播图、来源链、候选架构和出版层，它是不是已经成为一个研究机构？本章要区分“让研究可持续的基础设施”与“能够独立产生领域知识的机构”，并回答点火还需要哪些人与制度。

## 可支持的认识

1. Q24/Q25 把冷启动、远端真相、candidate/current/merged、claim ceiling、传播和同步义务纳入操作流程。
2. Q32/Q32I 说明实质机制候选、仓库依赖和同步义务可以用不同类型传播，并在局部范围选择性物化、缓存和回滚。
3. Q30/Q31 将人类索引、机器注册、形式化工作、来源链、分析、双源材料池和 system map 组织成出版展示层。
4. 之元写作法 0.4.0 提供 embodied anchor、垂直/水平移动、retro-illumination 和反馈材料的表达方法。
5. `README.md` 的当前定位把点火描述为版本化、可审计的跨域研究/行动基础设施，并明确它不是完成的普遍理论。
6. 研究机构化需要把外部领域专家、领域证据、开放审查、复制、维护者责任和读者反馈纳入，不仅是增加机器层。

## 不可支持的强说法

* 不能说同步链完整就等于研究机构已经拥有外部权威。
* 不能说一个 map/registry 自动替代专家、实验室、档案馆或同行评议。
* 不能说写作法提高了科学真理等级。
* 不能说任务流程越多，研究结论就越可靠。
* 不能说当前点火已代表所有跨域研究者或公共知识。

## 来源与提交

* `reports/operations/121Q24-current-state-reconciliation.md`、`121Q25B-project-sync-contract.md`。
* `reports/operations/121Q30-publication-showcase.md`、`121Q31-system-map.md`。
* `reports/operations/121Q32-typed-propagation.md`、`121Q32I-selective-materialization.md`。
* `docs/publication/zhiyuan-writing-method.md`。
* `README.md`、`RESULTS/RESEARCH-AND-ARTICLES.md`。
* 所有来源以固定基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b` 为出版基线。

## 相互冲突的历史版本

|旧想象|当前收紧|
|---|---|
|一套命令就是研究机构|命令只保证操作链的一部分|
|零 residue 就是未知依赖为零|只在声明 seeds/path/surfaces 范围内成立|
|公共页面可达就是权威|页面是展示面，来源/提交/运行/人类审查分开|
|一卷文章可以替代审计|文章必须带来源、边界和审查|

## 关键数字

* Q32：48 seeds、2 iterations、19 components、15 paths、16 surfaces、zero residue；它们是一次局部运行的记录。
* Q31：9 groups、41 nodes、37 edges；是系统地图的 schema 规模，不是现实系统的全貌。
* Q32I：116/116 aggregate local tests；只说明定义的本地阶段。
* 出版素材包含 10 篇 editorial articles、1 篇 publication work、1 个案例来源记录和 1 个长篇 Jin-rise 分析；数量不代表真理。

## 反例

* 传播图可以遗漏未声明依赖，zero residue 不能发现不存在于 seeds 的未知边。
* 一个有来源链接的文章可以在正文里仍然过度推断。
* 一个读者喜欢的叙述可能只是表达有效，不是机制有效。

## 开放问题

* 如何让领域专家和非仓库读者共同参与 adjudication？
* 研究机构的最低外部责任是来源核验、开放数据、复制、反方审查还是别的组合？
* 如何让维护、出版、证据和研究决策不由同一条自动链互相证明？
* 如何衡量读者的理解改善，而不把反馈循环成证据？

## Claim ceiling

本章支持“点火已经有研究基础设施和出版/同步制度的雏形”，可到 `workflow_passed`、`current_state_synchronized` 和 `publication_surface_ready` 的局部层。它不支持机构权威、领域代表性、因果研究能力或同行评议替代。

## 可进入正文的材料

用“研究机构像一座有账本、走廊和门禁的房子”作比喻，但马上说明房子不是实验室，账本不是事实。写 Q32 的传播和 Q30 的出版分层，让读者看到机构化首先意味着责任、可追溯和允许反驳，而不是更多术语。

## 只能放附录的工程信息

edge type、seed 数、graph component、cache、rollback、schema、目录结构、commit/PR 约束和 status machine 放附录。正文只解释它们解决的读者/研究者问题。

