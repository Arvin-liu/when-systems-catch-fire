# Attack Matrix — R2 Positive Routing Repair R1 (>=64 checks)

Repair-specific acceptance checks (see `tests/adaptive_relational_runtime/
test_r2_positive_routing_repair.py`). Grouped by defect:

### 4.1 Adapter dispatch protocol
- each adapter receives only its declared context (parametrized x6)
- unknown context key fails closed (parametrized x6)
- undeclared Function OS capability fails closed
- mechanism adapter receives declared capabilities and succeeds
- non-mechanism adapters do NOT forward declared_capabilities
- unknown object class fails closed
- protocol mutation changes behavior (proven)

### 4.2 Schema-valid Source / Observation
- Source validates for all 48
- Observation validates for all 48
- Source record_id matches pattern
- Observation record_id matches pattern
- rights boundary + 64-hex digest present
- typed locator present
- no full private content in Source

### 4.3 Manifest immutability
- manifest bytes unchanged before/after run
- nested adapter_ref unchanged
- same manifest instance runs three times (identical ids/run_id)
- no adapter inserts defaults into caller object

### 4.4 Real projection
- projection invoked; actual route recorded (never defaulted)
- expected vs actual route compared
- actual route matches a fresh real projection
- generic relation not upgraded to cause
- causal wording delegates to MCF
- probability without PSD boundary rejected
- valid PSD boundary routes correctly
- time-impossible path rejected

### 4.5 Receipt + outcome semantics
- every receipt has explicit outcome fields
- expected rejection counted as EXPECTED_REJECT (not infra failure)
- unexpected rejection is FAILURE (not silently relabeled)

### 4.6 Aggregation semantics
- coverage measures success not mere receipt
- coverage false when a class only has extraction failures
- routing residue counts quarantined / missing projection / mismatch
- representation residue distinguishes ref-only from failure
- same-source digest cluster flagged (false consensus)
- false consensus without manifest not fabricated
- engineering signal complete only when coverage complete

### Boundaries / counters
- no private content published
- no real-world action
- no PROMOTE/EVOLVE path in source (static gate clean)
- counter invariants: receipts/adapter/runtime/projection/immutable/replay/
  match = 48, unexpected extraction/runtime = 0, promote/evolve = 0,
  private publication = 0
- predecessor/digest/propagation invariants (local git + digest retained)

Total repair-specific checks: 71 (>= 64 required). All pass on the repair head
and fail to collect on the frozen R2 predecessor (no `adapter_protocol`).
