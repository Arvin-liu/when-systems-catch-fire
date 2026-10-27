# Task185 Step09 — Reuse / Retirement Candidate Register

## Scope and interpretation

This is a research-only candidate register, not an implementation plan. It classifies all 20 mechanism families in the Step02 atlas, plus three cross-cutting records whose dispositions are explicit in Step04. Each row gives the atlas-declared dependencies, exact source-artifact references, risk, and evidence needed before reconsideration.

`REUSE_AS_IS` is limited to the already documented contract and its existing authority boundary. `REUSE_WITH_ADAPTER` requires a typed, provenance-preserving boundary. `KEEP_SEPARATE` protects distinct grains, consumers, or authorities. `HISTORICAL_ONLY` preserves archived/superseded status. `NEEDS_FURTHER_EVIDENCE` leaves the question open. These labels do not authorize changes.

## Candidate disposition

| Disposition | Candidates | Count |
| --- | --- | ---: |
| `REUSE_AS_IS` | `UNKNOWN_PRESERVATION`, `KNOWLEDGE_RETRIEVAL` | 2 |
| `REUSE_WITH_ADAPTER` | `OBJECT_IDENTIFICATION`, `EVIDENCE_BINDING`, `PROVENANCE`, `COUNTEREXAMPLE`, `DECISION_INTEGRITY`, `OBSERVATION_CALIBRATION`, `CAPABILITY_CALIBRATION`, `COGNITIVE_TRANSITION`, `STRUCTURALIZATION` | 9 |
| `KEEP_SEPARATE` | `CLAIM_BOUNDING`, `ANALOGY_TRANSFER`, `FAILURE_MEMORY`, `SELF_CORRECTION`, `ROUTING`, `INDEPENDENT_EVALUATION`, `GOVERNANCE_AUTHORITY`, `EXECUTION_ORCHESTRATION` | 8 |
| `NEEDS_FURTHER_EVIDENCE` | `METHOD_SELECTION`, `R0_SELF_MODEL_IR_TRANSITION_FIELD_OVERLAP` | 2 |
| `HISTORICAL_ONLY` | `Q37_Q38_ARCHIVED_ANALOGY_RETRIEVAL_PILOT`, `LEGACY_EXHAUSTIVE_ARCHITECTURE` | 2 |
| `MIGRATE` / `CONSOLIDATE_CANDIDATE` / `RETIREMENT_CANDIDATE` | No target currently meets the evidence threshold for even a safe candidate nomination. This is not proof that none could qualify later. | 0 |

Counts cover 23 records: 20 mechanism families plus three explicitly scoped cross-cutting records (the overlap set and the two historical artifact sets). Full per-item rationale, dependencies, risks, and next evidence are in [reuse-retirement-candidates.jsonl](./reuse-retirement-candidates.jsonl).

## Reading the strongest boundaries

- **Reuse without broadening:** the explicit unknown-preservation and derived Knowledge Experience retrieval contracts are reusable only in their documented forms. Exact-source revalidation, anti-backflow, and the existing claim ceiling remain intact.
- **Adapter before interoperability:** identity, evidence, provenance, counterexample, decision, observation, capability, transition, and structuralization surfaces require typed crosswalks or fixtures before they can be treated as one reusable path.
- **Keep unlike state machines apart:** Foundation claim/governance authority, runtime failure memory, self-correction, routing, independent evaluation, and execution orchestration have distinct owners, grains, or roles. Similar words do not establish a common mechanism.
- **Preserve history:** Q37/Q38 pilot artifacts remain historical candidate-generation evidence; the older exhaustive architecture remains superseded/historical. Neither is silently reactivated or deleted.
- **No retirement or consolidation nomination:** Step04 identifies material overlap and field repetition, but its own next evidence is consumer tracing and round-trip/reconstruction checks. Until those exist, proposing a target would outrun the evidence.

## Evidence ceiling

Task185 did not execute a migration, consolidation, retirement, Successor, or Evaluator. No canonical registry, Foundation/Current authority, Task179/181 history, or held-out payload was changed or used as an implementation target. The register is limited to candidate categorization and explicitly named next evidence.
