# 任务 112 第一卷章节证据地图

本文件把最终第一卷的十个概念章节与可复核来源绑定。它是证据导航，不把来源数量转换成结论强度。每章的正文仍必须保留自己的边界句；读者不需要打开本文件才能理解第一卷。

固定来源基线：R0 原始材料 `9b15d359c54694d851c38df6ab3c7ae42544a51b`；当前正式仓库快照在审计时为 `302362f66dad4e8a9c9e72400f4267c12b0b0d00`。任务 111 的生命周期恢复事实只用于说明项目状态，不能替代历史、物理或因果证据。

## 章节绑定

| 章 | 核心问题 | 可支持的认识 | 不能支持的强说法 | 主要来源 | 只能进入附录的工程信息 |
| --- | --- | --- | --- | --- | --- |
| 01 | 点火为何从跨域相似感开始？ | 相似可以生成候选问题；对象、关系和失败条件使候选可检查。 | 跨域相似已证明同构、共同机制或普遍因果。 | `docs/author_motivation_and_boundary_note.md`；`docs/v0.2_summary.md`；早期函数/案例索引 | 文件级清单、旧编号映射、生成脚本 |
| 02 | 为什么解释不等于证明？ | 不同证据类型和 claim ceiling 必须并列；可反驳性是研究问题的最低条件。 | 叙事流畅、形式化存在或内部测试通过即为外部真理。 | `docs/evidence_regime_library.md`；`ITERATION.md`；`RESULTS/EVIDENCE-LINEAGE.md` | 状态枚举 schema、CI 调用链 |
| 03 | 百轮纠正改变了什么？ | 强句可被降级、撤回、隔离并保留谱系；纠正本身是知识变化。 | 旧句仍可通过换名回到当前结论；一次纠正证明相反的普遍命题。 | `RESULTS/CORRECTIONS.md`；`KNOWLEDGE/EVOLUTION.md`；任务 98/100/111 资料 | PR 编号、恢复 tag 对象、机器事件行 |
| 04 | 函数与断言治理发现了什么？ | 登记、身份、成熟度、处置和证据链让对象可追踪；不同快照数字必须带范围。 | registry closure 等于定义完成、证明完成或外部真值完成。 | `docs/foundation/historical-function-deep-adjudication-20260729.md`；`reports/foundation-architecture/100-nonfunction-claim-evidence-lineage-closure.md`；`RESULTS/LATEST.md` | 生成器日志、逐项计数快照、schema |
| 05 | Function OS 能做什么？ | 在声明的符号、确定性、有限输入域内，可运行并保留局部失败；修复后的 benchmark 只支持有界能力。 | 它是通用解释器、生产安全系统，或覆盖所有函数。 | `docs/editorial/articles/007-bounded-trust-function-os-v02-capability-benchmark.md`；Function OS 测试与 benchmark 记录 | 测试命令、fixture 列表、内部函数路径 |
| 06 | 两次外部书目试验带来什么？ | Crossref/OpenAlex 可在固定协议内回收元数据并暴露 partial/null；来源入口能被复核。 | DOI 命中等于读过全文、论文主张获支持或理论获得验证。 | `evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION/`；`evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-OPENALEX-DOI-REPLICATION-20260801/`；任务 104/110 文章 | 原始响应哈希、HTTP 记录、运行脚本 |
| 07 | 苹果案例的边界在哪里？ | 历史材料支持有边界的 memoir association；没有 executable target 时不能宣称 reproduced implementation defect。 | 苹果唯一、直接、瞬间触发完整重力理论；故事已被程序复现或证伪。 | `data/operations/iterations/111/historical/EVIDENCE_DOSSIER.md`；`data/operations/iterations/111/TARGET_AUDIT.md`；`docs/editorial/articles/010-failure-case-evidence-gate-and-apple-case-adjudication.md` | 精确恢复 tag、生命周期 JSON、receipt 路径 |
| 08 | 点火仍不知道什么？ | 未知可被分类为证据缺口、定义缺口、外部复制缺口、解释缺口和机构缺口。 | 把路线图、类比或内部状态写成答案。 | `RESULTS/OPEN-QUESTIONS.md`；`UNRESOLVED.md`；本卷第八章和全景第三块 | 待办队列机器字段、历史任务号 |
| 09 | 基础设施怎样靠近研究机构？ | 公共作品、责任链、可撤回性、维护与独立审查是机构化的条件。 | 有仓库、CI、索引或一页入口就已经成为研究机构。 | `HUMAN-READING.md`；`KNOWLEDGE/README.md`；`docs/project-current-state.md`；本卷第九章 | Git 分支拓扑、部署/CI 配置 |
| 10 | 下一步最值得研究什么？ | 优先处理数字口径、claim-level 阅读、独立复制、target/oracle、跨域反例和读者误读。 | 方向清单是已批准项目、已有结果或成功承诺。 | `RESULTS/OPEN-QUESTIONS.md`；本卷第十章；全景第四块；台账缺口 | 任务调度、未来 PR 草稿、内部规划权重 |

## 证据使用规则

1. 版本、提交和路径用于定位历史材料；它们本身不提高材料的证据等级。
2. 内部工程结果只支持声明版本、输入、输出、oracle 和运行环境内的行为。
3. 外部元数据只支持元数据层命题；`supported`、`partial`、`null` 不得在正文中被改写成论文内容真值。
4. 历史来源的传播、回忆和后见之明必须分层；没有 target、精确输入、trace 和 oracle 时，案例不得进入“已复现程序缺陷”。
5. 所有仍有争议的数量都携带统计对象、快照和口径说明；若当前不能解释差异，正文保留差异。
