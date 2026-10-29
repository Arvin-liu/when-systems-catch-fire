# ARR R4 — Gap / Architecture-Candidate Gate

This document specifies the **architecture-candidate gate** used by R4 to decide
whether an observed weakness may be promoted from a lower-level limitation to an
`ARCHITECTURE_CANDIDATE` warranting a future R5 design change. The default
disposition is **`NO_EVOLVE`**. R4 never implements a candidate and never starts R5.

## 1. Purpose

R4 must separate "the material / evidence / extraction / metric is weak" from
"the runtime or architecture is structurally incapable." Only the latter may
become an architecture candidate. Promoting a material or metric defect to an
architecture candidate would misallocate future effort and violate the
non-goals (§15) of R4.

## 2. The eight mandatory conditions

A limitation may be labeled `ARCHITECTURE_CANDIDATE` **only when all** of the
following hold. If any is false, the disposition is `NO_EVOLVE`.

| # | Condition | Meaning |
|---|-----------|---------|
| 1 | `reproducible_from_sealed_evidence` | The weakness is observable from the frozen R3 evidence, not assumed. |
| 2 | `cross_source_or_class_breadth` | Observed across ≥3 independent source clusters **or** ≥2 materially different object classes. |
| 3 | `not_explained_by_lower_level` | Not explained by access, rights, missing source, malformed input, temporal absence, metric definition, test debt or a narrow implementation defect. |
| 4 | `measurable_loss_or_misclassification` | Produces a measurable loss or systematic misclassification. |
| 5 | `primitives_cannot_represent` | Current R1–R3 primitives cannot represent or route it without violating existing contracts. |
| 6 | `lower_cost_adapter_insufficient` | A lower-cost adapter, validator, registry, report or narrow runtime repair is insufficient. |
| 7 | `explicit_non_goals_risk_rollback` | The proposed change has explicit non-goals, risk, rollback and regression boundary. |
| 8 | `independent_audit_agrees` | An independent audit Agent agrees with the classification. |

## 3. Implementation

`arr_r4_self_reflection/arch_gate.py` provides a **pure** function
`decide(conditions: Dict[str, bool]) -> (disposition, failed_conditions)`. The
gate is intentionally side-effect free so it can be **mutation-tested**: removing
or falsifying any single condition must flip a would-be candidate back to
`NO_EVOLVE`. The test suite (`test_r4_architecture_gate.py`) mutates each
condition and asserts the gate rejects.

## 4. R4 outcome

All five attributed limitations (L1–L5) fail the gate:

- L1 (temporal): fails `not_explained_by_lower_level` (explained by absent source dates) and `primitives_cannot_represent` (R1–R3 simply do not need to represent missing dates).
- L2 (source concentration): fails `not_explained_by_lower_level` (material/source property).
- L3 (semantic not attempted): fails `primitives_cannot_represent` (R3 was measurement-only by contract; a semantic adapter is the lower-cost path) and `lower_cost_adapter_insufficient`.
- L4 (metric observability): fails `not_explained_by_lower_level` (metric definition) and `lower_cost_adapter_insufficient` (renaming/redefining a metric is low-cost).
- L5 (consent unverifiable): fails `primitives_cannot_represent` (provenance property).

Result: `ARCHITECTURE_CANDIDATES_TOTAL = 0`, `NO_EVOLVE` for all. The gate logic
itself is verified as correct via mutation tests, so a genuine future candidate
would be caught and promoted by a later authorized iteration.
