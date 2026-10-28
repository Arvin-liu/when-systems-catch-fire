# 赛课机制教师生存困境碰撞批次收口审计

## 批次范围

- 碰撞材料：`inputs/collisions/20260708-teacher-competition/source.md`
- 碰撞产物：`outputs/collisions/20260708-teacher-competition/`（collision-report / new-functions / new-cases / notes / expanded-notes / rejected / source-snapshot）
- 复核基准：`outputs/audit/teacher-competition-backfill-review-20260708.md`
- 收口目标：对照候选清单，逐条确认哪些已正式入表、哪些暂缓、哪些重定向，并核对索引可见性。

## 环境确认

- git status：干净
- git pull --ff-only：Already up to date
- P1 校验器：`ALL_P1_DATA_VALID`
- 本审计为「只审计不执行」：不新增函数、不新增案例、不修改两张表、不修改 data/schema。

## 候选清单逐项收口

| 候选 | 类型 | 决策 | 正式编号 | 索引可见性 | 审计 |
|---|---|---|---|---|---|
| NF-001 绩效绑定裹挟 | 函数 | 入表 | D595 | 已验证（teacher-competition-index-visibility-check） | small-batch-backfill-audit |
| NF-002 量化指标替代真实价值 | 函数 | 入表 | D597 | d597-index-visibility-check ✓ | nf-002-quantified-metric-backfill-audit |
| NF-003 表演化生产 | 函数 | 重定向为扩展注释 | D173（显态粘性）扩展注释，不新增 | 不适用（非新增） | backfill-review 已记录 |
| NF-004 系统性钝化 | 函数 | 入表 | D598 | d598-index-visibility-check ✓ | nf-004-systemic-numbing-backfill-audit |
| NF-005 避风港 | 函数 | 入表 | D596 | 已验证（teacher-competition-index-visibility-check） | small-batch-backfill-audit |
| NC-001 职称硬门槛裹挟青年教师 | 案例 | 入表 | C-0808 | c0808-index-visibility-check ✓ | nc-001-title-barrier-backfill-audit |
| NC-002 表演化假课与量化指标消解温度 | 案例 | 入表 | C-0809 | c0809-index-visibility-check ✓ | nc-002-performed-fake-class-backfill-audit |
| NC-003 系统性钝化与教室避风港 | 案例 | 入表 | C-0807 | 已验证（teacher-competition-index-visibility-check） | small-batch-backfill-audit |

## 函数表收口状态

- 新增 4 个函数：D595 / D596 / D597 / D598
- 重定向 1 个：NF-003 → D173 扩展注释（不新增函数）
- 函数表 INDEX 头部计数：605 → 606（同步完成）
- 四个新增函数均已完成索引可见性验证，可被后续碰撞流程按编号/标题/语义关键词召回。

## 案例表收口状态

- 新增 3 个案例：C-0807 / C-0808 / C-0809
- 案例表 INDEX 头部计数：790 → 793（分三轮同步：790→791 C-0807；791→792 C-0808；792→793 C-0809）
- 三个新增案例均已完成索引可见性验证。

## 关联闭环核对

- C-0807 → D598 + D596（系统性钝化 + 避风港）
- C-0808 → D595（绩效绑定裹挟）
- C-0809 → D597 + D173（量化指标替代真实价值 + 显态粘性/NF-003 重定向）
- 所有案例对应函数均为本批次已入表或已存在函数，闭环一致，无悬空候选引用。

## 来源与边界一致性

- 全部新增条目均保留来源回指：`inputs/collisions/20260708-teacher-competition/source.md`
- 全部新增案例标注 pending：单篇一线访谈，跨行业/全国普遍性 pending，不写定论。
- 函数/案例均标注与既有条目的边界（D597 vs D244、D598 vs D364/D423、C-0807/0808/0809 之间互不重复）。

## 未完成项（明确挂起，非遗漏）

- **N1~N3（注释/扩展注释类）**：原碰撞产物含 notes.md / expanded-notes.md，本轮收口审计仅做记录，未启动回填复核。状态：pending，等待 GPT 明确指令。
- **E1~E2（evidence 类）**：evidence_regimes（EVID-011/004）约束已在各条目 pending 标注中体现，未单独建 evidence 条目。状态：pending，等待 GPT 明确指令。

## 收口结论

赛课机制教师生存困境碰撞批次**主体已收口**：

- 5 个函数候选 → 4 入表（D595/D596/D597/D598）+ 1 重定向（NF-003→D173 扩展注释）；
- 3 个案例候选 → 3 全部入表（C-0807/C-0808/C-0809）；
- 全部新增条目完成索引可见性验证，来源/边界/pending 标注齐全；
- 未越权处理 N1~N3 / E1~E2，未修改 data/schema，未启动 UNESCO / 得到笔记大规模任务。

## 后续建议

- 若需继续：可对 N1~N3（注释/扩展注释）与 E1~E2（evidence）做回填复核，仍按小批量、显式指定、先验证后入表流程执行。
- 本批次已具备「收口」状态，可择机做 P1 级封版（tag / 发布）动作——但该动作需 GPT 明确指令，本审计不触发。

## 未处理项

- N1~N3：挂起（pending）
- E1~E2：挂起（pending）

## 未修改事项

- 未新增函数
- 未新增案例
- 未修改函数表
- 未修改案例表
- 未修改 data
- 未修改 schema
- 未启动 UNESCO
- 未启动得到笔记大规模任务
