# Federation Router R1

`FederationRouter` is a vendor-neutral selection boundary.  It evaluates
observable `ExecutorDescriptor` records against a data policy and an OS
`RoutingRequest` in this order:

1. explicit Owner/Profile pin priority;
2. declared capability and policy permission ceiling;
3. approval/effect compatibility;
4. availability and health;
5. task granularity;
6. privacy class and workspace locality;
7. configured task-type preference;
8. least-privilege surplus;
9. stable executor/instance ID tie-break.

The routing policy is
`data/agent-federation/federation-routing-policy-r1.json`; executor IDs,
task-type preferences, privacy/locality classes, permission ceilings and
sandbox semantics are data.  The router never uses a brand conditional, star
count, marketing claim or inferred model quality.  An unavailable executor
can fall back only to another already-compatible candidate; the router never
expands capabilities to make a route fit.

Every result is an auditable `RoutingDecision` containing all candidates,
typed rejection reasons, effective permission, selected executor, and fallback
order.  `Supervisor` can consume this plan without importing a vendor adapter;
execution, validation and canonical state remain separate OS contracts.
