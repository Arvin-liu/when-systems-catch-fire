# R0.4 operational-control boundary

R0.4 reuses the existing task-scoped branch authorization and status-only guard mechanism from `ignition/evaluation/operational-control/r0.3/` and `ignition/evaluation/tools/task_branch_guard_r0_3.py`. This is a deliberate reuse of the established control surface, not a parallel admission framework.

The successor may execute `bootstrap-r0.4.sh` and record only its finite status. It must not read the guard source, authorization receipt, hooks, or other operational-control content. The R0.4 finalizer is a final-attestation component outside the certified ledger scope and must write its receipt outside the successor-visible packet.
