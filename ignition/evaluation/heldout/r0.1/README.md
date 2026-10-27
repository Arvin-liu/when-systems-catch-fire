# Held-out Successor Protocol R0.1

This packet prepares but does not execute a Task182 successor trial. The visible
allowlist is generated and checked by `build_packet_manifest.py`; the sealed
criteria and evaluator preregistration instructions are outside that allowlist.
The source payloads are two new bounded objects, each with immutable source
commit, repository path, Git blob SHA, byte count, and SHA256 provenance.

Isolation is procedural. The manifest and read ledger make deviations
observable; they do not provide cryptographic access control in a full Git
clone. No case-specific gold or expected answer has been authored in the
successor-visible packet. Task183 must independently preregister source anchors
before reading Task182 outputs.

The four frozen dimensions and criteria are in
`evaluation-criteria-r0.1.json`. They report per case and do not combine into a
cognitive-inheritance or capability verdict.

## Complexity budget and retirement candidates

Added in this task: 3 JSON schemas (evaluation evidence, explicit transition,
successor read ledger), 1 evaluation policy contract, 1 shared admission class
and prefix rule, 1 path-classification category/schema value, 1 admission and
promotion helper, 1 target-repository preflight tool, 2 small Git hooks, 2
Task181 regression test files, 1 held-out manifest builder, 1 held-out output
schema, 1 evaluator criteria file, 1 receipt plus 2 case payloads and provenance
records, and concise protocol/readme artifacts. No new generated semantic
registry, Foundation copy, or provenance service is introduced.

Runtime overhead is bounded to path-policy checks, hashing the 14-file
allowlist, and JSON Schema validation when validating an evaluation artifact.
Migration burden is limited to path classification and the common admission
policy; evaluation artifacts remain auditable and are never auto-discovered as
semantic candidates.

When all evaluation and held-out records use a separately governed storage
plane with equivalent path accounting and provenance, the evaluation prefixes,
special admission class, and allowlist builder can be retired together. The
explicit transition schema can be merged into the repository's general
adjudication transition machinery if that machinery accepts typed source refs
without bypassing existing gates. Do not retain both implementations after such
a merge.
