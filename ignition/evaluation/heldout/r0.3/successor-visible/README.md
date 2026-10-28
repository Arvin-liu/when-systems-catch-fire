# R0.3 Held-Out Successor Packet

This packet prepares a new held-out trial for `IGNITION-20260918-182-R3`.
Task187 built the protocol and two fresh synthetic cases; it did not run a
Successor or Evaluator and supplies no inheritance evidence.

## Included inputs

- `cases/EXPERIENCE-RESEARCH-01.md` — bounded synthetic room-experience notes.
- `cases/ENGINEERING-GOVERNANCE-01.md` — bounded synthetic change-window
  notes.
- `cases-manifest-r0.3.json` and its SHA256 file — case IDs, provenance, and
  source pins.
- `task-contract-r0.3.md`, `method-contract-r0.3.md`, and
  `capability-interface-r0.3.md` — the trial boundaries and provider-neutral
  response shape.
- `successor-output-r0.3.schema.json` — the response structure.
- `successor-read-ledger-r0.3.schema.json` and
  `successor-ledger-validation-receipt-r0.3.schema.json` — read accounting
  and the separate final-status interface.
- `packet-manifest-r0.3.json` — the exact cognitive allowlist and operational
  component inventory.

## Evidence boundaries

Only files listed in `cognitive_evidence_surface.files` may be opened as
cognitive evidence; every such read belongs in the R0.3 ledger with its
content digest. The packet separates `CERTIFIED_LEDGER_SCOPE` from
`FINAL_ATTESTATION_SURFACE`. All operational tools and hooks are
`EXECUTE_STATUS_ONLY`; their source and the clone-local authorization receipt
must not be read by the Successor. The Successor also must not read the final
validation receipt, evaluator-sealed materials, answer keys, or gold data.

Before the trial, the Owner or Builder must provide the exact successor task
command and provision the corresponding local authorization receipt. Run
`bootstrap-r0.3.sh` to obtain only the finite branch-guard status. This packet
does not itself authorize a branch mutation or a GitHub write.

After all intended in-scope reads and operational status observations have
been recorded, close the ledger once and run the manifest-listed R0.3
finalizer. It freezes the ledger and creates the independent receipt at the
Owner-provided path outside this packet. The Successor observes only the
finite status; it cannot read the receipt. No further ledgered operation may
be added after closure.

All names, counts, statements, and events in both cases are synthetic. The
cases contain no expected relations, continuation, answer, scoring rubric,
or evaluator key. The trial output is an evidence artifact, not a verdict
about cognitive inheritance.
