# R0.2 `FAIL_READ_LEDGER_INVALID`: synthetic reproduction

Source checkout: `Arvin-liu/when-systems-catch-fire@047fb0ef0b4a734e42efb4a29b4e70b831ef0be4`.

## Scope

This reproduction uses only in-memory synthetic manifests and ledgers, the R0.2 read-ledger schema, validator, branch guard, and their protocol tests. It did not open Task182-R2's local case records, read ledger, packet manifest, or case contents. The actual private ledger root cause is not inferred.

The supplied minimal failure summary is preserved as: manifest SHA matched; authorization install and CHECK passed; the first COMMIT guard returned `FAIL_UNEXPLAINED_WORKTREE`; staging the three specified evidence items allowed COMMIT CHECK to pass; both records and the ledger passed JSON Schema; the manifest-listed ledger validator returned `FAIL_READ_LEDGER_INVALID`; no `PROTOCOL_CONTAMINATED` status occurred; Task182-R2 made no commit, push, or PR.

## Synthetic validator results

The fixtures run against the R0.2 validator and R0.2 read-ledger JSON Schema. Every fixture ledger is schema-valid.

| Synthetic fixture | Validator status |
| --- | --- |
| Entries and summary disagree | `FAIL_READ_LEDGER_INVALID` |
| Entries and trial disposition disagree | `FAIL_READ_LEDGER_INVALID` |
| A semantically clean row is marked contaminated | `FAIL_READ_LEDGER_INVALID` |
| Allowed manifest digest differs | `FAIL_READ_LEDGER_INVALID` |
| Manifest path differs | `FAIL_READ_LEDGER_INVALID` |
| Operational component is not listed | `FAIL_READ_LEDGER_CONTAMINATED` |
| Operational status exposes case-specific information | `FAIL_READ_LEDGER_CONTAMINATED` |
| Listed operational execution and finite status are clean | `PASS_READ_LEDGER_CLEAN` |

The machine-readable fixture and result summary is `r0-2-invalid-reproduction.json`. The reproducible harness is `ignition/evaluation/tests/test_task187_r0_2_synthetic_reproduction.py`. Source digests for the R0.2 schema, validator, branch guard, and authorization schema are recorded in the JSON.

## Closure sequence

R0.2 validates the ledger schema, manifest digest and path, entry semantics, recomputed summary, `CLEAN` trial disposition, and each row's `CLEAN` contamination disposition. It has no ledger closure marker, no frozen-ledger byte binding, and no independent final-validation receipt. The operational ledger model permits recording an execution and finite status for a validator component.

In the synthetic sequence, each validator run returns `PASS_READ_LEDGER_CLEAN` for its input ledger. Recording that run and its returned status appends two entries. The next input therefore grows from 0 to 2 to 4 entries and has a different SHA256 each time. If policy requires the final validator invocation and its resulting status to be present in the same ledger being certified, its result is always for the preceding ledger bytes; another run changes the ledger again. This reproduces a protocol self-reference and shows no finite fixed point under that rule.

This is conditional on treating the final validator's own invocation and returned status as entries in its certified ledger. The synthetic result does not establish why the private Task182-R2 ledger returned `FAIL_READ_LEDGER_INVALID`.

## COMMIT guard staging interaction

A synthetic repository reproduces the R0.2 guard lifecycle: untracked evidence returns `FAIL_UNEXPLAINED_WORKTREE`; staging it returns `PASS_BRANCH_AUTHORIZED`. Recording that pass in the ledger makes the ledger unstaged and the next COMMIT check returns `FAIL_UNEXPLAINED_WORKTREE` until the updated ledger is staged. This is an operational bookkeeping effect; the synthetic cognitive disposition remains `CLEAN` throughout.

## Root-cause classification

- `R0_2_IMPLEMENTATION_BUG`: not demonstrated by these synthetic fixtures.
- `R0_2_PROTOCOL_SELF_REFERENCE`: reproduced conditionally when the final validator invocation and status must be included in the ledger it certifies.
- `SUCCESSOR_BOOKKEEPING_ERROR`: not established without the private ledger.
- `UNRESOLVED_WITHOUT_PRIVATE_LEDGER`: retained for the actual Task182-R2 invalid result.

Schema success alone does not imply semantic ledger validity. The R0.2 summary/trial/row/manifest mismatches above are alternative synthetic routes to `FAIL_READ_LEDGER_INVALID`; none is attributed to the actual private ledger.
