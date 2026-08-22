# IGNITION-20260822-135 Step 01 — Canonical full regression runner

The repository now has one explicit orchestration wrapper, `ignition/tools/run_full_regression.py`, and one machine-readable contract at `ignition/data/operations/full-regression-runner-r1.json`.

The wrapper derives the formal repository from its own file path and confirms the Git toplevel. It invokes the existing unittest suite from the explicit application root `ignition`, with `PYTHONPATH` entries for the application, test modules and legacy foundation helper modules. This resolves the runner's working-directory boundary without changing test meaning or adding a test framework.

The runner performs a read-only exact-version dependency preflight from `ignition/requirements-foundation.txt`; it never installs packages or changes global configuration. It captures stdout/stderr and their SHA-256 digests, parses test/failure/error/skip counts, records the candidate HEAD, and compares clean Git status before and after the suite. Any precondition dirt, dependency mismatch, parse failure, skip, test failure/error or tracked/untracked post-run mutation is nonzero. It does not regenerate projections during the suite; Step 02 is a separate explicit preflight.

The supported natural window is at least 14,400 seconds. The runner has no kill timeout and marks a process complete only after normal subprocess return. A short test may finish sooner; the contract is the maximum observation window available to the caller, not an artificial kill threshold.

Contract/parser/dependency-read-only tests pass. This step establishes orchestration semantics only. It does not run the 47-minute full suite and does not claim that the current candidate is green.

Claim ceiling: repository-local runner contract and bounded targeted tests only; `CURRENT_WITH_OPEN_OBLIGATIONS` and `EPISTEMICALLY_ACCEPTED=0` remain unchanged.
