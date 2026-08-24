# IGNITION-20260824-138 — Step 07 Synthetic Fixture / Answer Freeze

Task138 now has a new disposable fixture family, separate from Task137
dispatch and attempt identities. Its seven-row table applies the deterministic
rule `eligible == true` and `score >= 60`, then sorts by `(score, id)`. With
the frozen synthetic nonce `abcdef0123456789abcdef01`, Pointfire computes the
independent answer `selected_ids=[item-a,item-d,item-f,item-c]` and
`count=4`; the workspace-before digest is
`40ab9b327e6bf1044e3f57e00aaf483fe6d7f2f77a3bcddc4c414d1825556fba`.

The fixture contains only `README.txt`, `nonce.txt` and `table.json`. It is
made mode `0555` with read-only files before dispatch. A strict JSON Schema
file is created outside the task workspace, mode `0444`, with SHA-256
`060ba4499607b008aa9111390662782787fbf1ce6426c16188a7195b5fbfba58`; it
requires exactly `nonce`, `selected_ids`, `count` and
`workspace_digest_claim`, and disallows additional properties. The expected
answer is held in the Pointfire-side expectation/validator contract, not in a
file exposed to the external executor.

The independent validator recomputes the rule from the fixture, checks exact
keys/types/values, the digest claim, file set, read-only guard and unchanged
tree. Correct and wrong-answer fixtures both pass their intended validator
outcomes. No inference was started.

Claim ceiling: Task138 synthetic fixture and independent answer-contract
evidence only; no live result, validated completion, production readiness,
external truth, Owner acceptance or epistemic acceptance is inferred.
