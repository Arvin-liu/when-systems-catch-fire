# Step02 — Three Fresh Synthetic Replicated Cases

The Task198 case manifest freezes three new, bounded, synthetic sources:

| Case | Structure | Required observation boundary |
| --- | --- | --- |
| `REPL-CASE-01` | two-lane mirror-latch relay | missing pre-input measurement; interpretation remains unresolved |
| `REPL-CASE-02` | queue, acknowledgement register, and watchdog | negative observation: watchdog expiry with no recorded acknowledgement |
| `REPL-CASE-03` | primary/shadow cells and a separated read channel | repeated fold observation with an unmeasured read-channel boundary |

The cases are structurally different rather than numeric substitutions. They
use only invented names, values, and local observations; they contain no real
personal data or external-knowledge dependency. The facts sources contain no
method history, condition label, evaluator label, expected disposition, or
embedded method answer.

## Frozen bytes

The authoritative hashes are in `cases/case-manifest.json` and are checked by
`tools/validate_step02_cases.py`. The manifest itself is bound by the
`cases/case-manifest.sha256` sidecar. The validator requires:

- each source SHA-256 to equal the final source bytes;
- each provenance SHA-256 to equal the final provenance bytes;
- each provenance source hash to equal its manifest entry;
- the manifest sidecar digest to equal the final manifest bytes; and
- facts sources to remain free of method/evaluator leakage markers.

Validation result before commit:

`TASK198_STEP02_CASE_MANIFEST_VALID`

No Successor or Evaluator was run. No prior Task190/Task197 artifact was
modified, no condition was assigned to a case at this step, and no canonical
claim was created.
