# IGNITION-20260822-134 Step 10 — Full unittest discovery

Status: `TERMINAL_FAILURES_RECORDED`

The exact requested command was allowed to run to its natural terminal state:

```text
PYTHONPATH=ignition python3 -m unittest discover -s ignition/tests -p 'test*.py'
```

It ran for `2730.121` seconds and reported `Ran 1008 tests in 2730.121s`, followed by `FAILED (failures=22, errors=4)`. No arbitrary short timeout, process kill, skipped test or false PASS was used.

The dominant current Task134 finding is deterministic projection drift: the function-asset and nonfunction-claim generated outputs are stale after the new formal step artifacts entered the live source set. The nonfunction closure also reported `listed=4151 tracked=4419`. These are actionable current projection failures and remain release-blocking until regenerated and revalidated in Step 11.

The other observed classes are kept separate. The default interpreter still reports `T16_SYMPY_COUNTEREXAMPLE: SYMPY_UNAVAILABLE:ModuleNotFoundError`, while the declared isolated environment passed T16 in Step 09. Task104–106 reconciliation produced 18 historical diagnostics. Existing State Changelog entries fail the current field contract, and three errors expose tests that assume `ignition` as cwd even though the exact requested command was run from the repository root. An active Task133-specific witness binding also conflicts with a historical fixture and must be made ordinal-aware during the current migration.

No `ignore`, `skip`, residual broadening or validator weakening was used. Step 11 must repair only the current projection/identity failures, then rebuild the Current manifest and re-run targeted gates before closure.

Claim ceiling: exact repository-local full-discovery terminal evidence and failure classification only; no whole-project correctness, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
