# IGNITION-20260709-033-S2-G20-RULE-AND-EVIDENCE-AUDIT

- Repo/worktree: `/Users/zhiyuan/Documents/Codex/2026-07-11/ignition-20260709-033/worktree/when-systems-catch-fire-meta-protocols-release`
- Branch: `codex/meta-protocols-main-release-20260711`
- HEAD at audit start: `34f2aaa545148a7bd2a85f28bbbc2f05d3189b9e`
- Scope: `S2` only

## Sources checked

- `canonical/data/gate-registry.json`
- `canonical/docs/gate-semantics.md`
- `tools/validate_protocol_canonical.py`
- `tools/canonical_registry.py`
- `data/meta-protocols/protocols-canonical.json`
- `data/meta-protocols/meta-protocols.json`

## 1. G20 的正式语义是什么

G20 的正式语义是“与函数表相似性 / 函数层对照是否成立”。

证据：

- `canonical/docs/gate-semantics.md` 明文写的是：`G20 与函数表相似性：semi_automatic → 需对照函数表。`
- 同一文件同时规定：`G07/G10/G13/G20/G22/G23/G33` 这类门槛不得伪装为自动 PASS。
- `canonical/data/gate-registry.json` 中 `G20` 被标成：
  - `type: hard`
  - `mode: semi_automatic`
  - `blocks_content_machine_eligible: true`
  - `auto_derivable: false`

结论：G20 不是“字段存在性检查”，而是一个需要真实证据对照的硬门槛。

## 2. G20 的 PASS 条件是什么

G20 的 PASS 条件应当是：存在足以支持“该协议与函数表关系已被真实对照确认”的证据。

至少应满足：

- 不只是 `function_layer_relation` 字段非空；
- 需要真实函数表对照证据；
- 需要可追溯的 evidence path / locator / reason；
- 在当前冻结语义下，若没有这类证据，应保持 `PENDING`。

这与 `canonical/docs/gate-semantics.md` 和 `gate-registry.json` 的口径一致。

## 3. validator 为什么曾将 S2 判为 PASS

原因为 `tools/validate_protocol_canonical.py` 里把 G20 写成了：

```python
gate("G20", "PASS" if get("function_layer_relation") else "PENDING", ...)
```

也就是说，只要 `function_layer_relation` 非空，validator 就直接给 `G20=PASS`。

S2 当前 canonical 记录中确实有：

- `function_layer_relation: "reference"`

因此旧逻辑会把 `S2` 自动判成 `G20=PASS`。

## 4. PASS 是否仅因为某个字段非空

是。

旧实现中，G20 的 PASS 完全由 `function_layer_relation` 是否非空触发，没有真实函数表对照步骤。

这与 G20 的正式语义不一致。

## 5. PASS 是否要求真实函数表对照证据

要求。

原因：

- `gate-registry.json` 明确 `auto_derivable: false`
- `gate-semantics.md` 明确 `需对照函数表`
- `gate-semantics.md` 明确此类门槛不得伪装为自动 PASS

因此没有真实函数表对照证据时，G20 不能自动 PASS。

## 6. 当前 S2 是否确实满足该条件

不满足。

本轮检查到的 S2 记录虽然有：

- `function_layer_relation: "reference"`
- `positive_evidence`
- `source_references`
- provenance 中的 `unresolved_questions: ["formal_expression", "G20 similarity check"]`

但没有发现能直接证明“已经完成函数表对照”的专门证据字段或审核结果。

相反，现有 provenance 仍保留：

- `G20 similarity check`

这说明该项仍未完成，因此 G20 应保持 `PENDING`。

## 7. canonical 中原来的 G20 PENDING 为什么没有同步更新

因为之前发生的不是 canonical 错，而是 validator 误判。

更准确地说：

1. canonical 持久化记录把 `S2` 存成了 `G20=PENDING`、`content_machine_eligible=false`。
2. 旧 validator 把“`function_layer_relation` 非空”误当成了 G20 PASS 条件。
3. 这让实时结果飘到了：
   - `G20=PASS`
   - `content_machine_eligible=true`
4. 于是出现了“持久化状态”和“实时派生状态”不一致。

所以没有必要把 canonical 强行改成 `true`；应该修正 validator 的 G20 判定逻辑，使其回到正式语义。

## 结论

本任务采用 **路径 B**。

理由：

- G20 的正式规则要求真实函数表对照证据；
- 当前 S2 并没有这类充分证据；
- 旧 validator 只是因为 `function_layer_relation` 非空而误判 PASS；
- 因此应保持：
  - `G20 = PENDING`
  - `G33 = PENDING`
  - `content_machine_eligible = false`
  - `ratification_ready = false`

## 修复方向

已按路径 B 处理：

- 修复 `tools/validate_protocol_canonical.py` 的 G20 逻辑；
- 不再允许“字段非空”直接等同于 G20 PASS；
- 新增 `S2` 持久化状态与实时 validator 一致性测试；
- 保持 S2 canonical 持久化状态不变。
