# IGNITION-20260828-144 Step 10 — minimum production state machine

Step 10 reuses the Owner Editorial Authority contract from Step 02. Its
machine-checked path is deliberately small:

`CANDIDATE -> OWNER_SELECTED -> DRAFTING -> OWNER_REVIEW ->
ACCEPTED / REVISE / PARKED / REJECTED`.

Only Owner explicit brief or selection authority can enter the selected or
accepted meanings. A generated draft, ranking, cluster, fire-seed score or
existing Results Book row cannot promote itself. All Task143 smoke outputs
remain candidates with no Owner selection or publication acceptance.
