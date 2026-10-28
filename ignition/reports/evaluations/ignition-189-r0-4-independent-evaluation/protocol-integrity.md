# R0.4 protocol integrity

Artifact type: `EVALUATION_EVIDENCE`
Task: `IGNITION-20260919-189-R0.4`
Stage: Step01, before semantic evaluation

Disposition: `PROTOCOL_INTEGRITY_PASS`

The Successor output, closed read ledger, and final validation receipt were frozen under `frozen-successor-evidence/`. The three copies are byte-identical to their local Successor sources. Their SHA-256 values, the packet manifest digest, and the case manifest digest are recorded in `evidence-freeze.json` and `protocol-integrity.json`.

Mechanical checks passed:

- Successor output, closed ledger, packet manifest, case manifest, and receipt all pass their R0.4 JSON Schemas.
- The Task188 exact-head finalizer returned `PASS_READ_LEDGER_CLEAN` when run against the frozen copy.
- Ledger state is `PRE_FINAL_VALIDATION_CLOSED`; trial disposition is `CLEAN`; the 22-entry summary and closure summary agree.
- All 18 cognitive reads resolve to the manifest or its allowlisted cognitive files with matching digests.
- `case_specific_information_exposed=true` occurs only on the two case sources and two provenance files, all through `COGNITIVE_READ`.
- All four operational rows have `content_exposure=NO`, no case-specific information, and no digest.
- There are zero prohibited cognitive reads, zero contaminated entries, and no evaluator-sealed path in the ledger.
- The receipt binds the exact ledger SHA, packet manifest SHA, task ID, finalizer source SHA, and validator status. It is outside the certified packet surface.
- The frozen ledger and receipt SHA-256 values were unchanged before and after finalizer verification; no validator writeback occurred.

No semantic case verdict was performed in this step. The result authorizes proceeding to the blind case evaluation under the command's boundaries. This evidence has no canonical claim IDs and no canonical promotion.

Provenance: `ignition/evaluation/heldout/r0.4/successor-visible/`, frozen local Successor evidence, and the Task188 exact-head R0.4 finalizer. The evaluator-sealed surface and prior evaluator/Successor outputs were not used for this step.
