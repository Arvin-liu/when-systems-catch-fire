# Evaluation Evidence Plane

R0.1 remains a frozen historical protocol and evidence plane. R0.2 keeps the
existing typed EVALUATION_EVIDENCE classification and promotion boundary,
while correcting the held-out trial model.

The R0.2 successor packet explicitly separates:

- COGNITIVE_EVIDENCE_SURFACE: the manifest-listed task/method contracts,
  capability interface, output and ledger schemas, provenance, and two new
  bounded synthetic sources. These paths may be read and must be ledgered.
- OPERATIONAL_CONTROL_SURFACE: hooks, task branch guard, and read-ledger
  status tool. These may execute and return finite status codes; their source
  and authorization receipt may not be opened or interpreted.

The R0.2 typed read ledger mechanically distinguishes cognitive reads,
operational executions, status observations, and prohibited cognitive reads.
Only actual exposure of unlisted content, operational source, or
case-specific/gold/evaluator information through an operational result
contaminates a trial. A status-only hook execution is not a cognitive read.

The two R0.2 cases are newly authored and are unrelated to the earlier
successor-visible payloads. The evaluator-sealed path is a sibling of the
successor-visible packet and is excluded from its manifest. No R0.2 answer
key or evaluation criteria are authored by the Builder.

Evaluation evidence remains noncanonical by default. This work does not
promote any evaluation record to a Foundation claim or asset, and makes no
general cognitive-inheritance claim.

## R0.3 ledger closure

R0.3 supersedes R0.2 only for final read-ledger closure. The R0.3 contract
separates `CERTIFIED_LEDGER_SCOPE` from `FINAL_ATTESTATION_SURFACE`, freezes
ledger bytes at `PRE_FINAL_VALIDATION_CLOSED`, and binds the final validator
status in a deterministic receipt outside the ledger. R0.2 artifacts remain
historical. See `r0.3-ledger-closure-protocol.md`, the R0.3 packet schemas,
and `tools/finalize_successor_read_ledger_r0_3.py`.

R0.3 uses a versioned task authorization schema, branch guard, and hook path
for the new held-out trial. Its source and finite status vocabulary are
operational controls, not cognitive evidence; see
`operational-control/r0.3/README.md`.
