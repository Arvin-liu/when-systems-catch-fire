# Task172 routing facets

这是 `knowledge.collide_object` 的薄人类入口。它是检索与碰撞路由元数据，不是正确性、重要性、成熟度、证据、公开资格或领域权威。旧的七个 Knowledge subjects 仍然有效；这里的 UNESCO 分面与其正交。

机器索引：[`step07-routing-index.json`](../data/research/task172-routing-r1/step07-routing-index.json)。当前索引包含 24137 条 canonical-ID 路由记录；返回候选后必须回读 authority registry 做 fingerprint exact validation。

## 受控 collision-use 标签

### `EXPLAIN`

- 含义/可做什么：retrieve assets useful for bounded explanation; never a truth claim。
- 当前记录数：4565；示例：`FUNCTION_ASSET:D107`, `FUNCTION_ASSET:D11`, `FUNCTION_ASSET:D114`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `COMPARE`

- 含义/可做什么：place governed assets side by side for a stated comparison。
- 当前记录数：1535；示例：`NONFUNCTION_CLAIM:CLAIM-BC-20260709-001`, `NONFUNCTION_CLAIM:CLAIM-BC-20260709-002`, `NONFUNCTION_CLAIM:CLAIM-BC-20260709-005`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `ANALOGY_SOURCE`

- 含义/可做什么：retrieve a source for a structural analogy review。
- 当前记录数：0；示例：无。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `MECHANISM_TEST`

- 含义/可做什么：retrieve an asset for mechanism-boundary inspection。
- 当前记录数：1561；示例：`NONFUNCTION_CLAIM:CLAIM-BC-20260709-003`, `NONFUNCTION_CLAIM:CLAIM-BC-20260709-006`, `NONFUNCTION_CLAIM:CLAIM-BC-20260709-012`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `CAUSAL_CHALLENGE`

- 含义/可做什么：retrieve an asset for causal-claim challenge, not causal proof。
- 当前记录数：1561；示例：`NONFUNCTION_CLAIM:CLAIM-BC-20260709-003`, `NONFUNCTION_CLAIM:CLAIM-BC-20260709-006`, `NONFUNCTION_CLAIM:CLAIM-BC-20260709-012`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `COUNTEREXAMPLE`

- 含义/可做什么：retrieve a negative or competing case for boundary testing。
- 当前记录数：16316；示例：`FUNCTION_ASSET:A0`, `FUNCTION_ASSET:A0004`, `FUNCTION_ASSET:A0036`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `EVIDENCE_CHECK`

- 含义/可做什么：retrieve an asset whose evidence boundary needs checking。
- 当前记录数：16476；示例：`FUNCTION_ASSET:A0`, `FUNCTION_ASSET:A0004`, `FUNCTION_ASSET:A0036`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `METHOD_TRANSFER`

- 含义/可做什么：retrieve a method/formal-scope candidate for cautious transfer review。
- 当前记录数：0；示例：无。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `BOUNDARY_TEST`

- 含义/可做什么：retrieve an asset for scope, ceiling or failure-condition review。
- 当前记录数：2927；示例：`FUNCTION_ASSET:D182`, `FUNCTION_ASSET:D183`, `FUNCTION_ASSET:D184`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `NORMATIVE_CHECK`

- 含义/可做什么：retrieve an asset for an explicit normative boundary review。
- 当前记录数：0；示例：无。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `NARRATIVE_CASE`

- 含义/可做什么：retrieve a source-defined narrative or interpretive case。
- 当前记录数：0；示例：无。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

### `HISTORICAL_CONTEXT`

- 含义/可做什么：retrieve historical or withdrawn context without positive promotion。
- 当前记录数：14755；示例：`FUNCTION_ASSET:A0`, `FUNCTION_ASSET:A0004`, `FUNCTION_ASSET:A0036`。
- 不适用：不能把命中标签写成事实、因果、证据支持、证明或 canonical promotion。

## UNESCO 分面

- 二位 field facet 值：19；四位 discipline facet 值：0。空 discipline 不表示失败：它表示当前 routing 没有足够依据伪造四位等价。
- `OUT_OF_UNESCO_SCOPE` / `UNRESOLVED` 保留为合法状态；内部治理、CI、运行时和 bookkeeping 不为覆盖率强贴科学学科码。
- 该 taxonomy 是 1988 UNESCO proposed nomenclature 的版本化 routing ontology，不应表述为 2026 年唯一现代学科真理标准。

## 操作边界

`knowledge.collide_object` 仍是 `CURRENT_BOUNDED + READ_ONLY_RUN`。路由器只读 compact index 与 Current authority；不写 registry、不联网、不改变输入对象、M/E、disposition、claim ceiling 或 evidence status。若 facet 交集不足，结果会显式标记 fallback 和原因。
