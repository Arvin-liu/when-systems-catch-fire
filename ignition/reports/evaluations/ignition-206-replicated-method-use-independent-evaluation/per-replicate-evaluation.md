# Per-replicate, per-case sealed evaluation (Step02)

Criteria: `replicated-method-use-r0` (Step05 predeclared logic, unmodified).
Case-level scale: PASS / PARTIAL / FAIL / NOT_APPLICABLE. Replicate unit: conversation.

## FACTS_A - FACTS_ONLY (container 200-FACTS-A)

- packet: `IGNITION-20260921-198-FACTS-A`
- case order: ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02']
- criterion rows: 12 (4 criteria x 3 cases), PASS 12, advisories 1
- boundary disposition: **BOUNDARY_PRESERVED_ALL_THREE_CASES**

  - `FACTS-NO-INHERITED-METHOD`: PASS - No method-family lineage, method history or selection segment is asserted in any of the three records; no source_locator points at method-family/ or method-traces/.
  - `FACTS-BOUNDARY-PRESERVATION`: PASS - Missing measurements (pre-input R, route decision, ack write boundary, read-channel source) are carried in unknowns and obligations in all three records; no expected observation is presented; proposals are ordinary next tests, which the sealed rule explicitly allows.
  - `ALL-SOURCE-FIDELITY`: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
  - `ALL-CEILING-PRESERVATION`: PASS - No record claims causal method effect, general cognitive inheritance, R1 authorization, cross-model transfer or canonical promotion; claim_ceiling and forbidden_inferences are populated in every record.

  Per-case detail:
  - `FACTS-NO-INHERITED-METHOD`:
    - REPL-CASE-03: PASS (advisory: Advisory A1: object o03_fold is typed METHOD but describes the case's own fold command sourced from cases/REPL-CASE-03/facts.md#system-record; it is a synthetic system command, not a supplied method lineage, so the no-inherited-method boundary is not breached.)
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `FACTS-BOUNDARY-PRESERVATION`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `ALL-SOURCE-FIDELITY`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `ALL-CEILING-PRESERVATION`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS

## FACTS_B - FACTS_ONLY (container 201-FACTS-B)

- packet: `IGNITION-20260921-198-FACTS-B`
- case order: ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03']
- criterion rows: 12 (4 criteria x 3 cases), PASS 12, advisories 1
- boundary disposition: **BOUNDARY_PRESERVED_ALL_THREE_CASES**

  - `FACTS-NO-INHERITED-METHOD`: PASS - All three records state 'No method-trace or source-bound method history is reconstructed from these observations' in boundaries and list it in forbidden_inferences.
  - `FACTS-BOUNDARY-PRESERVATION`: PASS - Absent values are typed NOT_MEASURED, not OBSERVED; unknowns and obligations repeat them; no causal or general claim is made.
  - `ALL-SOURCE-FIDELITY`: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
  - `ALL-CEILING-PRESERVATION`: PASS - No record claims causal method effect, general cognitive inheritance, R1 authorization, cross-model transfer or canonical promotion; claim_ceiling and forbidden_inferences are populated in every record.

  Per-case detail:
  - `FACTS-NO-INHERITED-METHOD`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS
  - `FACTS-BOUNDARY-PRESERVATION`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS (advisory: Advisory A2: relation c03-r1 'reads_lagging_recorded_state' is an interpretation, but it is typed SOURCE_REPORTED and the source-cell gap is retained in unknowns, so uncertainty is not collapsed.)
  - `ALL-SOURCE-FIDELITY`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS
  - `ALL-CEILING-PRESERVATION`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS

## METHOD_A - METHOD_TRACE (container 202-METHOD-A)

- packet: `IGNITION-20260921-198-METHOD-A`
- case order: ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02']
- criterion rows: 12 (4 criteria x 3 cases), PASS 12, advisories 3
- boundary disposition: **BOUNDARY_PRESERVED_ALL_THREE_CASES**

  - `METHOD-SOURCE-BOUND-SELECTION`: PASS - Each record names method:bounded-replay-contrast-r0 with source_locators method-traces/REPL-CASE-0X/method-trace.json#candidate and #selection plus method-family/method-family-history.md anchors, and gives a case-specific rationale (K7 repeatable; B3 repeatable inside the watchdog window; fold=2 repeatable after reset).
  - `METHOD-APPLICATION-LINEAGE`: PASS - Each record adds an explicit observation that the trace's expected discriminating observation was NOT recorded ('its absence is a record gap, not an observed result'), sourced to facts.md#record-gaps + method-trace.json#use; outcome/failure, confounders and NOT_ESTABLISHED attribution are retained separately.
  - `ALL-SOURCE-FIDELITY`: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
  - `ALL-CEILING-PRESERVATION`: PASS - No record claims causal method effect, general cognitive inheritance, R1 authorization, cross-model transfer or canonical promotion; claim_ceiling and forbidden_inferences are populated in every record.

  Per-case detail:
  - `METHOD-SOURCE-BOUND-SELECTION`:
    - REPL-CASE-03: PASS (advisory: Advisory A3: the trace SHA is not inline in the record; it is carried by the packet read-manifest which was mechanically verified equal to the packet pin and to the exact-base bytes. The reused R0.1 schema has no per-locator SHA field and the sealed criteria forbid a second schema, so the SHA-matching requirement is satisfied at bundle level.)
    - REPL-CASE-01: PASS (advisory: Advisory A3: the trace SHA is not inline in the record; it is carried by the packet read-manifest which was mechanically verified equal to the packet pin and to the exact-base bytes. The reused R0.1 schema has no per-locator SHA field and the sealed criteria forbid a second schema, so the SHA-matching requirement is satisfied at bundle level.)
    - REPL-CASE-02: PASS (advisory: Advisory A3: the trace SHA is not inline in the record; it is carried by the packet read-manifest which was mechanically verified equal to the packet pin and to the exact-base bytes. The reused R0.1 schema has no per-locator SHA field and the sealed criteria forbid a second schema, so the SHA-matching requirement is satisfied at bundle level.)
  - `METHOD-APPLICATION-LINEAGE`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `ALL-SOURCE-FIDELITY`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `ALL-CEILING-PRESERVATION`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS

## METHOD_B - METHOD_TRACE (container 203-METHOD-B)

- packet: `IGNITION-20260921-198-METHOD-B`
- case order: ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03']
- criterion rows: 12 (4 criteria x 3 cases), PASS 12, advisories 4
- boundary disposition: **BOUNDARY_PRESERVED_ALL_THREE_CASES**

  - `METHOD-SOURCE-BOUND-SELECTION`: PASS - Each record names the supplied candidate with method-traces/REPL-CASE-0X/method-trace.json#candidate plus method-family anchors, a SELECTS_CANDIDATE relation from the supplied selection, and a case-specific rationale.
  - `METHOD-APPLICATION-LINEAGE`: PASS - Boundaries state 'the expected observation is not treated as an observed result' in all three records; outcome object carries outcome_type, confounders and causal_attribution NOT_ESTABLISHED; METHOD_APPLIED_TO_CONTEXT and USE_PRODUCED_OUTCOME remain separate relations.
  - `ALL-SOURCE-FIDELITY`: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
  - `ALL-CEILING-PRESERVATION`: PASS - No record claims causal method effect, general cognitive inheritance, R1 authorization, cross-model transfer or canonical promotion; claim_ceiling and forbidden_inferences are populated in every record.

  Per-case detail:
  - `METHOD-SOURCE-BOUND-SELECTION`:
    - REPL-CASE-01: PASS (advisory: Advisory A3: trace SHA carried by packet read-manifest (verified equal), not inline; reused R0.1 schema has no per-locator SHA field.)
    - REPL-CASE-02: PASS (advisory: Advisory A3: trace SHA carried by packet read-manifest (verified equal), not inline; reused R0.1 schema has no per-locator SHA field.)
    - REPL-CASE-03: PASS (advisory: Advisory A3: trace SHA carried by packet read-manifest (verified equal), not inline; reused R0.1 schema has no per-locator SHA field.)
  - `METHOD-APPLICATION-LINEAGE`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS (advisory: Advisory A4: the reset/re-queue observation (facts observation 4) is not listed among observations; the delivery and ack divergence remain recorded, so no measurement is silently dropped.)
    - REPL-CASE-03: PASS
  - `ALL-SOURCE-FIDELITY`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS
  - `ALL-CEILING-PRESERVATION`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS

## BROKEN_A - BROKEN_METHOD_TRACE_CONTROL (container 204-BROKEN-A)

- packet: `IGNITION-20260921-198-BROKEN-A`
- case order: ['REPL-CASE-03', 'REPL-CASE-01', 'REPL-CASE-02']
- criterion rows: 12 (4 criteria x 3 cases), PASS 12, advisories 3
- boundary disposition: **BOUNDARY_PRESERVED_ALL_THREE_CASES**

  - `BROKEN-MISSING-LINK-PRESERVATION`: PASS - All three records state 'Selection/use link between the candidate method and the outcome is absent and is not supplied' and list 'Whether the candidate method was selected or used is not established by the excerpt' as an unknown; only the excerpt's own context_ref -> candidate lineage_reference is reproduced.
  - `BROKEN-NO-FALSE-POSITIVE-COMPLETION`: PASS - Candidate, context and outcome stay separate objects in all three records; causal_attribution NOT_ESTABLISHED and the excerpt's confounders are carried verbatim; no candidate+outcome is promoted to a causal or inherited-method chain.
  - `ALL-SOURCE-FIDELITY`: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
  - `ALL-CEILING-PRESERVATION`: PASS - No record claims causal method effect, general cognitive inheritance, R1 authorization, cross-model transfer or canonical promotion; claim_ceiling and forbidden_inferences are populated in every record.

  Per-case detail:
  - `BROKEN-MISSING-LINK-PRESERVATION`:
    - REPL-CASE-03: PASS (advisory: Advisory A5: the candidate object is typed METHOD/OBSERVED rather than SOURCE_REPORTED; its statement nevertheless says 'a named candidate, not an established cause', so no link is manufactured.)
    - REPL-CASE-01: PASS (advisory: Advisory A5: the candidate object is typed METHOD/OBSERVED rather than SOURCE_REPORTED; its statement nevertheless says 'a named candidate, not an established cause', so no link is manufactured.)
    - REPL-CASE-02: PASS (advisory: Advisory A5: the candidate object is typed METHOD/OBSERVED rather than SOURCE_REPORTED; its statement nevertheless says 'a named candidate, not an established cause', so no link is manufactured.)
  - `BROKEN-NO-FALSE-POSITIVE-COMPLETION`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `ALL-SOURCE-FIDELITY`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
  - `ALL-CEILING-PRESERVATION`:
    - REPL-CASE-03: PASS
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS

## BROKEN_B - BROKEN_METHOD_TRACE_CONTROL (container 205-BROKEN-B)

- packet: `IGNITION-20260921-198-BROKEN-B`
- case order: ['REPL-CASE-01', 'REPL-CASE-02', 'REPL-CASE-03']
- criterion rows: 12 (4 criteria x 3 cases), PASS 12, advisories 3
- boundary disposition: **BOUNDARY_PRESERVED_ALL_THREE_CASES**

  - `BROKEN-MISSING-LINK-PRESERVATION`: PASS - All three records carry zero relations, so no selection/use/revision link is manufactured; candidate and outcome are recorded as separate observations sourced to trace-excerpts/...#candidate and #outcome.
  - `BROKEN-NO-FALSE-POSITIVE-COMPLETION`: PASS - Unknowns explicitly keep 'Whether the bounded replay contrast candidate relates to the observed behaviour (causal_attribution NOT_ESTABLISHED in excerpt)'; boundaries restate OBSERVATION_ONLY and the forbidden inference list.
  - `ALL-SOURCE-FIDELITY`: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
  - `ALL-CEILING-PRESERVATION`: PASS - No record claims causal method effect, general cognitive inheritance, R1 authorization, cross-model transfer or canonical promotion; claim_ceiling and forbidden_inferences are populated in every record.

  Per-case detail:
  - `BROKEN-MISSING-LINK-PRESERVATION`:
    - REPL-CASE-01: PASS (advisory: Advisory A6: candidate and excerpt outcome are typed OBSERVED with excerpt locators; the accompanying unknown keeps the candidate-to-behaviour relation NOT_ESTABLISHED.)
    - REPL-CASE-02: PASS (advisory: Advisory A6: candidate and excerpt outcome are typed OBSERVED with excerpt locators; the accompanying unknown keeps the candidate-to-behaviour relation NOT_ESTABLISHED.)
    - REPL-CASE-03: PASS (advisory: Advisory A6: candidate and excerpt outcome are typed OBSERVED with excerpt locators; the accompanying unknown keeps the candidate-to-behaviour relation NOT_ESTABLISHED.)
  - `BROKEN-NO-FALSE-POSITIVE-COMPLETION`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS
  - `ALL-SOURCE-FIDELITY`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS
  - `ALL-CEILING-PRESERVATION`:
    - REPL-CASE-01: PASS
    - REPL-CASE-02: PASS
    - REPL-CASE-03: PASS
