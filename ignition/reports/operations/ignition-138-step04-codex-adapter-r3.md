# IGNITION-20260824-138 — Step 04 Codex Live Adapter R3

The Codex adapter now has an explicit R3 mode in which the disposable task
workspace remains read-only and `--sandbox read-only` remains bound in the
literal argv. Runtime HOME, TMPDIR, CODEX_HOME and XDG cache/config/runtime
paths are redirected to one empty, attempt-specific writable scratch lease.
The lease is separate from the task workspace, formal repository, 1111
control repository and persistent user-document roots.

The adapter keeps `--ephemeral`, `--ignore-user-config`, `--ignore-rules`,
`--skip-git-repo-check`, the one-level child guard and the `repo.read`
permission ceiling. Dangerous bypass flags and widened workspace/effect
contracts remain rejected. Existing login state is represented only by an
opaque `auth://` reference; no credential content is read or materialized.

The R3 dispatch accepts completion only when the transport returns a
runtime-scratch receipt whose attempt binding, empty-start digest, transient
content policy and `CLEANED` status are all proved. The adapter also records
workspace before/after digests and the provider-neutral three-domain contract.
Missing scratch lifecycle support or failed cleanup is fail-closed.

The deterministic R3 adapter test used a local fake public CLI, not a model or
provider inference. It wrote a helper marker only into scratch; the task
workspace digest and modes remained unchanged, all scratch content was
cleaned, and the public JSONL event parsed successfully. The test also proves
that an R3 adapter refuses a transport without scratch lifecycle support.

The live-bridge targeted set ran 83 tests with zero failures, errors or skips.

Claim ceiling: Codex adapter R3 filesystem-domain binding and deterministic
fake-CLI lifecycle evidence only; no real Codex inference, validated live
completion, production readiness, external truth, Owner acceptance or
epistemic acceptance is inferred.
