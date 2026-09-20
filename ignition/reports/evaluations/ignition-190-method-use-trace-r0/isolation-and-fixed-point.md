# Evaluation/research isolation and fixed point

All Task190 files are under the task-local prefix
`ignition/reports/evaluations/ignition-190-method-use-trace-r0/`. The path-accounting manifest lists every file, including the
Step09 manifest, receipt, and isolation note. Every entry is typed
`RESEARCH_EVALUATION_ONLY`, provenance-visible, excluded from automatic
Foundation non-authoritative claim discovery, and assigned zero candidate
fragments and zero canonical claim IDs.

Knowledge canonical admission, Fire Seeds promotion, Current mutation, and
automatic promotion are all `NONE`.

The same inventory generation was performed twice against the exact Step09
pre-addition tree snapshot plus the declared Step09 additions. Both output the
same manifest SHA-256:

`225c1b09e26b77c62f88ff8e6a179d3b8d7a9384cd0cc949d96c435b18ffe198`

This is a fixed point for path accounting. The receipt binds the frozen
inventory independently; it does not mutate a certified ledger during its own
validation. Task190 does not run Successor or Evaluator.
