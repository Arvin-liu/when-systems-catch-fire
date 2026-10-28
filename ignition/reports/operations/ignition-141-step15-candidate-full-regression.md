# IGNITION-20260826-141 Step 15 — Candidate natural full regression

## Result

The repaired isolated candidate head
`429364bc8f5b9a07652f41303fd7d2106a24aaf5` completed the exact natural full
regression with **1260 tests, 0 failures, 0 errors and 0 skips**. The runner
completed naturally in `2983.884s` runtime / `2984.920s` elapsed, with no
watchdog, arbitrary timeout or process kill. The isolated dependency contract
passed with Python `3.14.6`, SymPy `1.14.0`, z3-solver `4.16.0.0` and
jsonschema `4.26.0`; the candidate tree was clean before and after the run and
generated-output drift was empty.

The machine receipt preserves both natural attempts. The first run was not
relabeled as green: it completed with **1260 tests, 2 failures, 0 errors and
0 skips**. The failures identified two concrete stale bindings: the full
regression contract still named Task140, and the system-map geometry contract
still named map version `0.14.0` after the Task141 current map advanced to
`0.15.0`. The runner contract, human-front-door map bindings and deterministic
system-map geometry were repaired; the focused closure then passed **16 / 16**.
The second natural run passed without adding skips, xfails, expected failures
or ignores.

The captures remain external to the formal repository and are preserved by
digest in the machine receipt:

- first attempt stdout SHA-256: `d0f1d35419064923c62db5d79d4414ba1f54dc7d32b3e446bf7de3e281859d3f`;
- first attempt stderr SHA-256: `7a67106b8b2053dbc0e7fdc610f6a9c2936a1da9dc8cd3872459ea85a771c807`;
- successful attempt stdout SHA-256: `a6af0ac70af23dde353adc3f2697b47ff4ec043928b49317616e1f33c569b440`;
- successful attempt stderr SHA-256: `2dbadd649ddfa4117a67c00648a8aac85460828bbf1eadb0fabd2aea73f75cf6`.

## Projection and live boundaries

The recorded projection preflight is a 25-check PASS with no failed checks,
release admission true and no side effects. Its formal worktree was still
dirty while the Step15 receipt was being assembled; the isolated candidate
tested above was clean. Step16 fresh-clone replay remains required.

No new live invocation occurred in Step15. The canonical typed projection
remains at six attempts, zero validated completions, zero unreconciled attempts
and two observation-incomplete records. The `LIVE_EXTERNAL_INVOCATION`
obligation remains `OPEN`, retry remains `NOT_AUTHORIZED`, and no offline test
creates a live completion claim.

Claim ceiling: exact repository-local candidate natural offline full-suite and
projection-repair evidence only; no fresh-clone, formal-main publication,
validated live completion, external truth, production readiness, Owner
acceptance or epistemic acceptance is inferred.
