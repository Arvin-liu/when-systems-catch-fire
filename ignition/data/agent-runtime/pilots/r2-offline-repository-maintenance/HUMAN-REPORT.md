# R2 Offline Repository-Maintenance Pilot

This is a committed observation from one disposable local run. It is not a
production service, a remote-repository operation, or a general intelligence
claim.

## What ran

- A fresh local Git clone was prepared before the Supervisor started. The
  source and clone heads matched.
- The Supervisor drove the dependency DAG `audit → repair → validate` with
  `FAIL_FAST`, a bounded action/time/output budget, and three typed approvals.
- The audit found one declared `MISSING_HASH` finding. The approved repair
  added the README SHA-256 to the local manifest and wrote a repair receipt.
- The repair action was fault-injected after execution and before journal
  persistence. The Supervisor recorded
  `EPISODE_CHECKPOINTED_RESUMABLE`; a new `repair-executor-instance-2`
  resumed the durable postimage and the episode completed as
  `EPISODE_COMPLETED_VALIDATED`.
- A separate `CONTINUE_INDEPENDENT` adversarial episode rejected both a
  network request and a remote Git mutation proposal. The protected file was
  unchanged, and the Gateway rejected permission expansion and forged
  completion claims.

## Durable evidence

`pilot-receipt.json` records one checkpoint, the repair executor handoff,
three completed child Runs, `network_allowed=false`,
`remote_mutation=false`, `git_push_invoked=false`, and sanitized receipt
paths. `durable-memory.jsonl` contains one `FAILURE` entry and one `EPISODIC`
entry; `memory-capsule.json` is bounded operational recall and explicitly not
Knowledge truth, evidence, proof, or permission authority.

## What this cannot establish

The pilot establishes only that this bounded offline fixture produced the
recorded local outcomes under the checked-in runtime contracts. It does not
establish external repository safety, production reliability, human or Owner
acceptance, truth authority, epistemic acceptance, or general intelligence.
