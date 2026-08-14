# 迭代生命周期模型（事件溯源 · 任务 108 引入）

本目录与 `data/operations/` 下的生命周期文件定义了点火仓库的**迭代终态模型**。
它在任务 108 中取代"一行可变终态记录"的循环模型，改为**追加式、事件溯源**的不可变事件 + 不可伪造标注终端 tag。

## 关键文件

- `data/operations/lifecycle-events.jsonl` — 追加式生命周期事件（候选 / 终端化投影 / 兼容终态）。**只追加，不删除、不改写历史行。**
- `data/operations/derived-lifecycle-view.json` — 从事件 + 终端 tag 推导出的当前真相视图（确定性生成）。
- `data/operations/current-truth-projection.json` — 对外当前真相投影，仅从 TERMINAL_SUCCESS 推导。
- `tools/propagation/lifecycle_events.py` — 事件加载、schema 校验、Git 历史校验、失败闭合解析器。
- `tools/propagation/tag_validator.py` — 标注终端 tag 校验（annotated / 指向 / 消息字段 / core 摘要）。
- `tools/propagation/terminalization_allowlist.py` — 终端化 PR 差分白名单校验。
- `tools/propagation/terminalization_generator.py` — 确定性终端化投影生成器。
- `schemas/operations/lifecycle-event.schema.json` — 事件 schema。

## 事件类型

| 事件 | 何时写入 | 约束 |
|------|----------|------|
| `ITERATION_CANDIDATE` | 内容 PR 合并**之前** | 不得含未来 merge/tag/core 摘要；`lifecycle_state=READY_FOR_CONTENT_MERGE` |
| `TERMINALIZATION_PROJECTION` | 内容 PR 普通合并**之后** | 必须含 `content_pr_number` 与 `content_merge_commit`；不得早于内容合并 |
| `LEGACY_TERMINAL_SUCCESS` | 历史兼容 | 向后兼容，不参与新链推导 |

## 终端 tag

每个被归为已终态的任务必须存在标注 tag：`ignition/iterations/<n>/terminal-r1`。
它必须：为标注 tag（含 tag 对象）；指向终端化合并；消息绑定 `core_receipt_sha256`；
在创建后从全新完整克隆重新解析验证。详见 `tag_validator.py`。

## 解析状态

`READY_FOR_CONTENT_MERGE` · `CONTENT_MERGED_AWAITING_TERMINALIZATION` ·
`AWAITING_TERMINAL_TAG` · `TERMINAL_SUCCESS` · `BLOCKED` · `INVALID`。
缺失 Git 历史或 tag 时，受影响任务以 `INVALID`/`BLOCKED` 失败闭合。

## 操作

```bash
# 推导视图（确定性）
python3 tools/propagation/derived_lifecycle_view.py --repo .

# 校验（CI 使用）
python3 tools/propagation/lifecycle_events.py --json
python3 -m pytest tests/test_lifecycle_events.py tests/test_terminalization_allowlist.py -q
```
