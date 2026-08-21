# IGNITION-20260821-129 Step 00 — Steering gap audit

## Baseline

- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Task branch: `codex/ignition-129-os-steering-intent-obligation-r1-20260821`
- Execution-time `origin/main`: `354be6c079945eb8349e0fee1de79395eb5f8d1c`
- Relay control tip: `Arvin-liu/1111:origin/relay/current`
  `0064897c5537cc4a20eb7b03824841a9d6a608d6`
- Working tree: clean at audit start

## Answers to the required audit questions

1. Existing `goal` fields are run-local contracts. R1 run spec/state and the
   Federation envelope carry bounded execution goals, while Supervisor carries
   an episode and child-run DAG. None is a persistent Owner intent or Goal
   lifecycle. Scheduler and resource arbitration have integer priorities, but
   they are local dispatch hints rather than a sourced long-term policy.
2. The Supervisor DAG answers which child run may proceed after another child;
   it does not answer why a long-term goal exists, whether the goal is
   satisfied, or whether a new episode should supersede an old one.
3. Current scheduler/resource priorities have no Owner rank, source,
   authority, or provenance. They must be consumed as bounded inputs to a new
   explainable policy, not silently upgraded.
4. Driver Console can show a control-plane `next_action` for queue, health,
   resource, dispatch, checkpoint, or budget state. It cannot name the active
   goal, compare skipped goals, expose the reason chain, or distinguish run
   completion from goal completion.
5. Operational Memory is durable operational context. Profile and ESI can
   constrain or contextualize execution, but neither currently has an explicit
   guard that repeated preference or advisory signal cannot become Owner
   intent, commitment, or priority authority. This is a required negative-test
   surface for R1.
6. Reusable structures are Supervisor Episode/Run, scheduler and resource
   arbitration, NamespaceGuard, Durability snapshot-plus-tail/migration,
   Federation contracts, Driver Console, and the existing Current-State sync
   contract. A separate parallel scheduler, Knowledge registry, or executor
   authority would duplicate existing boundaries and is not justified.
7. Task 128 lineage closure is consistent at the execution baseline:
   `CURRENT_TASK_LINEAGE_STATUS` identifies Task 128 as terminal with
   classified residuals, preserves `HISTORICAL_UNEXECUTED`/`REBASED_INTO_127`,
   and the Current-State contract remains `CURRENT_WITH_OPEN_OBLIGATIONS` with
   `EPISTEMICALLY_ACCEPTED=0`.

## Reuse and non-escalation decision

The new work will add an OS-owned steering contract under the existing Agent
Runtime/Control Plane boundary. It will reference existing Episode, Run,
Action, Namespace, Durability, Federation, Profile, Memory and Driver Console
records without treating any of them as an Owner-intent source. Synthetic
fixtures will be used for Owner-declared examples; no private chat, profile
body, or external executor content will be copied into the repository.

## Baseline gate

The scoped baseline command passed 50 tests covering Current-State sync,
current task lineage, scheduler, Supervisor, Driver Console, snapshot,
Namespace, and Federation core/router contracts. Full regression remains a
later task step and existing historical/environment residuals remain classified
rather than rewritten.

Claim ceiling: this file is an execution-time repository audit. It does not
prove that the OS knows a real Owner's goals, that deterministic priority is
better than human judgment, or that any runtime is production-safe.
