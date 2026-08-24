# IGNITION-137 Step 08 — dry-run readiness

Status: `READY_FOR_ONE_LIVE_CODEX_ATTEMPT`

At 2026-08-24 06:12:18 UTC, the current public Codex CLI was re-probed as `codex-cli 0.144.4`. The executable digest and `codex exec --help` interface digest matched the fresh lease. Public login status returned success without recording credentials or tokens.

The fresh lease `live-codex-137-attempt-lease` is eligible for `repo.read` only, expires at 06:32:18 UTC, and covers the bounded 900-second attempt. The envelope binds `IGNITION-20260824-137`, `live-dispatch-137`, `live-attempt-137`, `external.codex`, `codex-live-r2`, the disposable fixture, the strict four-field output schema, `NO_BLIND_RETRY`, and `NO_NEW_BILLING_AUTHORITY`.

The parent child depth was 0 and the materialized child depth was exactly 1. No parent prompt or formal task context crosses the boundary. The generated argv has the public JSON, ephemeral, ignore-config/rules, read-only sandbox, external output-schema, and explicit `--cd` controls; no unsafe widening flag was present.

The OS coordinator reached `PREPARED` in temporary state, while `external_process_started=false` and `dispatch_call_count=0`. Therefore this step proves readiness only; it is not a live completion. The targeted 25-test gate passed with 0 failures, 0 errors, and 0 skips.

Claim ceiling: dry-run readiness only. Step 09 is authorized for exactly one live Codex synthetic/read-only attempt, with no blind retry.
