# IGNITION-20260826-140 Step 12 — Independent live-attempt validation

## Result

Step12 independently validated the exact Task140 binding across task, dispatch,
attempt, executor family and capability lease. The canonical record is sequence
5 with a complete durable capture and a cleaned process group.

The typed boundary is explicit:

| Layer | Observed result |
|---|---|
| Public probe | return code `0`, two calls |
| Transport | return code `0` |
| Live dispatch | exactly one call; inference started |
| Live process | started, return code `1`, state `MALFORMED_RESULT` |
| Durable capture | `COMPLETE`; process group `CONFIRMED_GONE` |
| Structured result | absent |
| Independent result validator | `NOT_RUN_NO_EXACT_PUBLIC_RESULT` |

The legacy record's return code is retained with the scope
`LIVE_PROCESS_RETURN_CODE_OBSERVED`; it is not a public-probe return code. The
read-only fixture digest is unchanged. Current now derives six attempts, zero
validated completions, zero unreconciled attempts and two observation-incomplete
records. The live obligation remains `OPEN` because a process observation is not
the same thing as a validated completion.

The frozen policy forbids same-family blind retry. The fresh census had no second
safe executor family admitted, so no second live attempt was authorized. There is
no `LIVE_READONLY_VALIDATED_COMPLETION`; the task must remain fail-closed at this
boundary.

Machine evidence: [`step12-independent-validation.json`](../../data/operations/iterations/140/step12-independent-validation.json),
[`step11-live-attempt.json`](../../data/operations/iterations/140/step11-live-attempt.json),
[`live-observation-events-r1.jsonl`](../../data/operations/iterations/140/live-observation-events-r1.jsonl),
[`live-current-projection-r2.json`](../../data/operations/iterations/140/live-current-projection-r2.json).

Claim ceiling: repository-local exact binding, typed observation and
fail-closed Current validation only; no external effect, production readiness,
Owner acceptance or epistemic acceptance is inferred.
