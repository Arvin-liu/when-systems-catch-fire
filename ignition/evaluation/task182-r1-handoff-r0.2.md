# IGNITION-20260918-182-R1 — Task182 R0.2 Repair Handoff

**Lifecycle:** READY_FOR_HELD_OUT_SUCCESSOR_RETRY

## Authority and Formal branch

- Authority command: Arvin-liu/1111:agent-commands/IGNITION-20260918-182-R1.md
- Command ref: ca1f8c1780001aaef07f6e82c87b67b5d14ce237
- Command blob: baed4ede38b22de2885510d36fed17595e3354d4
- Sole Formal target: Arvin-liu/when-systems-catch-fire
- Exact Task181 base: 7cab7541895620d68d5bce2d16c46871ebd03ac0
- Repair branch: work/IGNITION-20260918-182-r1-heldout-protocol-repair
- Stacked Draft PR base: work/IGNITION-20260917-181-cognitive-inheritance-r0-1-isolation-protocol
- Exact final repair head and its matching Draft PR, workflow runs, and clean-clone evidence are recorded in the Draft PR description after final verification.

## Task182 R0.1 contamination adjudication

The first trial is PROTOCOL_CONTAMINATED. Its reported push was rejected with
FAIL_TASK_BRANCH_MISMATCH; the R0.1 preflight is bound to the Builder branch,
and the protocol counted execution of an operational hook as a cognitive
out-of-scope read. This is a protocol and execution-substrate defect, not a
successor cognition failure.

The remote branch
work/IGNITION-20260917-182-heldout-successor-r0-1-trial was observed at
985ad8953a0eb7777817bee86ef086a739303f45. That disclosure commit's parent is
5aecee5d4b6becaa954e5882d6869a292d393725; the S1 candidate's parent is the
Task181 base 7cab7541895620d68d5bce2d16c46871ebd03ac0. The S1 candidate is
therefore remotely reachable as an ancestor of the contamination branch tip.
The original disclosure statement that the candidate “remains local and was
not pushed” is false as a claim of remote non-reachability. The exact push
operation and any separate S1 ref are not established.

The original contamination branch remains preserved and permanently
quarantined as clean-trial evidence. It is not rewritten, amended, force-pushed,
deleted, reused as a clean retry, or used to infer cognitive inheritance
success or failure. See
ignition/reports/evaluations/ignition-182-protocol-repair-r1/task182-contamination-adjudication.json
for the typed adjudication receipt.

## R0.2 protocol repair

The successor-visible packet manifest separates
COGNITIVE_EVIDENCE_SURFACE from OPERATIONAL_CONTROL_SURFACE. Its 12
cognitive files may be read and must be ledgered. Six operational components
are identified by path and digest; allowed hooks, branch guard, and ledger
validator may execute or return finite status codes, but their source and local
authorization receipt may not be opened or interpreted. Operational execution
and status observation are distinct ledger actions. Status-only execution is
not a cognitive read. Source exposure, unlisted cognitive reads, or
case-specific leakage through an operational result is contaminated.

R0.2 branch authorization is task-scoped and clone-local. It binds the Formal
repository, exact base head, task ID and exact branch, push remote and URL,
public noreply identity, and allowed operation class. The guard rejects wrong
repository, branch, base, identity, remote, ref, force update, hook
configuration, and invalid receipt. Its command ref/blob digest is
traceability, not a cryptographic signature; GitHub-side permission and review
remain the remote authority boundary. Global Git configuration is unchanged.

The new cases are:
- coastal-meter-study-r02-01 — source SHA256 db80603f526043fa8b3a82600fb4772e1f24607342a4e64097a18bb2f395c818
- harbor-export-policy-r02-01 — source SHA256 ded7bdbd0aa0e1cf56021785bd5f83dc6833694ffbce90f5390ed23e67731b77

Both are newly authored synthetic sources. The packet contains no answer key,
gold relations, transition answer, human confirmation, expected continuation,
or evaluator criteria. The old cases and first-run outputs are not reused.
Evaluator-sealed material is kept in a sibling directory excluded from the
cognitive manifest.

The final R0.2 packet-manifest SHA256 is recorded in the Draft PR description
together with fixed-point verification. Targeted R0.2 protocol and branch
authorization tests pass 28/28; the Task179/Task181 regression suite, exact-head
CI, and final clean-clone status are reported there from their actual runs.

## Role and epistemic boundary

Task182-R2 Successor: NOT_RUN.
Task183 Evaluator: NOT_RUN.
Owner/GPT adjudication for the retry: NOT_RUN.
General cognitive inheritance: NOT_ESTABLISHED.

The future successor must use a separately issued Task182-R2 command and a
clone-local receipt bound to this repair's exact final head. It must validate
both records before freezing S1, verify commit ancestry and the exact remote
branch before saying whether S1 was pushed, and stop if prohibited content is
exposed. The normal future successor lifecycle is
HELD_OUT_SUCCESSOR_RETRY_COMPLETE; R1 stops here at
READY_FOR_HELD_OUT_SUCCESSOR_RETRY.
