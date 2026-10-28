# Task182-R2 R0.2 Failure Receipt

## Authority and scope

This receipt records only the Owner/GPT minimum failure summary embedded in
`Arvin-liu/1111/agent-commands/IGNITION-20260918-187.md` at `main`, blob
`92d0719c2c9d25f4d51c97f62fecd4fa87c37a6c`. It does not use or reproduce
Task182-R2's local case records, read ledger, packet manifest, or case
contents. None of those private files was opened for Task187.

## Supplied minimum failure summary

- manifest SHA256 匹配；
- authorization guard install/CHECK 成功；
- 第一次 COMMIT guard 因 untracked evidence 返回 `FAIL_UNEXPLAINED_WORKTREE`；
- staging 三份指定 evidence 后 COMMIT guard 成功；
- 两份 successor records 与 ledger 各自 JSON Schema pass；
- manifest-listed read-ledger validator 返回 `FAIL_READ_LEDGER_INVALID`；
- 未触发 `PROTOCOL_CONTAMINATED`；
- 未 commit / push / create PR。

## Classification

- R0.2 trial: `NOT_COMPLETED`.
- Successor record and ledger schema result: `PASS`; this does not imply
  semantic validator success.
- Read-ledger validator result: `FAIL_READ_LEDGER_INVALID`.
- Contamination status: `NOT_FLAGGED` in the supplied summary.
- Commit, push, and PR result: none.
- Synthetic R0.2 self-reference result: reproduced conditionally if the
  final validator invocation and returned status are required to be entries
  in the same ledger the validator certifies.
- R0.2 implementation bug: `NOT_DEMONSTRATED_BY_SYNTHETIC_REPRODUCTION`.
- Successor bookkeeping error: `NOT_ESTABLISHED_WITHOUT_PRIVATE_LEDGER`.
- Actual private R2 invalid root cause:
  `UNRESOLVED_WITHOUT_PRIVATE_LEDGER`.
- Inheritance evidence:
  `NO_INHERITANCE_EVIDENCE_ADMITTED_FROM_FAILED_R0_2_TRIAL`.

The synthetic self-reference result establishes a protocol-level closure
defect under that same-ledger requirement. It does not prove that this defect
caused the private Task182-R2 `FAIL_READ_LEDGER_INVALID` result. Other
synthetic schema-valid routes to INVALID were also demonstrated in Step00;
none is attributed to the private ledger. No root-cause guess or case content
is admitted by this receipt.
