# Future Task182-R2 Successor Contract

This contract prepares a future Successor task and does not start it. The
Successor role is limited to recording the two supplied cases. Do not act as
Builder, Evaluator, or Owner/GPT Adjudicator.

## Authority and branch

Use the separately issued Task182-R2 command. Create a new task branch from
the exact final head recorded by this R1 handoff and bind it with the
clone-local R0.2 authorization receipt. Do not reuse a historical or builder
branch. The supplied authorization template is descriptive and is not a
receipt. Stop before writing if command, base, repository, branch, identity,
push target, or guard status does not match.

## Read boundary

Read only this directory's cognitive file allowlist in packet-manifest.json,
the manifest itself, and the R0.2 read-ledger schema. Record every cognitive
read with its path, purpose, digest, exposure fields, and disposition.
Operational hooks and guards may execute and return only finite listed status
codes; do not open their source, the local authorization receipt, or explain
their implementation. Do not read evaluator-sealed paths, pull-request
narrative, Task180 or earlier Task182 results, or any prior case output.

For each cognitive read, record action kind COGNITIVE_READ, content exposure
YES, the exact manifest-listed file digest, and whether case-specific content
was exposed. Record the manifest read with its own byte digest. For a tool
invocation, record OPERATIONAL_EXECUTION with content exposure NO; record its
finite return code separately as OPERATIONAL_STATUS_OBSERVED, also with content
exposure NO and case-specific-information-exposed false. If operational output
contains case-specific information, or any prohibited source is actually
opened, record PROHIBITED_COGNITIVE_READ / CONTAMINATED and stop. Recompute the
ledger counts and trial disposition from the entries.

## Records

For each case, create one record conforming to
successor-output-r0.2.schema.json. Cite source locators and distinguish
observations from source-reported claims, interpretations, hypotheses, and
unknowns. Preserve boundaries and unresolved obligations. Include one bounded
proposal with prerequisites and a stop condition. Do not invent expected
answers, gold relations, a transition result, human confirmation, or evaluator
criteria.

Write only to
ignition/reports/evaluations/ignition-182-heldout-successor-r0-2/. Validate
both records against the supplied schema before freezing S1. The R0.2 ledger
validator, if invoked, is an execution-only component and may return only its
listed status.

## Evidence and stop rules

Before claiming that an S1 commit was or was not pushed, confirm its parent
chain and the exact remote branch ref. A failed or ambiguous check does not
prove a local-only state. If any unlisted cognitive content or prohibited
operational source is exposed, preserve forensic evidence, record
PROTOCOL_CONTAMINATED, and stop without repairing that trial.

Do not run an evaluator, self-grade cognitive inheritance or capability, read
PR narrative as task evidence, or infer general cognitive inheritance. The
normal successor lifecycle is HELD_OUT_SUCCESSOR_RETRY_COMPLETE; evaluation
and Owner/GPT adjudication remain separate later roles.
