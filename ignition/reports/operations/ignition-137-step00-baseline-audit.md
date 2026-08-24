# IGNITION-20260824-137 — Step 00 Baseline Audit

The live control ref was refreshed before this task. `origin/relay/current` is
`e5529e107e2fbed9bddf7b9e0b621fae477727cb`, whose task pointer is IGNITION-137
and whose task material is `fc0ad277`.

The formal repository's current `origin/main` and the new task worktree are
both `a1766ec1b96f59eaca45c013cda574cd5224b78f`. Task136's machine receipt
contains the earlier pre-publication baseline `3acf15ea4c1b1c27eb6e8b9cadbc4f0526bdfddb`;
this is recorded as observed publication drift, not treated as a reason to
rewind the formal repository.

Task136 evidence was re-read from its formal result, machine receipt, live
preflight and execution receipt. The Hermes attempt remains
`TIMED_OUT_EFFECT_UNKNOWN` with unchanged fixture bytes and open
reconciliation. OpenClaw remains skipped at its unsafe workspace/channel
boundary. Codex is eligible for a bounded read-only attempt, but no validated
completion was observed. Accordingly, `LIVE_EXTERNAL_INVOCATION` remains open.

Task136's declared candidate and fresh-clone natural regression evidence is
`1131 tests / 0 failures / 0 errors / 0 skips`. This is the baseline evidence
for the current task; the current task must not weaken it or turn an executor
return into completion without independent OS validation.

The two closure targets are deliberately narrow: reconcile the old Hermes
timeout without rewriting its receipt, and obtain at most one new Codex
synthetic/read-only live attempt under a one-level child/reentrancy boundary.
If the attempt fails or times out, the failure remains the terminal evidence;
there is no blind retry.

Claim ceiling: this audit records repository-local baseline evidence only. It
does not establish validated live completion, production readiness, Owner
acceptance or epistemic acceptance.
