# IGNITION-20260824-138 — Amendment 01 live Codex receipt reconciliation

The repaired second Codex family attempt was started with the explicit
`gpt-5.6-luna` model and `max` reasoning effort, after the first attempt had
been proven to be a pre-inference runtime-scratch startup failure. The outer
execution tool then reported that its output exceeded the available model
context. No resumable tool session or durable stdout/stderr capture was
available afterward; a read-only process check found no live Codex child and
no remaining `live-02` attempt scratch directory.

This is not evidence of either success or failure of the child. The exact
return code, lease receipt, structured result, and independent validation
receipt were not recoverable, so Pointfire does not promote the attempt and
does not claim `LIVE_READONLY_VALIDATED_COMPLETION`. The validator was not
run against an invented or reconstructed result.

The task-wide budget remains bounded at three real external invocations, but
the Codex family default limit and `NO_BLIND_RETRY` rule forbid starting a
third same-family call merely to replace a lost receipt. No new executor
family passed dynamic admission. The historical
`LIVE_EXTERNAL_INVOCATION` obligation therefore remains open.

Claim ceiling: host-side receipt-recovery evidence only; no external truth,
production readiness, Owner acceptance, publication, or epistemic acceptance
is inferred.
