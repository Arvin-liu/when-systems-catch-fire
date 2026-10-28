# IGNITION-138 — Amendment-01 Step 06 Dynamic Admission

The census found five installed Agent candidates but admitted none at the
initial boundary. A read-only public re-attestation then selected Codex CLI
because its current surface is the most independently enforceable: JSONL and
output-schema results, `--ephemeral`, `--sandbox read-only`, ignored user
config/rules, explicit disposable `--cd`, the Pointfire child-depth guard, and
the R3 attempt scratch lifecycle. `codex login status` reported an existing
ChatGPT login; no credential content was read or copied.

Gemini CLI was explicitly rechecked and remains a real `AGENTIC_EXECUTOR`
candidate, not a reasoner or a tool. Its headless JSON/plan surface is strong,
but the current public CLI has no separate auth-source or ephemeral-home
boundary. Passing the real `~/.gemini` home would not satisfy the read-only
auth/config contract, so it remains blocked. Plain `gh` remains `TOOL_ONLY`;
the absent Copilot CLI was not downloaded. Hermes and OpenClaw retain their
existing reconciliation and safety blockers.

The new adapter path binds `CODEX_HOME` to an existing auth reference while
binding `HOME`, `TMPDIR`, and XDG runtime paths to the attempt-specific writable
scratch. It never reads auth contents or copies them into scratch. Metadata
before/after is observed without content reads; any change fails closed. The
synthetic task workspace remains an independent read-only directory.

The previous Codex attempt is allowed as the one repaired same-family
exception because it was a confirmed pre-inference startup failure with no
session, no structured result, no timeout/effect uncertainty, unchanged
workspace and a concrete repair. This is not a blind retry. Task138 still has
at most three real external invocations and will stop at the first independently
validated success.

Machine receipt: `ignition/data/operations/iterations/138/step06-amendment-01-dynamic-admission.json`.

Claim ceiling: repository-local dynamic admission and capability-lease evidence
only; no live result, validated completion, production readiness, model
ranking, external truth, Owner acceptance, or epistemic acceptance is inferred.
