# R0.3 case-exposure semantic defect reproduction

## Scope

This report uses only a new synthetic manifest and synthetic ledger rows. It does not read or infer any Task182-R3 private successor output, read ledger, or final receipt.

The synthetic manifest contains an allowlisted method path, an allowlisted held-out case path, a certified operational component, and the R0.3 final validator as a final-attestation component. Every synthetic ledger is schema-valid before finalization.

## Observed results

| Synthetic row | Row disposition | R0.3 finalizer result |
| --- | --- | --- |
| Allowlisted cognitive non-case, `case_specific_information_exposed=false` | `CLEAN` | `PASS_READ_LEDGER_CLEAN` |
| Allowlisted held-out case cognitive read, `case_specific_information_exposed=true` | `CLEAN` | `FAIL_READ_LEDGER_INVALID` |
| The same allowlisted case read, forced to `CONTAMINATED` | `CONTAMINATED` | `FAIL_READ_LEDGER_CONTAMINATED` |
| Operational status with `case_specific_information_exposed=true` | `CONTAMINATED` | `FAIL_READ_LEDGER_CONTAMINATED` |
| Unlisted cognitive read | `CONTAMINATED` | `FAIL_READ_LEDGER_CONTAMINATED` |

The clean case row is schema-valid, but R0.3 first maps `case_specific_information_exposed=true` to contamination and then compares that derived disposition with the row's declared `CLEAN` disposition. The semantic mismatch produces `FAIL_READ_LEDGER_INVALID`. Marking the same legal case read contaminated makes the finalizer pass as contaminated, demonstrating that the protocol treats normal authorized case reading as contamination.

## Verdict

`R0_3_CASE_EXPOSURE_SEMANTIC_DEFECT_CONFIRMED`

The repair target is channel-aware semantics: authorized cognitive case exposure can remain `CLEAN`; case-specific exposure through operational/control channels remains `CONTAMINATED`; and unlisted cognitive content remains `CONTAMINATED`.

Machine-readable results: `r0-3-case-exposure-defect.json`.
