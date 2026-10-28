# IGNITION-20260827-142 Step 02 — Independent Open-Obligation Registry

Status: PASS.

`LIVE_EXTERNAL_INVOCATION` now has an independent machine source at `ignition/data/operations/open-obligation-registry-r1.json`. It records the obligation ID, kind, opening task, current `OPEN` status, owner plane, blocker, next eligible action, carry-forward task, exact terminal condition, and evidence references.

The registry is linked from the formal lifecycle and task-lineage sources, but neither lifecycle source derives task terminality from the registry. Task141 can therefore be terminal with `COMPLETED_WITH_OPEN_OBLIGATIONS` while the registry remains open. The registry validator cross-checks only the live projection’s validated-completion count and next action; it does not reopen a terminal task.

The Current projection will consume these two authorities as separate fields. The ceiling remains repository-local: no validated completion, external truth, production readiness, Owner acceptance, or epistemic acceptance is inferred.
