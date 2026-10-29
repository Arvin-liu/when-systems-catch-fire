# 验证报告：047 证据链补齐与 PR #11 合并前复核（IGNITION-20260709-049）

> 本文件为 IGNITION-20260709-049 第三阶段补齐的证据链验证报告，覆盖命令第六/九/十阶段全部门槛。
> 结论仅限材料内成立；普遍性主张全部 `pending_external_evidence`。

## 一、材料与哈希口径统一（问题 2）

- `authoritative_material_text_sha256` = `ee4819880dbbf258a15eb96d572762bc10f16fef8de85f4c41b9dcdfe49fa497`（Markdown 整理稿，实际全文读取与碰撞文本）
- `transport_pdf_sha256` = `218ec306ce1c8e6a8a437cb3d929ac788dd6d771e683489d4309a0c8f011f208`（PDF 传输／展示载体）
- 已在：本 README、D600/D601/D602 的 `source` 字段（已引用 MD SHA）、C-0810/C-0811 的「证据来源」、PR 正文同步采用此口径；PDF SHA 保留为 transport hash，未删除、未声称逐字节一致。
- 047/048 结果记录中涉及「material SHA」的表述已在 049 result 中按此口径统一。

## 二、047 原始产物定位与哈希审计（问题 1 / 第五阶段）

- 原始本地工作区为本机 Codex 任务目录（绝对路径仅记入 1111 progress/result，不写入点火公开仓库）；下含 source-analysis / psi0 / collision / meta-protocols / value-charter / reports / candidates 子目录。
- 本机多点查找确认（不只查单一猜测路径）：Codex 路径命中；047 dianhuo worktree 的 PR 分支未含 outputs（符合 048 仅推送正式条目）。
- 7 份逐字产物原样取回审计（SHA-256 见 `data/collisions/20260711-disobedience-subjectivity.json` 的 `published_evidence_files` 中 `kind: original_verbatim_047` 条目），均未含访谈原文、密钥、MEDIA 标记、真实本机绝对路径。
- 命令点名但本机无精确同名的两份经语义等价确认：
  - `validation-report.md`（命令点名）→ 047 既有 `outputs/reports/verification-report.md`，内容为本轮方法/结论/合规，已据其实质新建本 `validation-report.md` 承接「合并前复核」职责，非凭空编造。
  - `data/collisions/20260711-disobedience-subjectivity.json`（命令点名）→ 047 既有 `outputs/candidates/json/candidates-decision.json`，已据其实质扩展生成本数据 JSON，新增双 SHA 字段与发布文件 SHA。
- 真实缺失文件：`README.md`（命令点名）本机无；已按命令「真实材料优先、禁止伪装」原则，依据 047 command/result/分支 diff 与 7 份原始产物原样新建，不标记为原始产物。

## 三、D600—D602 逐条复核（第七阶段·函数门槛）

| 函数 | ≥2 独立锚点 | 因果链 | 触发 | 停止 | 反例 | 边界 | 异于既有 | 断言等级 | pending | 数学表达 |
|---|---|---|---|---|---|---|---|---|---|---|
| D600 | A2/A3/A4 | 支持→绑定→退出成本↑ | 资源集中+「为你好」定义唯一路径 | 接受方独立+边界 | 无条件兜底/纯建议/交换/胁迫 | ✅ | 异于 D595（代际 vs 绩效） | 材料内成立 | E2 | 结构化表达，非已估计模型 |
| D601 | A5/A8/A15 | 角色占入口→能力附属→目标遮蔽→决策外移 | 角色稳定+外部只按角色评 | 角色外自我叙事 | 角色与自我一致/多元/可逆 | ✅ | 异于 D245（数学门控 vs 社会遮蔽） | 材料内成立 | E5 | 同上 |
| D602 | A7/A8/A9 | 价值—决策分离→漂移→回收→对齐 | 创造者无决策权+战略分歧 | 决策权对齐 | 自然对齐/非核心增值/集体决策 | ✅ | 异于 T40（无价值来源维度） | 材料内成立 | E6 | 同上 |

结论：三条均满足门槛，不降回 candidate。

## 四、C-0810—C-0811 逐条复核（第七阶段·案例门槛）

- C-0810：事件层（A7/A8/A9）与解释层分开；来源可回指（材料 SHA）；关联 D602/T40 准确；非金句；未反向把成功当机制证明；不含大段转载。✅
- C-0811：事件层（A5/A8/A10/A15）与解释层分开；来源可回指；关联 D601/D600 准确；非金句；未把成功当证明；不含大段转载。✅

## 五、编号与计数口径（第八阶段）

- 在最新点火 `origin/main`（`19fdec6…`）重算：D600/D601/D602、C-0810/C-0811 均 FREE，无需重编号。
- 权威 D 计数：main 545 → branch 548（+3，无移除）。
- 权威 C 计数：main 804 → branch 806（+2，无移除）。
- 注：047 回执所报 622/807 为含 `MF-xxxx`/`A-T` 条目的函数总表「文件总数」，与权威 D/C 唯一编号计数不同，不构成阻塞。
- INDEX 行数、唯一 ID 数、文件数三者一致（main 与 branch 均一致）。
- 历史 D224 重复：未在本轮触及；如仍存在，登记为历史债务，不归咎 047。

## 六、完整验证清单（第九阶段，20 项）

1. `git diff --check`：通过（新增文件无空白错误）。
2. `python3 tools/validate_data.py`：ALL_P1_DATA_VALID（新增 data JSON 不影响既有数据集校验）。
3. `python3 tools/validate_meta_protocols.py`：ALL_META_PROTOCOL_DATA_VALID。
4. canonical 现有测试套件 `tests/test_canonical.py`：全 PASS。
5. JSON 全部解析：本数据 JSON `json.load` 通过。
6. INDEX 引用解析：函数/案例 INDEX 链接与文件一致。
7. D/C 唯一编号检查：D600–D602、C-0810–C-0811 唯一。
8. 新文件模板字段检查：各发布文件含必需 front-matter/标题/结论。
9. source hash 双字段一致性：MD SHA 为权威文本 hash，PDF SHA 为 transport hash，二者不混称。
10. 密钥/凭证扫描：无接口密钥、访问令牌、会话凭据或账号类敏感串。
11. 绝对路径扫描：发布文件无真实本机绝对路径（D583 历史路径不在此 PR 清理范围）。
12. 媒体标记占位扫描：无。
13. 长段原文扫描：无访谈全文/大段转载。
14. canonical diff=0：未改 canonical。
15. 价值宪章 diff=0：未改。
16. 12 元协议治理记录 diff=0：未改。
17. Schema/validator/gate diff=0：未改。
18. PR #11 changed files 全部在允许范围：原 9 文件 + 本证据链 10 文件（9 md + 1 json）均属命令允许集合。
19. 047 分析报告（7 份原始产物 + 本验证报告）与正式条目结论一致：D600/D601/D602/C-0810/C-0811 编号、因果、断言等级一致。
20. PR 正文与真实 diff 一致：正文按真实 SHA / 计数 / 文件清单撰写。

## 七、D583 历史路径处置（问题 3）

- D583 文件中的本机绝对路径（指向本机 Get 笔记本地缓存目录，属 `origin/main` 历史遗留）确认存在于 `origin/main` 历史文件，047 仅向该文件追加边界扩展块，未引入该路径；此处不展开写出该路径，避免在点火公开仓库新增真实本机绝对路径。
- 登记为 `pre_existing_repository_debt`；不在本 PR 顺带大范围清理历史文件。
- 未修改 canonical、Schema、validator、gate、价值宪章或元协议记录。

## 八、合并授权与结果（第十阶段）

- 全部门槛通过后，依据 049 command 明确授权合并 PR #11。
- 合并方式：Create a merge commit；不 squash、不 rebase merge、不 auto-merge、不删远程分支。
- 合并后从全新临时目录只读 clone 最新 main 做验收（见 049 result 的 `final-publication-audit.md` 路径引用）。
