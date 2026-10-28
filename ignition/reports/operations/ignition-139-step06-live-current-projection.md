# IGNITION-20260825-139 Step 06 — Deterministic Live Current Projection

The public live-attempt status is now derived from the append-only ledger at
`ignition/data/operations/iterations/139/live-attempt-ledger.jsonl`. The
projection contains no raw provider output, private session data, or model
context.

| Derived fact | Value |
| --- | --- |
| Total attempts | `4` |
| Executor counts | `external.codex: 3`; `external.hermes: 1` |
| Validated completions | `0` |
| Unreconciled attempts | `2` (`live-hermes-136-initial`, `attempt-138-live-02`) |
| Observation-incomplete attempts | `1` (`attempt-138-live-02`) |
| Latest Codex attempt | `attempt-138-live-02` — `OBSERVATION_INCOMPLETE` |
| Latest validated completion | `null` |
| Current live ceiling | `LIVE_EXTERNAL_INVOCATION_OPEN_NO_VALIDATED_COMPLETION` |
| Next eligible action | `RECONCILE_UNRECOVERED_ATTEMPTS` |

The Task138 second Codex attempt is therefore a ledger-derived historical
fact: it happened, but observation evidence is incomplete. The projection does
not infer a return code, structured result, lease result, workspace result, or
validator input.

## Determinism and integrity

- Two independent builds are byte-identical.
- Projection validator: `LIVE_CURRENT_PROJECTION_OK`.
- Ledger head: `6acf6d4dcc55555e8890483e9fe04cfc58ab1eab663eeb06eadb8492b76b3b9e`.
- Projection digest: `0bfa042fe6f2ccc64e4b133babf0fdfb220f9aa75367d7458da72598db50aa1a`.
- A tampered count fails closed; the append-only ledger remains the only
  attempt source for this projection.

Claim ceiling: deterministic repository-local live-attempt projection only;
no external truth, production readiness, Owner acceptance, or epistemic
upgrade is inferred.
