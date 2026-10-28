# D583 可移植来源引用清理审计报告（IGNITION-20260709-055）

- 日期：2026-07-11
- 任务：IGNITION-20260709-055
- 仓库：Arvin-liu/when-systems-catch-fire
- 基线 main SHA：895c9895b7f7587a0db26f00619bbdd272204df1
- 分支：fix/d583-portable-source-reference-20260711
- 目标文件：`统一函数总表/0593-D583-认知肌肉锻炼.md`

## 一、原问题性质

D583 文件中含有历史遗留的 macOS 本机绝对路径，作为原始来源锚点写入 3 处：
1. frontmatter `source:` 字段
2. 正文「基本信息 · 来源」
3. 正文「原文捞回 · 验证 · 来源报告」

该路径指向本机 Get 笔记导出文件，是不可移植的本机目录引用，属于仓库可移植性债务，不是函数理论内容。

## 二、原路径脱敏类型

脱敏形式：

`/Users/<user>/Library/Containers/com.biji.getNotes/Data/Library/Caches/<Get 笔记导出 md 文件名>`

（不复制完整敏感路径；仅保留必要片段以说明其类型为 macOS 用户目录下的 App 容器缓存路径。）

## 三、历史归因

- `git blame` 显示三处路径均来自 commit `590833b`（作者：之元，2026-07-07 20:46），早于 047。
- 047 引入的内容为「边界扩展（IGNITION-20260709-047，2026-07-11）」块（commit `b6afd2f`，第 66 行），该块不含任何绝对路径。
- 结论：绝对路径为 047 之前的历史遗留债务，非 047 引入。与 049 result 中登记的 `pre_existing_repository_debt` 一致。

## 四、替代引用方案（目标 B 决策）

按命令优先级逐档判定：
1. 仓库内是否存在同一来源文件副本？——否（`find` / `grep` 全仓未发现该 Get 笔记导出 md 的仓库内副本）。
2. 是否存在稳定公开 URL？——否（Get 笔记本机导出，无公开 URL）。
3. 是否已有稳定标识（标题 / 文档 ID / 内容 SHA）？——仅有可读标题与日期，无仓库登记的内容 SHA 或文档 ID。
4. → 采用第 4 档：中性来源描述。

改写后统一为：

`Get 笔记导出《本次对话新增函数编号与数学表达 2026年7月5日1819》（2026-07-05，来自【Get 笔记】）。原始本机绝对路径已移除；该来源文件当前不随仓库分发。`

保留的可验证 provenance：来源平台（Get 笔记）、原始导出标题、日期（2026-07-05）、任务编号（IGNITION-20260709-055）。未编造任何 URL、文件名、SHA 或文档 ID。

## 五、D583 语义 diff 结论

- 仅修改 3 处来源引用文本行。
- 未改动：函数定义、`JIP = α·log(W) + β·log(T)` 公式、判定理由、数学推导过程、有效条件、收敛状态、关联案例（C-0781—C-0784）、原文捞回注释、扩展注释、047 边界扩展块、Ψ₀ 判定（J⁺=1, J⁻=0）。
- D583 编号与函数名称「认知肌肉锻炼」未变。
- 理论语义、公式、边界、反例、扩展注释均未变化。

## 六、全仓绝对路径扫描摘要

扫描模式：`/Users/`、`/home/`、`C:\Users\`、`file:///`（`*.md`）。

| 目录 | 命中行数 | 分类 |
|------|---------|------|
| 统一案例总表 | 801 | 真实历史债务（同类 Get 笔记来源锚点，pre-existing） |
| 统一函数总表 | 606 | 真实历史债务（含本任务已清理的 D583；其余为同类 pre-existing） |
| outputs | 5 | 文档说明 / 审计记录中的执行位置或来源快照（历史审计文本，非条目正文） |
| 新故事 | 1 | 真实历史债务（0001-S1 的 source/derived_from/来源锚点） |
| docs | 1 | 文档说明（agent-trigger-phrases 中的示例仓库路径） |

- 全仓命中约 1814 行 / 1414 文件。
- 本任务仅修改 D583 中确认的历史债务，其余全部只报告、未批量修改。

## 七、未处理的其他候选债务清单

- 统一函数总表 / 统一案例总表中其余数百个条目的同类 Get 笔记本机来源锚点（真实债务，建议后续任务统一批量可移植化，需独立命令授权）。
- `新故事/0001-S1-比刀剑更持久的，是共享观念.md` 的 source / derived_from / 来源锚点（真实债务）。
- `docs/agent-trigger-phrases-20260708.md` 第 17 行示例路径（文档说明类，非条目 provenance，优先级低）。
- outputs/audit 与 outputs/collisions 下历史审计/快照文本中的执行位置路径（文档说明类，反映历史执行环境，是否清理待 GPT 决定）。

## 八、验证结果

- D583 绝对路径残留：0（`grep /Users/ /home/ C:\Users` → NONE）。
- `git diff --check`：通过。
- 分支 vs origin/main diff：仅 D583 文件 + 本审计报告。
- `tools/validate_data.py`：ALL_P1_DATA_VALID。
- `tools/validate_meta_protocols.py`：ALL_META_PROTOCOL_DATA_VALID（protocols=12 combinations=64 book_cases=22）。
- `tests/test_canonical.py`：TOTAL 40 | PASS 40 | FAIL 0。
- canonical / 价值宪章 / 12 元协议治理记录 / Schema / validator / gate / 其他函数 / 案例：diff=0。
- 无凭证 / token / 密钥 / 新本机路径进入 commit。
