# Iteration Boundary Archaeology R1

## Scope

This is the Step 00 audit for `IGNITION-20260822-133`. The formal baseline was
`main@5ed99d148dfb49e6c2ff729a345d2499d4b76021`. The audit is intentionally
historical and read-only: no current value was changed to justify a conclusion.

## What the history shows

`current_iteration_boundary` first appeared in Task123's `CURRENT_STATE_SYNC_INVARIANT`
contract at `122`. That first value preserved the prior current architecture
boundary while Task123 established synchronization machinery. It then appeared as
`124`, `126`, `127`, `128`, and `129` in later Current identity projections. Most
of those values coincided with architecture-changing work, but the repository
never added a derivation rule saying that the field was an architecture ordinal.

Task130 is the decisive counterexample. Step 09 changed the identity and
current-facts values from `129` to `130` while classifying the work as
`PRESENTATION_ONLY` and creating the lifecycle record with the same copied
integer. No task-id parser, source pointer, or validator relation explained that
advance. Task131 changed publication semantics and Task132 advanced the canonical
formal task and release bindings, but both left the opaque integer at `130`.

Therefore the fresh-main state is not a case of one missed numeric replacement.
It is a missing semantic contract: the formal task can advance independently of
architecture identity, and the existing field has no machine-verifiable meaning.

## Consumer audit

| Consumer | Current behavior | Semantic gap |
| --- | --- | --- |
| `current-system-identity.json` | Stores an opaque non-negative integer | No source or relation to a task identity |
| `current-release-lifecycle-r1.json` | Copies the identity value | Equality only; no ordinal derivation |
| `generate_current_facts.py` | Copies the contract value into JSON and Markdown | Deterministic propagation of an undefined value |
| volatile fact registry | Names the identity field as the source | Does not distinguish formal vs architecture ordinal |
| state-sync/lifecycle validators | Check type/equality | Cannot reject `Task132 + boundary=130` |
| snapshot/compiler | Advertises a possible rendering, but materialized Task132 snapshot does not render it | Dead/misleading metadata rather than a semantic consumer |
| historical receipts | Preserve captured values such as Task123=`122` | Must remain historical and must not be rewritten |

## Step 00 conclusion

At the baseline, `130` is **semantically undefined and currently stale**:

- canonical current formal task: `IGNITION-20260822-132`;
- current formal ordinal: `132`;
- latest architecture-changing task: `IGNITION-20260821-129`;
- latest architecture ordinal: `129`;
- opaque boundary: `130`.

The compatible resolution to carry into Step 01 is to introduce named canonical
formal and architecture ordinals, derived from canonical task IDs, and retain
`current_iteration_boundary` only as a deprecated deterministic compatibility
alias of `current_formal_task_ordinal` in Current projections. Historical
receipts retain their captured values with historical labels. This makes a normal
state such as “latest formal Task133; latest architecture Task129” valid without
forcing the two concepts together.

Claim ceiling: this document records repository-local history and consumer
behavior only. It does not establish external truth, production readiness, Owner
acceptance or epistemic acceptance.
