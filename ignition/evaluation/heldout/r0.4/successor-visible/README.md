# R0.4 Held-Out Successor Packet

This packet prepares a future held-out trial for `IGNITION-20260919-188-R0.4`. It is a Builder-created protocol artifact. This task does not run a Successor or Evaluator and supplies no inheritance evidence.

## Included inputs

- `cases/IGNITION-20260919-188-EXP-01.md` — a bounded synthetic experience/content research case.
- `cases/IGNITION-20260919-188-GOV-01.md` — a bounded synthetic engineering/governance case.
- `cases-manifest-r0.4.json` and its SHA256 file — case IDs, provenance, and source pins.
- `task-contract-r0.4.md`, `method-contract-r0.4.md`, and `capability-interface-r0.4.md` — trial boundaries and the provider-neutral response shape.
- `successor-output-r0.4.schema.json` — the response structure without answer, score, or continuation fields.
- `successor-read-ledger-r0.4.schema.json` and `successor-ledger-validation-receipt-r0.4.schema.json` — read accounting and the separate final-status interface.
- `packet-manifest-r0.4.json` — the exact cognitive allowlist and operational component inventory.

## Case exposure semantics

The Successor is expected to read the two held-out case sources and their provenance files. Those reads are cognitive reads through the manifest allowlist, so `content_exposure=YES` and `case_specific_information_exposed=true` are normal ledger values and derive `CLEAN` when the path and digest match.

`CASE_SPECIFIC_INFORMATION_EXPOSED_IS_CHANNEL_CONTEXT_NOT_CONTAMINATION_BY_ITSELF`.

An operational execution or status observation must never expose case-specific information. Case-specific information observed through an operational/control channel is `CONTAMINATED`. An unlisted cognitive path or prohibited cognitive read is also `CONTAMINATED`.

## Evidence boundaries

Only files listed in `cognitive_evidence_surface.files` may be opened as cognitive evidence; every such read belongs in the R0.4 ledger with its content digest. Operational tools are `EXECUTE_STATUS_ONLY`; their source and the clone-local authorization receipt are not cognitive evidence. The final validator is outside the certified ledger scope and writes a separate receipt outside this packet. The Successor observes only its finite status and must not read the receipt.

Before a future trial, the Owner must provide the exact task command and provision the corresponding local authorization receipt. Run `bootstrap-r0.4.sh` only for its finite branch-guard status. This packet does not itself authorize a branch mutation or a GitHub write.

All case facts are synthetic. The cases contain no gold answer, expected relation, expected continuation, evaluator answer, score, or real personal data. The trial output is an evidence artifact, not a verdict about cognitive inheritance.
