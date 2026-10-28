# IGNITION-20260825-139 Step 10 — Single-live-attempt admission freeze

## Result

`PASS`: the only currently admitted candidate is `external.codex`, and Step10
froze one bounded dispatch envelope without starting inference. The fresh Codex
lease came from two real public probes (`codex --version` and `codex exec
--help`), with no secret content read and no configuration or billing change.

The lease is `lease-ignition-139-codex-live-01` for `codex-cli 0.144.4`, with
binary digest `134063e133f0b4244fa3b251acf973d4fe4b4aeeacbdc135211bf480f59f1477`
and interface digest
`9f86f0115238ddde2514587e5f95b0ab0aa6b89495e5912878d49ad26038aa19`.
Capability admission is the strict OS/executor intersection: effective
capability `repo.read` only. The envelope is bound to
`dispatch-139-live-01` / `attempt-139-live-01`, uses a disposable synthetic
read-only fixture, a 90-second bound, `NO_BLIND_RETRY`, and
`NO_NEW_BILLING_AUTHORITY`.

## Boundary evidence

- The task workspace is read-only and separate from attempt runtime scratch.
- Host durable capture is available, with the capture parent separate from the
  runtime-scratch parent.
- The auth source is a read-only reference; content was not read or copied.
- The one-level child guard passed; recursive Agent spawning is rejected.
- The Codex argv shape includes JSON, ephemeral, ignored-user-config/rules,
  read-only sandbox, explicit workspace and strict output-schema flags. Unsafe
  widening tokens are rejected.
- The independent `LivePilotValidator` binding self-test passed for the exact
  task, dispatch, attempt and executor identities. This is a validator freeze,
  not a live result.

Current still projects four historical attempts, zero validated completions,
two unreconciled attempts and one observation-incomplete attempt. Its open
obligation and ceiling remain
`LIVE_EXTERNAL_INVOCATION_OPEN_NO_VALIDATED_COMPLETION`; the 138 second Codex
attempt is not rewritten as “not run”.

Machine evidence: [`step10-live-admission.json`](../../data/operations/iterations/139/step10-live-admission.json) and
[`run_task139_live_admission.py`](../../tools/run_task139_live_admission.py).

## Next gate

Step11 may perform at most one live dispatch using this frozen envelope. The
process must be captured before model-visible summarization, then Step12 must
bind the result to the exact task/dispatch/attempt/executor/lease and run the
independent validator. A timeout, incomplete observation, malformed output or
validator failure is terminal for this attempt; no blind retry is authorized.

Claim ceiling: repository-local admission and boundary evidence only; no live
inference, completion, model-quality judgment, production readiness, external
truth, Owner acceptance or epistemic acceptance is inferred.
