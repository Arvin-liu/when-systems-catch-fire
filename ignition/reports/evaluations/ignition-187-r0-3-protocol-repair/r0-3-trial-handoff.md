# IGNITION-20260918-187 R0.3 Trial Handoff

## Synthetic R0.2 conclusion

Synthetic, schema-valid ledgers reproduce several independent causes of
`FAIL_READ_LEDGER_INVALID`, including summary, disposition, and manifest
mismatches. A separate synthetic closure sequence reproduces a protocol
self-reference if the final validator invocation and returned status must be
written into the same ledger that the validator certifies. Each validation
then changes the ledger bytes, so the previous attestation no longer covers
the current ledger.

This establishes the conditional protocol defect. It does not attribute the
private Task182-R2 result to that defect. No Task182-R2 local case record,
read ledger, or packet manifest was opened. The actual private root cause
remains `UNRESOLVED_WITHOUT_PRIVATE_LEDGER`; `SUCCESSOR_BOOKKEEPING_ERROR` is
not established. The failed R0.2 trial contributes no inheritance evidence:
`NO_INHERITANCE_EVIDENCE_ADMITTED_FROM_FAILED_R0_2_TRIAL`.

## R0.3 closure boundary

The trial ledger closes at `PRE_FINAL_VALIDATION_CLOSED`: its rows, summary,
entry count, and manifest digest are checked, and its bytes are frozen. The
deterministic finalizer validates those bytes and writes an independent
receipt binding the ledger digest, manifest digest, validator component and
source digest, task, protocol, scope, and status. The receipt states
`FINAL_VALIDATOR_OUTSIDE_CERTIFIED_LEDGER_SCOPE`. Repeating finalization over
the same frozen inputs does not append to or otherwise change the ledger.

The finalizer remains an operational control surface. The Successor may
execute only the listed operational interfaces and observe finite status; it
cannot read validator source or receipt files or manually provide a passing
receipt.

## Fresh held-out cases

The new R0.3 case manifest has SHA256
`7d76008c8cb7fc73497ff70e0c947ddd474da5b0835ca1f9efb1bf7da106c109`.

- `IGNITION-20260918-187-EXP-01` source SHA256:
  `f420e4c0062155f028e27cfcbebb2078cbed92161b855bb03038f6fccb9413a9`
- `IGNITION-20260918-187-GOV-01` source SHA256:
  `5d30785684bbc86a112b6d5b2fea2d7bcfc1e8b9765f6547aa4d4c0b4d11eaf1`

Both are newly authored synthetic cases with provenance pins. They use no
real personal data and contain no gold IR, expected relations, expected
continuation, or evaluator answer.

## Authority boundary

`SUCCESSOR_NOT_RUN`; `EVALUATOR_NOT_RUN`; no canonical promotion; `R1_NOT_AUTHORIZED`.
The final exact branch head, clean-clone gate results, GitHub Actions run IDs,
and terminal handoff state are recorded in PR #225 after exact-head checks
complete. This file records protocol scope and evidence limits; it is not a
Successor or Evaluator result.
