# ARR R4 — Architecture Decision Records

task_id: `ARR-R4-WAIC-SELF-REFLECTION-R1-RELAY-20260725`
control_commit: `e8530a7d87f13ef09cea58d34f6f548a695d7955`

## ADR-R4-1 — Four-axis model replaces the single `SUCCESS` verdict

**Decision.** Stop treating one undifferentiated `outcome=SUCCESS` as the meaning
of an entire object. Derive four independent axes (pipeline / semantic /
evidence / governance), one status each, from fields already present in the
immutable R3 receipt.

**Rationale.** R3 recorded `SUCCESS=836` for every note, which was routinely read
as "836 notes understood/verified." The four-axis model makes the distinctions
explicit and prevents pipeline success from implying semantic sufficiency.

**Consequences.** `INDEPENDENTLY_SUPPORTED` stays 0 unless sealed evidence truly
contains independent verification. Pipeline completion never implies semantic
sufficiency. The model is reusable on other corpora (no 836 hard-coding).

## ADR-R4-2 — Metric contradictions get exactly one machine-readable disposition

**Decision.** Each of the six mandatory apparent contradictions receives exactly
one disposition from the seven-enum set, with evidence references; none may be
omitted or rhetorically explained.

**Rationale.** R3 shipped several internally inconsistent aggregates (e.g.
`crash_recovery_success_rate` 0.0 in AGGREGATE_METRICS vs 1.0 in
CORPUS_RUN_LEDGER). R4 must surface these as `AGGREGATION_DEFECT`, not bury them.

## ADR-R4-3 — Architecture-candidate gate defaults to NO_EVOLVE

**Decision.** A weakness becomes `ARCHITECTURE_CANDIDATE` only when all eight
gate conditions hold. The gate is a pure, mutation-tested function.

**Rationale.** Prevents promoting material/source/metric/temporal defects to
architecture candidates. R4 produces 0 candidates and does not start R5.

## ADR-R4-4 — Deterministic, generic, private-safe tooling

**Decision.** The audit engine accepts generic evidence directories and synthetic
fixtures; it never hard-codes the 836 note ids, private titles, or R3 result
values as passing conditions. Private detailed ledgers live only on the 1111
evidence branch; the formal repo receives a non-private projection only.

## ADR-R4-5 — Exactly five ordinary commits; no amend/rebase/force

**Decision.** The formal work lands as exactly five ordinary commits per the task
plan. No history rewrite, no sixth commit, no merge/Ready/Main change.
