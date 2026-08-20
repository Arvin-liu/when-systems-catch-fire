# OS Control Plane R2

Task `IGNITION-20260817-124` adds the bounded control-plane fabric that a
driver needs to coordinate multiple declared work units. It is an orchestration
projection over repository-owned records, not a new Agent shell, executor, truth
source, or authority layer.

## Event Ledger R1

The canonical event ledger is append-only, typed, aggregate-versioned and
hash-linked. A writer must pass the aggregate compare-and-swap boundary;
duplicate event identities, broken links, malformed public payloads and a
snapshot that is not a ledger prefix fail closed. Deterministic replay rebuilds
state from a verified snapshot plus the ordered ledger tail.

## Monotonic Policy Compiler R1

Effective policy is compiled by intersection and minimum operations: requested
capabilities, paths, resource intents, permission ceilings, budgets and expiry
can only narrow a parent policy. Stronger prohibitions are retained, and an
approval is valid only when it was predeclared and bound to the task, policy
digest and action. Stale digests and any attempted escalation are rejected.

## Resource Arbitration R1

Typed resource intents use hierarchical overlap, canonical acquire-many order
and expiring leases. Shared reads may coexist; writes, metadata, external and
unknown side effects conflict conservatively. A multi-resource acquisition is
atomic, and unknown side effects never receive automatic failover merely because
no textual path overlap was observed.

## Bounded Concurrent Scheduler R1

The scheduler executes a validated dependency DAG with explicit global and
executor concurrency ceilings. Ready work is ordered deterministically by
priority, aging and stable identity, while resource leases, action/time/output
budgets, cancellation and deadlines are checked before dispatch. Checkpoint and
resume are explicit durable transitions; cancelled, expired, failed and
reconciliatory outcomes remain visible in the terminal rollup.

## Executor Health Lease R1

Routing consumes a digest-bound observation of executor capabilities,
permissions, workspace and concurrency ceilings, support flags and probe class.
Expiry becomes `STALE`; failed probes enter cooldown and repeated failures may
become `UNSAFE_TO_PROBE`. A stale or tampered lease is never a healthy route.
The lease records observed health; it grants no external execution success.

## Queue and Backpressure R1

Admission is durable and bounded by queue depth, project/profile quotas,
`not_before` and deadline. Priority has deterministic FIFO tie-breaking and
aging; pause, backpressure, quota rejection and pre-dispatch cancellation are
distinct states. A post-dispatch cancellation remains a reconciliation
obligation rather than a fabricated completion.

## Durable Dispatch and Reconciliation R1

Dispatch envelopes bind task, executor, effect class, idempotency key and payload
digest. Acknowledgement and public progress are monotonic. An external receipt
is recorded before independent OS validation; only the validation gate may
promote it to `COMPLETED_VALIDATED`. Read-only timeout retry is narrow, while
external or unknown side effects stop at `REQUIRES_RECONCILIATION`.

## Concurrent Operational Memory R2

Operational memory uses generation compare-and-swap, event-reference and
semantic duplicate suppression, atomic supersession/tombstones and
generation-bound capsules. Compaction is a deterministic bounded projection;
stale capsules and integrity tampering fail closed. Memory is operational recall,
not Knowledge truth, proof, permission or Owner authority.

## Driver Console R1

The Driver Console is a human-readable projection of queue, policy, resources,
health, dispatch and memory records. It orders the next action by
reconciliation, stale/unsafe health, resource conflict, queue pause and explicit
checkpoint resume before routine admission. It explains open obligations and
claim ceilings but is not a second truth source.

## Durability and Lifecycle R3

Task 127 adds a single Durability / Lifecycle component inside the existing
Ignition OS control spine. It composes the repository-local snapshot-plus-tail
chain, deterministic compaction, versioned schema migration, namespace and
delegation isolation, Pack pin/activation/rollback, capability revocation,
accounting and fairness, operational memory, recovery orchestration and
disaster-recovery bundle restore. These records preserve lifecycle continuity;
they do not create a second system map, a Knowledge source, a permission layer
or an external executor.

Recovery is fail-closed at the boundary that cannot be verified locally:
tampered, stale, partial, cross-namespace or wrong-epoch state is rejected;
uncertain external dispatch stops at `REQUIRES_RECONCILIATION`, and automatic
external re-execution is forbidden. The Step 16 continuity pilot is a
disposable offline repository fixture with two namespaces and two workspaces;
its snapshot, migration, revocation, accounting, recovery and DR observations
are bounded repository evidence, not production durability, exact-once delivery,
live-provider success, Owner acceptance or epistemic acceptance.

## Boundaries and evidence

The five-child pilot is a disposable offline repository fixture. It demonstrates
bounded coordination, conflict arbitration, stale-executor rejection,
checkpoint/resume, cancellation, deadline handling, forged-receipt rejection,
concurrent memory and console projection. It does not establish live provider
behavior, production safety, general intelligence, external validity, Owner
acceptance or `EPISTEMICALLY_ACCEPTED`; the current state remains
`CURRENT_WITH_OPEN_OBLIGATIONS` with `EPISTEMICALLY_ACCEPTED=0`.
