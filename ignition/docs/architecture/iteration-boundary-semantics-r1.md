# Iteration Identity Model R1

`ITERATION_BOUNDARY_SEMANTICS_INVARIANT` gives every Current iteration field one
machine-checkable meaning. The canonical task identity source is
`ignition/data/operations/current-task-lineage-status.json`; ordinals are parsed
from its task IDs by the deterministic parser introduced in Step 02.

| Field | Meaning | Source / derivation | Authority and lifecycle |
| --- | --- | --- | --- |
| `current_formal_task_id` | Most recent formal task in canonical Current state | `/task_identity/current_formal_task` | Canonical task identity; advances only through task advancement |
| `current_formal_task_ordinal` | Integer ordinal of the current formal task | Parse `current_formal_task_id` | Derived on every validation; never hand-authored |
| `latest_architecture_changing_task_id` | Most recent task that changed architecture identity | `/task_identity/latest_architecture_changing_task` | Independent canonical architecture role |
| `latest_architecture_task_ordinal` | Integer ordinal of the architecture task | Parse `latest_architecture_changing_task_id` | Derived on every validation; may differ from formal ordinal |
| `current_method_version` | Current method version | `ignition/ITERATION.md` marker | Independent method declaration |
| `current_iteration_boundary` | Backward-compatible alias of the current formal ordinal | Exact alias of `current_formal_task_ordinal` | Deprecated; new consumers must use named fields |

The old field is therefore not an architecture boundary and not a free-standing
iteration counter. In a valid Current state, `current_iteration_boundary` equals
`current_formal_task_ordinal`. Historical receipts keep their captured values and
are interpreted only under their historical labels; they are not rewritten to
fit the Current alias.

The formal and architecture roles are deliberately independent. “Latest formal
Task133; latest architecture Task129” is valid. A validator must reject stale or
manually widened ordinals, but must not reject a difference between the two
roles merely because they differ.

The machine-readable contract is
[`iteration-boundary-semantics-r1.json`](../../data/operations/iteration-boundary-semantics-r1.json),
validated by
[`validate_iteration_boundary_semantics.py`](../../tools/validate_iteration_boundary_semantics.py).

Claim ceiling: this is repository-local identity and compatibility governance
only. It does not establish external truth, production readiness, Owner
acceptance or epistemic acceptance.
