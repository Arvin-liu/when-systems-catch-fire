# IGNITION-20260824-138 — Step 00 Baseline Audit

The live control ref was refreshed before this task. `origin/relay/current` is
`556dda03ec5019480e79d474910abe836f6f099e`, which points to the IGNITION-138
task material at `6c7e01c5`. The formal repository was fetched with
`--all --prune`; its verified `origin/main`, remote `refs/heads/main`, and the
new isolated worktree all resolve to
`e22013b0c01cdcce052b9fd8a3c85c31798f3f51`.

The isolated formal branch is
`codex/ignition-138-executor-runtime-scratch-live-codex-r1-20260824`. Its
worktree was clean before the audit and no live inference was started.

Task137's durable evidence was re-read without modification. The Codex
attempt returned code 1 after `0.463087` seconds, emitted zero stdout bytes,
had no structured result or session pointer, and its process group was
`CONFIRMED_GONE`. The fixture digest was unchanged. This is retained as a
`KNOWN_NO_EFFECT_PRE_INFERENCE_STARTUP_FAILURE`, not a completion and not a
reason for an unbounded retry.

## Causal ledger

| Domain | Observed boundary | Evidence | Conclusion |
| --- | --- | --- | --- |
| `TASK_WORKSPACE` | Fixture was `DISPOSABLE_READ_ONLY`; the implementation applies file mode `0444` and directory mode `0555`. | Task137 fixture implementation and `step09-live-codex-attempt.json` read-only guard. | The task workspace must remain read-only. |
| `EXECUTOR_RUNTIME_SCRATCH` | No independent scratch domain existed. `LiveChildContext.child_environment()` set both `HOME` and `TMPDIR` to the fixture; an inherited `CODEX_HOME` was also allowed by the environment list. | `ignition/agent_federation/live_child_guard.py`, `live_adapters.py`, and the Task137 stderr receipt. | Codex's helper/app-server startup was forced to write into the read-only fixture or a path derived from it. |
| `AUTH_OR_CONFIG_SOURCE` | Public auth status was observed as logged in. Secret/token contents were not read; `CODEX_HOME` was unset in the parent environment and no config or billing mutation was attempted. | Read-only `codex login status`; environment presence-only probe. | Auth remains a read-only prerequisite, not a copied credential or new authority. |
| Startup operation | Codex 0.144.4 reported refusal to create helper binaries under the temporary directory, then `failed to initialize in-process app-server client: Permission denied (os error 13)`. | Sanitized Task137 stderr receipt; zero public events. | Failure occurred before meaningful inference or result production. |

The root cause is therefore a filesystem-authority conflation, not a model,
quota, timeout, or billing failure. The repairable design is to preserve the
fixture's `0555/0444` boundary while allocating an attempt-specific writable
runtime scratch directory outside the fixture, formal repository, 1111, and
persistent user-document trees. Existing auth may be referenced read-only;
its contents must not be copied or changed.

## Public surface and deterministic preflight

The public CLI probe observed `codex-cli 0.144.4`, the required JSONL,
ephemeral, read-only sandbox, config/rules-ignore, explicit `--cd`, and output
schema surfaces. `codex login status` reported a logged-in public status only.
The Task137/bridge targeted deterministic preflight ran 41 tests with zero
failures, errors, or skips. `validate_execution_contract.py --check` and
`validate_current_release_lifecycle.py --check` passed. The release-candidate
identity validator's only finding was the expected transitional branch-name
mismatch: the repository's canonical Current task is still 137 until the
IGNITION-138 Current-surface step; it is recorded rather than hidden.

Relevant parent environment presence was recorded only by class:
`HOME=SET(<home>)`, `TMPDIR=SET(<tmp>)`, `XDG_CONFIG_HOME=UNSET`,
`XDG_CACHE_HOME=UNSET`, `XDG_RUNTIME_DIR=UNSET`, `CODEX_HOME=UNSET`.

No live inference was run in Step 00. The next step must establish a
provider-neutral machine contract for the three filesystem domains and fail
closed on overlap, persistence, path escape, writable task workspace, auth
mutation, or secret materialization.

Claim ceiling: repository-local baseline, public-surface, and Task137 failure
causal evidence only. This step does not establish validated live completion,
production readiness, Owner acceptance, external truth, or epistemic
acceptance.
