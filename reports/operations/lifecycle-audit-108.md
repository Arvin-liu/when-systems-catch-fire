# 生命周期审计 · 任务 108（双相迭代终态化与自闭合当前真相 R1）

- 审计对象：`data/operations/lifecycle-events.jsonl`、`data/operations/derived-lifecycle-view.json`、`data/operations/current-truth-projection.json`、`tools/propagation/lifecycle_events.py`、`tag_validator.py`、`terminalization_allowlist.py`、`terminalization_generator.py`、`schemas/operations/lifecycle-event.schema.json`
- 生成方式：`tools/propagation/derived_lifecycle_view.py`（确定性，可重放）
- 审计时间基准：`origin/main` = `77352d27bc997ff9418de017f622f0c72dd634e3`（任务 107 普通合并）

## 1. 基线矛盾（任务 108 之前）

`data/operations/merged-iteration-ledger.jsonl` 在 `main` 上呈现：

| 任务 | 状态 | 说明 |
|------|------|------|
| 104 | TERMINAL_SUCCESS | PR#160 / head 16f64004 / merge 16f64004 |
| 105 | TERMINAL_SUCCESS | PR#161 / head 9d7d5ab5 / merge 9b5b4b9b |
| 106 | **PR_OPEN**（null PR/head/merge） | 已被普通合并（PR#162/head 974c0531/merge af988422）且有终态回执，但单行记录无法在准备时填入未来 merge |
| 107 | **缺失** | 已被普通合并（PR#163/head 43011f37/merge 77352d27）且终态，但未写入该单行表 |

此为合同 §2 要求保留的基线矛盾；本任务**不删除、不改写**历史行。

## 2. 事件溯源模型（替代循环单行）

`lifecycle-events.jsonl` 采用追加式事件：

- `ITERATION_CANDIDATE`（任务 106/107/108 各一条）：提交于内容 PR 合并**之前**，刻意**不含**未来 merge/tag/core 摘要，打破"一行预知未来"的循环。
- `LEGACY_TERMINAL_SUCCESS`（任务 104/105）：向后兼容包装，无需改写旧记录即可判定为已终态。
- `TERMINALIZATION_PROJECTION`（任务 106/107/108 在内容合并后追加）：仅承载内容 PR 号、内容合并提交、预期终端 tag 名，`attestation_mode` 区分 `ORIGINAL_TERMINATION` 与 `RETROACTIVE_RECONCILIATION_BY_TASK_108`。

## 3. 解析结果（当前，未创建终端 tag 前）

运行 `tools/propagation/lifecycle_events.py --json`：

- 104 / 105 → TERMINAL_SUCCESS（legacy）
- 106 / 107 → CONTENT_MERGED_AWAITING_TERMINALIZATION（候选在册，待其回溯标注 tag）
- 108 → READY_FOR_CONTENT_MERGE（候选在册，未合并）

`errors` 为空。任务 106/107 在创建回溯标注 tag 并校验通过后将解析为 TERMINAL_SUCCESS；任务 108 在内容合并→终端化合并→核心证据→标注 tag→全新克隆校验后解析为 TERMINAL_SUCCESS。

## 4. 失败闭合覆盖

`tests/test_lifecycle_events.py` + `tests/test_terminalization_allowlist.py` 覆盖合同 §12 全部 22 项负向 fixture 与正向 fixture（legacy/回溯/常规双相/管理豁免）。解析器在缺失 Git 历史或 tag 时对受影响任务以 `INVALID`/`BLOCKED` 失败闭合，而非默许。

## 5. 当前真相投影

`current-truth-projection.json` 维持 `_derived_from_terminal_only=true`；在 106/107 的回溯 tag 解析为 TERMINAL_SUCCESS 之前，`_non_terminal_tasks_excluded` 含 106。当前 `current_accepted_iteration` 保持 105，直到 106/107 经有效回溯证明纳入。这保证公开当前真相**不**再含过时的任务 106 `PR_OPEN` 解释，且**包含**任务 107 的终态。

## 6. 系统图影响

受管系统图审计（`tools/propagation/system_map_audit.py`）对任务 108 判定 `NO_MAP_IMPACT`：四个受管源与生成器字节未变。证据见 `data/operations/propagation/108-impact/system-map-nonimpact-proof.json`（机器可重验，非自由文本）。

## 7. 诚实边界

- 不声称消除所有传播缝隙；声称缝隙不再依赖单行预知未来，而依赖从干净仓库可重走的不可伪造终态链。
- 任务 106 的历史 `PR_OPEN` 行被显式保留为"当时无法知道未来合并"的证据，而非被抹掉重述。
- 未自动执行任务 109（需显式控制授权）。
