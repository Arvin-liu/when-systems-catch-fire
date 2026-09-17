# Future Task182 Successor Contract

This packet defines a future trial only. It does not start Task182.

For each case listed in `packet-manifest.json`, create one successor record that
follows `method-contract.md`, the provider-neutral interface, and
`successor-output-r0.1.schema.json`. Reference only the supplied raw object and
its provenance record. Use explicit locators and preserve the source's scope.

The record must include observations, objects, relations, uncertainty,
boundaries, unresolved questions, obligations, a bounded proposed continuation,
and a claim ceiling. Keep any transition suggestion labeled as a proposal and
leave unknown target state unresolved. Do not mutate canonical files, run an
evaluator, read R0 fixture/gold files, or consult any file omitted from the
allowlist.

Output records must be written under
`ignition/reports/evaluations/ignition-182-heldout-successor-r0-1/`. Output
records and the required read ledger are evaluation evidence. Record
every read path, purpose, and SHA256 using
`ignition/evaluation/schemas/successor-read-ledger-r0.1.schema.json`. A nonzero
out-of-scope read count or any observed out-of-scope read means
`PROTOCOL_CONTAMINATED`; stop and disclose it without trying to repair the
record in the same trial.
