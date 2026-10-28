# IGNITION-137 Step 09 — one real Codex synthetic/read-only attempt

The single authorized Codex live dispatch ran at 2026-08-24 06:16:05 UTC with a fresh `codex-cli 0.144.4` lease, `repo.read` ceiling, disposable fixture, strict output schema, 900-second deadline, depth-one child guard, `--skip-git-repo-check`, read-only sandbox, and no new billing authority.

The process exited in 0.463087 seconds with exit code 1. It did not time out, emitted no stdout events, and its process group was `CONFIRMED_GONE`. The public startup failure was deterministic: Codex attempted to create helper binaries under its temporary HOME/Codex directory, but that directory was the read-only fixture. The process therefore never returned a structured Task137 result. Pointfire recorded `MALFORMED_RESULT`; the durable dispatch is `FAILED_VALIDATION`, not `COMPLETED_VALIDATED`.

The fixture digest stayed exactly `a4993a9ba29920bacecee2575c544053a499c57e906cd5d2189536ed493910f7` before and after, the read-only guard remained true, and the formal worktree HEAD stayed `d2e949b58a6542c4a7bfb9f8b3c240f2735012e9`. No session pointer, channel, browser, remote Git, user-data, or formal-repo mutation was observed.

This is a genuine external invocation receipt, but not a validated live completion. Independent answer validation was not run because there was no exact public result to validate. The task’s Step 09 rule requires the malformed attempt to be preserved and forbids blind retry; therefore retry is recorded as `NOT_RUN_NO_BLIND_RETRY`.

The observed startup constraint is now explicit for future task design: a read-only fixture workspace must be paired with a separate writable disposable runtime HOME/TMPDIR. That correction is not applied by replaying this attempt.
