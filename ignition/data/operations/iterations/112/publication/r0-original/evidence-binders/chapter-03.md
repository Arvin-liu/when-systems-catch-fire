# Chapter 03 Evidence Binder：百轮迭代纠正了哪些强结论

## 章节核心问题

运行上百轮后，点火究竟变得“知道更多”，还是变得“更会收回自己说过的话”？本章追踪强结论被反例、类型门、来源审计和缺失目标改写的过程，重点不是罗列错误，而是说明纠正如何成为研究成果。

## 可支持的认识

1. 物理纠正文档撤回了“点火证明四种相互作用不可能统一”的总说法，只保留声明载体内的有限结构、零除法或商映射边界。
2. D127 与形式化 T2 被分开，D260 从旧物理绑定改为 p/(1-p) bias sensitivity score，说明同名、同形或历史命名不能决定对象身份。
3. 零门被改写成 carrier-scoped product readout，而不是所有状态/信息消失。
4. Gödel、Hodge 和跨域类比被禁止充当跨域 no-go 证明。
5. 断言注册表闭合、CI 通过、图边存在、Pages 可达分别被降回其工程或表示层。
6. 任务 104 将来源从 `INJECTED_VERIFIED` 降到 metadata-only；任务 106 修正了 18/18 coverage 的过强表述；OpenAlex 保留 7 个 null。
7. Function OS 修复了实现缺陷，但不删除原始 25 false reject；苹果案例则因为 target absent 停在历史主张审计。

## 不可支持的强说法

* 不能说纠正史证明了所有当前断言正确。
* 不能说撤回物理 no-go 就证明真实统一可行。
* 不能说一次降级说明所有外部来源都没有价值。
* 不能说 Function OS 修复后“不再有失败”。
* 不能说苹果案例已被否定为虚构，或已被程序复现。

## 来源与提交

* `RESULTS/CORRECTIONS.md` — 基线 `9b15d359c54694d851c38df6ab3c7ae42544a51b`。
* `docs/foundation/physics-asset-correction-20260729.md` — 关键物理边界，历史提交 `23f4702a0`。
* `reports/external-research/104-source-quality-audit.md`、`104-dual-088-reconciliation.md` — 任务 104，基线包含。
* `reports/external-research/106-105-evidence-correction-report.md` — 任务 106。
* `function-os-candidate/v0.2/benchmark` 与 `data/operations/iterations/111` — 固定基线中的失败与边界证据。

## 相互冲突的历史版本

|旧版本|纠正触发|当前版本|
|---|---|---|
|普遍物理不可能性|有限载体反例和 Foundation gate|有限模型结果；真实统一开放|
|来源已验证|0 fulltext、0 claim support|metadata-only|
|18/18 evidence coverage|覆盖口径审计|来源/全文/主张/validator 分开，部分支持|
|Function OS 全部通过|25 false reject 的失败轨迹|修复后 bounded pass，原始失败保留|
|苹果实现缺陷|target、I/O、oracle 缺失|executable target absent|

## 关键数字

* 函数机器闭合快照：7,051 canonical identity cards，4,978 explicit quarantine/pending；人类公开表面另有 5,663/3,887 口径。
* 非函数机器闭合快照：17,626 canonical claims，5,801 explicit quarantine/pending；人类表面另有 17,333/5,581 口径。
* Function OS 原始 benchmark：semantic agreement 0.9372、25 false reject、0 false accept、0 registry contamination；修复目标在 bounded domain 达到 1.0。
* Crossref 117/117、OpenAlex primary 116 中 101 supported、8 partial、7 null、0 contradicted。

## 反例

* 一个有限代数反例可以反驳某个普遍公式，却不能告诉我们真实物理理论的完整结构。
* 一个来源 metadata 字段正确，不等于来源正文支持文章中的句子。
* 修复一个 parser bug 后的 1.0，只能回答修复版本在给定样本中的行为。
* 没有执行目标时，不能把“没有输出”解释成“程序失败”。

## 开放问题

* 如何让撤回和降级自动传播到所有公开文章和知识索引？
* 如何统一 Foundation 的两组公共/机器数字，或明确其统计范围？
* 哪些纠正真正改变了跨域研究的可证伪能力，而不仅是仓库表面？
* 如何引入独立领域专家来挑战当前仍然保留的候选？

## Claim ceiling

本章可以支持“百轮迭代产生了系统性的纠正和边界收紧”。它达到历史恢复、纠正谱系和局部实验结论；不达到“当前所有结论可信”或“纠正机制已经保证永不复发”。

## 可进入正文的材料

最适合正文的是三个转折：有限结构被误写成物理 no-go；Crossref/OpenAlex 成功却只到元数据；Function OS 在 1.0 之前暴露真实 parser 缺陷。每个转折都按“为什么当时诱人—哪里出错—保留什么—还不知道什么”来写。苹果案例可作为第四个转折，但放到第七章完整展开。

## 只能放附录的工程信息

各个 `D`、`T`、`Q` 编号的全表、commit graph、机器 distribution、每个 correction 的 JSON 字段、旧文案逐字差异和 validator 日志放附录；正文只选足以说明逻辑的案例。

