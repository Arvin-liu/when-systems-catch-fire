# Next Iteration Recommendation — Task 109

## Recommended next substantive iteration

- **canonical_id**: `C-01`
- **class**: CORE_CAPABILITY_VALIDATION
- **aggregate_score**: 73.2
- **source**: `data/external-research/104-source-registry.jsonl`
- **claim_id**: `SRC-REGISTRY-104-METADATA`
- **claim_ceiling**: Registry external-source metadata integrity only; not a claim about Pointfire physics correctness.

### Why this one

C-01 is a bounded, falsifiable evidence-program reserve pilot: it asserts that 117
source records marked `crossref_verified:true` resolve via the Crossref REST API to
DOIs whose title/year match the registry, and are not retracted or duplicate. It has
a direct oracle (the Crossref API), high falsifiability (0.95), full data availability
(1.0) and low evidence cost. It produces real evidence (pass/fail) without creating a
new governance layer.

### This is NOT task 110

Per contract §2/§10, the recommendation is a reviewed proposal only. It is **not**
automatically created or executed as task 110.

## Reserves

1. `CF-apple_gravity_failure` — IMPLEMENTATION_DEFECT
2. `CF-cross_domain_synergy_risk` — IMPLEMENTATION_DEFECT

## Dependency & evidence readiness

- C-01 dependencies: ['SRC-REGISTRY-104-METADATA']
- evidence needs: ['preregistration', 'independent replication', 'oracle/baseline']
- stop conditions / claim ceiling enforced: n/a

## Why plausible alternatives were not selected

See `decision_log.json` (>=5 explicit reasons: meta-governance gaps, grand untestable
physics, quarantine adjudication, lower-ranked pilots, upstream-dependent architectural gaps).
