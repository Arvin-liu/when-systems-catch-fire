# 任务 112 独立事实与证据审查

## 审查对象与方法

- 审查对象：任务 112 内容检查点 `13b8bb04` 的五件前台成果；第一卷审查前 SHA-256 为 `d8fe67fc5b0584cf37e711b3099d15cbf2a6d2bc75437109fd95950085000462`。
- 审查角色：事实与证据审查者。该角色只检查可定位的项目事实、数字、版本、证据类型和 claim ceiling，不把写作流畅度当作事实证明。
- 对照材料：R0 冻结的 `R0_SOURCE_LOCK.json`、`R0_FILE_MANIFEST.json`、`R0_CLAIM_AUDIT.jsonl`；正式仓库任务 103、105、110、111 的机器结果、文章和当前状态文件；任务 112 的 `FINAL_CHAPTER_EVIDENCE_MAP.md`。
- 限制：这是独立角色审查，不是外部领域专家或真实读者参与；“通过”表示本审查已找到可定位依据或明确标注缺口。

## 总结判定

初稿**证据结构通过但需要修订后通过**。没有发现会迫使本卷整体退回的虚构结果；发现 4 项必须修正的时间/措辞问题，8 项保留但需要在最终 manifest 中绑定，3 项可以保留为明确的解释性判断。最重要的事实风险不是数字本身，而是“任务 112 合并后仍把审计起点写成当前 main”。

## 逐项审查

| ID | 位置 | 检查问题 | 证据判断 | 处置 |
| --- | --- | --- | --- | --- |
| F-112-01 | 第一卷前言第 7 行；全景前言；台账导言；笔记导言 | `main=302362f6…` 被写成“当前”是否会在任务 112 合并后失效？ | 是。该 SHA 是任务 112 审计起点/前驱 111 terminal-evidence 合并后的快照，不可能继续作为合并后的 current main。 | **FIX**：统一改为“任务 112 审计起点 main”，把最终提交放入 manifest，不把历史快照伪装成当前状态。 |
| F-112-02 | 第一卷第十章/第七章；全景第 18 项 | 任务 111 的 `TERMINAL_SUCCESS`、recovery-1 和原始无效 tag 是否被误写成苹果或物理结果？ | 否。正文明确写成生命周期事实，并明确“不升级为历史因果/科学证明”；与 `data/operations/iterations/111/FINAL_STATE.json`、111 recovery tag 和任务 111 dossier 一致。 | **RETAIN**，最终 manifest 记录为历史状态来源。 |
| F-112-03 | 第一卷第 283–285 行；全景纠正项 13/14；台账 R0-063 | 7,051/4,978、5,663/3,887、17,626/5,801、17,333/5,581 是否被当作成果总量？ | 否。正文称并存快照并拒绝选择较大值；来源分层和未统一边界清楚。 | **RETAIN**；增加审计快照日期字段。 |
| F-112-04 | 第一卷第 365、395、413 行；全景第 14/15 项 | `0.9372`、25 false reject、0 false accept、0 contamination 和修复后 1.0 是否来源明确、范围充分？ | R0 benchmark/任务 105 材料支持原始数字；正文已写有限 benchmark、独立 oracle 和版本链，但“1.0”应明确为 semantic agreement，避免像普遍正确率。 | **FIX**：改为“修复后的 semantic agreement 1.0（在声明域内）”。 |
| F-112-05 | 第一卷第 437 行；全景第 16 项 | “处理了 5 年字段修正”是否会被读成五年时间跨度？ | 原始证据是 5 条 `crossref_year` 字段缺口/修正，不是五年跨度。 | **FIX**：改为“修正了 5 个年份字段”。 |
| F-112-06 | 第一卷第 437–443 行；全景第 16/17 项 | 117/117、101/116、8 partial、7 null 是否被写成全文或理论支持？ | 否。正文反复标为元数据/来源关联层，并保留 partial/null；与 Crossref/OpenAlex run result 一致。 | **RETAIN**；最终 manifest 记录 `METADATA_ONLY` claim ceiling。 |
| F-112-07 | 第一卷第 505–545 行；全景当前第 18/19 项 | 苹果材料是否区分 memoir association、target absent、formalization underspecified 和 reproduced defect？ | 是。正文没有把 memoir 写成唯一触发，也没有把 target absent 写成程序失败；任务 111 dossier 和 target audit 支持该边界。 | **RETAIN**。 |
| F-112-08 | 第一卷第 283 行 | “机器闭合快照”是否被写成当前正式真相？ | 否。前缀是 R0 固定基线，正文说明是登记/处置规模而非发现数。 | **RETAIN**。 |
| F-112-09 | 第一卷第 361–391 行 | 479 是否被用作所有函数的样本量？ | 否。文本明确说不是世界样本，属于预注册 bounded benchmark。 | **RETAIN**。 |
| F-112-10 | 台账统计摘要和 `FINAL_ACHIEVEMENT_LEDGER.jsonl` | 输出类别是否只按任务标题/文件名赋值？ | 不是。脚本的 `PRIMARY` 覆盖和每条记录的证据、当前结论、边界、source path、claim ceiling 共同给出分类；台账也明确禁止文件数量冒充成果。 | **RETAIN**；最终输出 accounting 报告分类规则。 |
| F-112-11 | 研究笔记 N42、N47–N50 | R0 中被审计指出的数字、source package 和 111 状态边界是否回弹？ | 目标五条已重写；笔记索引 60/60 有五个必需字段；没有发现 exact paragraph copy。 | **RETAIN**，最终 hash 绑定 index。 |
| F-112-12 | 出版书架和根入口 | 前台成果是否从 root README 一跳到 shelf、再一跳到 volume？ | 当前 branch 中 root README → `PUBLICATIONS/README.md` → volume 链接均存在；验证器会逐项检查。 | **RETAIN**，content PR 后在 fresh clone 重跑。 |
| F-112-13 | 第一卷第 125–135 行、第 869–879 行 | 形式化、工程、来源和研究推断是否被混作单一证据等级？ | 没有。四类关系在正文和证据约定中并列区分；仍需用最终 manifest 绑定 review state。 | **RETAIN**。 |
| F-112-14 | 第一卷第 917 行、全景最小总括 | 是否遗漏量子引力、四力统一、开放世界函数和历史因果未完成？ | 没有；这些未交付物在正文、全景未知项和 glossary 中重复出现。重复在此处是防止标题被单独摘引的必要保护。 | **RETAIN**。 |
| F-112-15 | 第一卷第 517 行 | 直接写出 `data/operations/iterations/111/FINAL_STATE.json` 和 tag 是否给普通读者制造内部路径负担？ | 事实本身准确，但属于定位细节，不应成为连续叙事的必读部分。 | **WEAKEN**：正文改为人类可读表述，精确路径移至来源附录。 |

## 最终必须满足的事实门

1. 最终 manifest 的每个 SHA 必须与合并前实际文件相同；不能使用本审查所绑定的预审查 hash。
2. 所有“当前”改为带时间范围的“审计起点”或改由终态证据写入；不能在出版物中硬编码未来 main。
3. 数字、`supported`、`1.0`、`TERMINAL_SUCCESS` 和 `target absent` 旁边必须保留对象与证据层，不得在编辑修订中删掉边界。
4. 本审查不接受 R0 的 72 条意见作为任务 112 的事实审查替代；R0 审查仅作为历史 intake 材料。

## 审查结论

`FACTUAL_REVIEW_PASS_AFTER_REQUIRED_FIXES`。F-112-01、F-112-04、F-112-05、F-112-15 必须在最终第二版写入；其余事实判断可保留，但必须绑定最终审查 hash、来源 manifest 和 fresh-clone 验证。
