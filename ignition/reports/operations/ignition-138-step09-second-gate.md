# IGNITION-20260824-138 — Step 09 Second-Invocation Gate

The concrete first-attempt startup defect was repaired in the bounded
transport: after validating an empty attempt scratch, it creates only the
declared `CODEX_HOME`, `XDG_CACHE_HOME`, `XDG_CONFIG_HOME` and
`XDG_RUNTIME_DIR` directories inside that scratch. It never creates anything
in the task workspace, formal repository, control repository, persistent user
documents or auth source. The transport regression was strengthened so the
child must observe those directories already present; the focused set ran 30
tests and the complete live-bridge targeted set ran 91 tests with zero
failures, errors or skips.

The Step08 hard-gate predicates were all true, but a final non-inference auth
probe under the repaired isolated runtime returned `Not logged in`. Current
public `codex login --help` and `codex exec --help` expose no separate
read-only auth-source reference. `CODEX_HOME` is the public auth/config
boundary; pointing it at the existing user auth root would also expose that
root to helper/runtime writes, while copying auth, creating a symlink escape,
or passing a secret token is forbidden by this task.

Therefore the second new real Codex invocation is `FORBIDDEN`, not retried.
No second dispatch/attempt was fabricated, no re-login/config/billing change
was made, and the real-inference invocation count remains exactly one. The
first attempt remains the classified pre-inference startup failure recorded in
Step08. The live completion obligation remains open.

Claim ceiling: specific scratch-path repair, hard-gate evaluation and
auth-source safety block only; no validated live completion, production
readiness, external truth, Owner acceptance or epistemic acceptance is
inferred.
