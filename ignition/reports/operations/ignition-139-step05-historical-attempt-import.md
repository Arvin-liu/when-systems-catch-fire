# IGNITION-139 Step 05 — Historical Attempt Import

The four historical live attempts are now represented by the append-only `LiveAttemptLedger`. Source receipts remain unchanged.

| Seq | Task | Executor | State | Evidence | Reconciliation | Return | Validator |
| ---: | --- | --- | --- | --- | --- | ---: | --- |
| 0 | `IGNITION-20260823-136` | `external.hermes` | `TIMED_OUT_EFFECT_UNKNOWN` | `COMPLETE` | `REQUIRES_RECONCILIATION` | `-15` | `NOT_RUN` |
| 1 | `IGNITION-20260824-137` | `external.codex` | `FAILED_VALIDATION` | `COMPLETE` | `NOT_REQUIRED` | `1` | `FAIL` |
| 2 | `IGNITION-20260824-138` | `external.codex` | `STARTUP_FAILURE` | `COMPLETE` | `NOT_REQUIRED` | `1` | `NOT_RUN` |
| 3 | `IGNITION-20260824-138` | `external.codex` | `OBSERVATION_INCOMPLETE` | `INCOMPLETE` | `REQUIRES_RECONCILIATION` | `UNRECOVERED` | `UNKNOWN` |

## Canonical correction

Task138 second Codex dispatch is recorded as `OBSERVATION_INCOMPLETE`: it happened, the outer host lost the full observation after context overflow, and return code, structured result, lease receipt, workspace result, and validator input remain `UNRECOVERED`. The old narrative that it was forbidden is not imported as attempt fact.

## Integrity

- Ledger records: `4`; unique dispatches: `4`; unique attempts: `4`.
- Hash-chain head: `6acf6d4dcc55555e8890483e9fe04cfc58ab1eab663eeb06eadb8492b76b3b9e`.
- Historical source files were not modified.
- Raw/private process output was not imported; only bounded public receipt fields and stable source pointers are projected.

Claim ceiling: historical attempt import and append-only ledger integrity only; no external completion is inferred.
