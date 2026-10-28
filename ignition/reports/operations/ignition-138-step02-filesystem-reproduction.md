# IGNITION-20260824-138 — Step 02 Deterministic Startup-Failure Reproduction

No model or live Codex invocation was started. A bounded Python subprocess
harness was used to mimic only the public startup filesystem operations
observed in Task137: create a helper directory/file under the effective
`CODEX_HOME`/`HOME`, create a runtime file under `TMPDIR`, and then emit one
structured readiness event.

| Case | Return | Structured result | Workspace unchanged | Scratch changed | Cleanup | Classification |
| --- | ---: | --- | --- | --- | --- | --- |
| `readonly_home_and_tmpdir` | 1 | no | yes | no | yes | pre-inference permission denial |
| `isolated_writable_runtime_scratch` | 0 | yes | yes | yes | yes | repaired startup boundary |
| `codex_home_workspace_collision` | 1 | no | yes | no | yes | `CODEX_HOME` collision with task workspace |
| `tmpdir_workspace_collision` | 1 | no | yes | yes | yes | `TMPDIR` collision with task workspace |
| `runtime_scratch_permission_mismatch` | 1 | no | yes | no | yes | scratch itself not writable |
| `isolated_runtime_after_permission_repair` | 0 | yes | yes | yes | yes | repaired startup boundary remains deterministic |

The matrix reproduces the causal distinction required by IGNITION-138:
runtime writability is necessary for the executor's own startup, while it
does not require or permit task-workspace writability. The two successful
cases changed only transient scratch metadata and left the read-only fixture
digest unchanged. All scratch roots were cleaned in a `finally`-equivalent
harness path.

The parent-environment probe passed with
`parent_marker_present=false`: only the explicit PATH/HOME/TMPDIR allowlist
was supplied to the child. The Step01 validator tests additionally reject
domain-root symlink aliases, in-tree symlinks, domain overlap, protected
formal/1111/user-document roots, writable auth references, secret-like env
names, unknown domains, and undeclared scratch persistence.

This is deterministic filesystem evidence, not evidence about model quality,
inference completion, external effects, or billing. The next step may extend
the existing bounded process transport with this contract and a real
attempt-specific scratch lifecycle.
