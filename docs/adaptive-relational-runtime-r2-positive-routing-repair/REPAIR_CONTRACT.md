# Repair Contract — R2 Positive Routing Repair R1

## Authorization
External review verdict `POSITIVE_ROUTING_REPAIR_R1=AUTHORIZED` (predecessor
`R2_POSITIVE_REAL_OBJECT_PROCESSING=REJECT`, `R2_FAIL_CLOSED_BOUNDARY_PILOT=ACCEPT`,
`R3_SCALE_RUN_AUTHORIZED=NO`). This repair fixes ONLY the five defects found in the
frozen R2 head `bfe90c65`; it does not erase or rewrite the original R2 result.

## Scope (narrow, stacked)
- 4.1 adapter dispatch protocol (type-correct, fail-closed)
- 4.2 schema-valid Source / Observation construction
- 4.3 locked-manifest immutability in memory
- 4.4 real projection routing (no `None` default)
- 4.5 receipt / outcome semantics
- 4.6 aggregation semantics (coverage / residue / false-consensus / signals)

## Hard constraints
- Author identity: `49422864+Arvin-liu@users.noreply.github.com` (from first commit).
- Exactly **four ordinary commits** on the new child branch
  `repair/adaptive-relational-runtime-r2-positive-routing-r1`.
- No force push, amend, rebase, squash, reset replacement, filter-branch/filter-repo,
  history rewrite, Ready, merge, or Main modification.
- Do not modify predecessor PR #109–#121 metadata / head / base / state / tags.
- Rerun the EXACT same 48-object selection (manifest digest `d132c825…`); do not
  swap objects to make the repair pass.
- Replay is deterministic and idempotent (>=3 runs); genuine routing/representation
  limits are reported, not converted into fake success.

## Branches / PR / tag / evidence topology
- Child branch: `repair/adaptive-relational-runtime-r2-positive-routing-r1`
- Draft PR: head = child branch, base = `runtime/adaptive-relational-runtime-r2-real-object-pilot`
- Annotated frozen tag (after final verification):
  `archive/adaptive-relational-runtime-r2-positive-routing-repair-r1-frozen-head`
- 1111 evidence branch: `agent/adaptive-relational-runtime-r2-positive-routing-repair-r1-20260725`
- Evidence: `evidence/adaptive-relational-runtime-r2-positive-routing-repair-r1/`

## Verdict target
`ARR_R2_POSITIVE_ROUTING_REPAIR_DRAFT_AWAITING_EXTERNAL_REVIEW`
(R3 remains unauthorized until independent external acceptance.)
