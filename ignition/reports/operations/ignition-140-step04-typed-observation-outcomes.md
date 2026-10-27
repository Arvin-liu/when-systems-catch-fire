# IGNITION-140 Step 04 — Typed Observation Outcomes

Status: `PASS`

Step 04 registers the typed boundary between public probe, transport, live
dispatch, live process, durable capture, structured result, and validator
outcomes. The historical Task139 sequence-4 zero is represented as
`probe_return_code=0` and `transport_return_code=0`; it has
`live_dispatch_calls=0`, `live_process_started=false`, and
`live_process_return_code=null`. Its preserved legacy value is explicitly
scoped as `PUBLIC_PROBE_TRANSPORT_VALUE_ONLY`.

New projections use `live-current-projection-r2`. Typed attempt summaries do
not expose the old unscoped `return_code` field; the legacy value is retained
only as `legacy_record_return_code_preserved` with
`legacy_return_code_scope`. Four historical records remain
`LEGACY_SCOPE_UNRECOVERED`, because this step does not infer process meaning
that the original evidence did not record.

The append-only ledger accepts an optional, schema-validated
`observation_typing` object for future attempts. The historical R1 projection
is still validated byte-for-byte, and the existing projection tool selects R1
or R2 from its explicit output filename so current historical material is not
silently rewritten in this step.

Evidence:

- typed projection digest: `b8fbe0690182dc4bed698d46007bcee1e35acb272757b8d6af18216ca7c3bbfe`
- historical R1 projection digest: `2769e67813ecae3b6dc321088fb44c845b6895c3c48ee841db289e7eac824f73`
- ledger head: `8ebe46858519650684d476609cea03f09340d5afb18bee1a9260a7e107851e9d`
- focused tests: `15 tests / 0 failures / 0 errors / 0 skips`

Claim ceiling: repository-local typed observation semantics and compatibility
only. No external process success, effect, production readiness, Owner
acceptance, or epistemic upgrade is inferred.
