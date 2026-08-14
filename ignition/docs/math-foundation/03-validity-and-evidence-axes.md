# Validity And Evidence Axes

废止用单一 `converged` 同时代表文档完成、数学正确和外部真实的做法。

最少拆分为：

- `workflow_status`
- `formal_status`
- `proof_status`
- `evidence_status`
- `scope_status`
- `provenance_status`

其中：

- `formal_status`: UNFORMALIZED / WELL_FORMED / TYPE_ERROR / SEMANTICALLY_UNDEFINED / FORMALIZATION_INCOMPLETE / COUNTEREXAMPLE_FOUND
- `proof_status`: DEFINITION_ONLY / UNPROVED_PROPOSITION / PROVED_IN_DECLARED_SYSTEM / EXTERNAL_THEOREM / DISPROVED / NOT_APPLICABLE
- `evidence_status`: SOURCE_ONLY / CASE_SUPPORTED / MULTI_CASE_SUPPORTED / EMPIRICALLY_TESTED / EXTERNALLY_VALIDATED / PENDING

任何强断言都必须明确属于哪一轴，不得用 `converged` 混写。
