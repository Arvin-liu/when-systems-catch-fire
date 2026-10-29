# Audit Finding Comparator R0

`maintenance.compare_audit_findings` compares two caller-supplied audit records that declare the same scope, target, and target revision. It reports finding coverage, disposition disagreements, and evidence-reference differences as a bounded JSON result.

The comparator does not perform an audit. It does not read evidence references, authenticate records or reviewers, establish that reviewers are independent, decide whether a finding is true, or authorize a repository action. Different `reviewer_ref` values are only caller declarations and are reported as unauthenticated. Matching dispositions do not establish correctness.

## Input and output

Input is one UTF-8 JSON request matching `schemas/operations/toolbox-audit-finding-comparison-r0.schema.json`. Each finding contains only a stable ID, a caller-declared disposition (`CONFIRMED`, `NEEDS_VALIDATION`, `REJECTED`, or `OUT_OF_SCOPE`), and source references with caller-supplied SHA-256 values. Raw audit notes, excerpts, credentials, and hidden reasoning are not accepted.

The tool rejects unequal audit scopes, targets, or revisions. It caps stdin at 256,000 bytes, each audit at 100 findings, each finding at 20 evidence references, and text fields at 512 characters. Duplicate object keys, duplicate findings, duplicate evidence identities, malformed hashes, and unknown fields fail closed with no partial JSON output.

Output records caller-declared matches and differences. It keeps `claim_truth=NOT_EVALUATED`, `evidence_authenticity=NOT_VERIFIED`, `reviewer_independence=NOT_ESTABLISHED`, `decision_authority=NONE`, and `execution_authorized=false` for every result.

## Invocation

```sh
python3 -B ignition/tools/toolbox_audit_finding_comparator.py --stdin < audit-finding-comparison.json
```

The tool is a local, read-only, optional CLI. It uses only the Python standard library, reads stdin, writes JSON to stdout, and performs no file reads, file writes, network requests, secret access, billing, or external action.

## Comparison with existing tools

- `research.validate_evidence_program_snapshot` runs the repository's fixed evidence-program validator; it does not compare two audit records.
- `maintenance.attribute_actions_validation_evidence` aligns a validation plan and its targets with an Actions run snapshot; it does not reconcile audit finding sets.
- `knowledge.navigate_raw_evidence` searches the checked-out Knowledge index and opens bounded source lines; it does not compare caller-supplied review dispositions.

These tools have separate inputs and outputs. The comparator has a narrow additional use for showing what two same-target reviews agree on, disagree on, or leave uncovered. Evidence does not establish that it replaces any existing tool; all remain available for their separate tasks.

## Claim ceiling and rollback

Local schema, unit, negative-control, and route tests establish deterministic record comparison only. A real-record invocation can show that the tool parses and compares the supplied audit records; it cannot establish independent review, external truth, or a quality improvement. The candidate is default-off. Rollback removes this candidate entry, its implementation, schemas, tests, generated identity projection, and evidence files; it does not change a Current operation or existing review record.
