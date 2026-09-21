# Step04 — Six Successor-Visible Packets

Six isolated, future-only packets are prepared:

`facts-a`, `facts-b`, `method-a`, `method-b`, `broken-a`, `broken-b`.

Each packet exposes the same three case facts in a pre-frozen order and uses
the same existing R0.1 per-case output record schema. Condition-specific
material is separated by allowlist:

- facts packets: facts and provenance only;
- method packets: facts/provenance plus the complete Method-Use Trace R0
  history and three valid case traces;
- partial-lineage packets: facts/provenance plus three neutral trace excerpts
  with selection/use lineage absent.

No packet exposes another condition's material, evaluator criteria, expected
labels, or answer key. Every future response is local-only and has the same
three-file contract: `successor-response.jsonl`, `read-manifest.json`, and
`freeze-sha256.txt`. The templates are shared under `packets/common/` and are
not evidence from a run.

The case-order receipt records deterministic SHA-256 ordering. A-order is
`REPL-CASE-03, REPL-CASE-01, REPL-CASE-02`; B-order is
`REPL-CASE-01, REPL-CASE-02, REPL-CASE-03`. The order was frozen before any
Successor or Evaluator execution and is not outcome-adaptive.

Step04 performs no conversation execution and writes no response evidence.
