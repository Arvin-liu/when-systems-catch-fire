# Step03 — Method History and Broken Controls

Task198 reuses the Task190 Method-Use Trace R0 schema and validator exactly:

- schema SHA-256: `e53532c8338c76d83b72c79edbb3780800d190ce9338c194c7ba2f03eec69e8b`
- validator SHA-256: `7adcd2c56acb520b26e2f9e126f0ac258ec5f794582e08c0e2c993fcb4f527a5`

The method family is `method:bounded-replay-contrast-r0`. Its history is one
synthetic source shared by the three case-specific traces. It defines a
bounded, held-input replay and a context-specific discriminating observation;
it does not embed a final answer for any case.

Each complete trace contains the exact R0 chain:

`candidate -> selection -> context -> use -> outcome/failure -> revision/disposition`

The outcome segment is bound to the corresponding Task198 facts source. The
three application records retain distinct boundaries: REPL-CASE-01 is
unresolved because measurements are missing, REPL-CASE-02 records watchdog
failure, and REPL-CASE-03 records a repeated bounded observation while leaving
the read-channel source open. All causal attribution remains
`NOT_ESTABLISHED`.

The three neutral `trace-excerpt.json` controls retain a candidate plus partial
context/outcome. Selection/use lineage fields and the revision/disposition
segment are absent. The existing R0 validator rejects each excerpt as expected;
no second schema is introduced and no filename/comment supplies a completion.

Validation result before commit:

```text
METHOD_USE_TRACE_R0_SELF_TEST_OK
VALID: .../REPL-CASE-01/method-trace.json
VALID: .../REPL-CASE-02/method-trace.json
VALID: .../REPL-CASE-03/method-trace.json
EXPECTED_INVALID:trace must contain six ordered segments  (three excerpts)
TASK198_STEP03_METHOD_TRACE_R0_REUSE_VALID
```

No Successor or Evaluator was run.
