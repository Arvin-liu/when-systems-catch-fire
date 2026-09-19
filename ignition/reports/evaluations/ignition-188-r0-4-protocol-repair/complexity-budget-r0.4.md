# R0.4 Complexity / Retirement Budget

This is a Builder-side maintenance budget for the evaluation protocol. It
does not run a Successor or Evaluator, does not promote a claim, and does not
retire forensic history.

## Version disposition

| Version | Disposition | Scope |
|---|---|---|
| R0.1 | Historical foundation contract; reused typed boundary | Evaluation-plane classification, provenance-only retention, and explicit non-promotion policy |
| R0.2 | Historical-only trial packet and validator | Earlier held-out packet, branch guard, read-ledger validator, and schemas |
| R0.3 | Historical-only repair packet and finalizer | Previous case packet and final-attestation semantics, retained byte-stable for forensic comparison |
| R0.4 | Current active protocol | Case-exposure semantics repair and the next successor-visible held-out packet |

The R0.1 evaluation-plane contract remains the shared boundary. “Historical-
only” applies to the versioned trial artifacts, not to the typed
`EVALUATION_EVIDENCE` isolation mechanism they reuse.

## Current active surface

R0.4 owns the active ledger protocol, finalizer, successor-visible packet,
case manifest, output/read-ledger/receipt schemas, two fresh cases, regression
fixtures, and the local-only bootstrap interface. R0.4 deliberately reuses
the R0.3 task-scoped branch guard and its R0.3 hook adapters; it creates no
new R0.4 guard or parallel operational-control framework.

The measured surface at this step is 29 Task188 evaluation artifacts, with
the versioned protocol files retained alongside the shared R0.1 boundary.

## Duplication inventory

- `task_branch_guard_r0_2.py` and `task_branch_guard_r0_3.py` are both 327
  lines and differ in the version label, authorization schema path, and hook
  directory. This is the clearest avoidable executable duplication.
- `finalize_successor_read_ledger_r0_3.py` and the R0.4 finalizer are 498 and
  500 lines. Their common frozen-ledger, receipt, and fail-closed machinery is
  a future shared-core candidate; the R0.4 semantic change remains explicit
  and versioned for this trial.
- The read-ledger schemas are 50 lines (R0.2) and 144 lines (R0.3/R0.4); the
  packet-manifest schemas are 77 lines (R0.2) and 84 lines (R0.3/R0.4); the
  case-manifest schemas are 45 lines in both R0.3 and R0.4; and the final
  receipt schemas are 63 lines in both R0.3 and R0.4. These are related
  versioned wire contracts, not evidence that an old contract may be erased.
- Successor-output schemas, bootstrap documents, packet READMEs, and method
  contracts repeat version-specific fields and boundary language. R0.4 adds
  only the packet needed for the fresh held-out cases and the repaired
  channel semantics.

## Future consolidation candidates

`EVALUATION_PROTOCOL_VERSION_CONSOLIDATION_CANDIDATE`

After the R0.4 held-out trial and its independent evaluation are complete,
consider the following in a separate Owner-authorized maintenance task:

1. Extract a version-neutral authorization core for repository, identity,
   branch, worktree, remote, and finite-status checks, with thin R0.2/R0.3/R0.4
   adapters. Keep each historical authorization schema and receipt immutable.
2. Extract shared ledger row definitions and receipt-binding helpers into a
   common schema/tool library, with version overlays for semantic differences
   such as authorized cognitive case exposure. Keep old finalizers runnable
   for historical reproduction.
3. Consolidate packet/case manifest `$defs` and common output fields while
   retaining versioned manifests and exact historical hashes at the packet
   boundary.

No consolidation is performed in this Step07 repair. A refactor before the
R0.4 trial would mix protocol repair with control-surface migration.

## Retirement candidates after stability

- R0.2 validator, guard, and hooks may be removed from active entrypoints
  after no R0.2 trial remains, but their files and receipts stay archived as
  historical evidence.
- R0.3 finalizer may become historical-only after the R0.4 successor trial
  has a separately reviewed receipt. R0.3 guard and hooks cannot be retired
  while the R0.4 bootstrap still intentionally reuses them.
- R0.1 evaluation-plane helper entrypoints may be made non-default after the
  current typed isolation tests fully cover their contract; the R0.1 policy
  and schemas remain the boundary reference.

`RETIREMENT_NOW=NONE`

All candidates are deferred. There is no deletion, rewrite, rebase, amend,
squash, or protocol-history compaction in this step.
