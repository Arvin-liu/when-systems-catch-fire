# Night Train Depth Audit Report — Second Pass

## Summary

| Stage | Files | Lines | Validator Lines | Test Lines | Tests | Verdict |
|-------|-------|-------|-----------------|------------|-------|---------|
| Q33   | 12    | 786   | 260             | 195        | 17    | PARTIALLY_OPERATIONAL |
| Q34   | 10    | 403   | 66              | 89         | 11    | DEMO_ONLY_NOT_GENERALIZED |
| Q35   | 10    | 388   | 93              | 74         | 11    | PARTIALLY_OPERATIONAL |
| Q36   | 9     | 198   | 69              | 45         | 6     | DEMO_ONLY_NOT_GENERALIZED |
| Q37   | 7     | 189   | 62              | 42         | 7     | SCHEMA_ONLY_NOT_OPERATIONAL |
| Q38   | 8     | 203   | 57              | 45         | 7     | SCHEMA_ONLY_NOT_OPERATIONAL |
| Q39   | 8     | 349   | 61              | 56         | 9     | DEMO_ONLY_NOT_GENERALIZED |

**Total**: 64 files, 2516 lines, 68 tests across 7 stages.

---

## Q33: Rights Governance

### 1. Quantitative
- 6 registries (jurisdiction, source-rights, derivation-ledger, publication-decision, historical-exposure, contributor-rights-attestation)
- 2 schemas (rights-registry, publication-gate)
- 1 validator (260 lines)
- 17 tests (7 normal + 10 attack)

### 2. Runtime Integration
Validator is a standalone tool that reads JSON files. No runtime pipeline calls it. No propagation closure integration.
**Verdict: SCHEMA_ONLY for runtime integration**

### 3. Semantic Validation
Validator does real semantic checks:
- Registry type enum validation
- Status enum validation (6 valid values)
- Source type enum validation (10 valid values)
- Risk level enum validation
- Claim ceiling enum validation (4 valid values)
- Cross-field: `content_in_repo=true` blocked for external source types
- Cross-field: `publication_allowed=false` + `content_in_repo=true` contradiction
- Derivation chain structure (source_id + relation required)

**Verdict: SEMANTIC — real field-level validation, but no cross-registry integrity**

### 4. Dead Code
No dead code found. All functions are called.

### 5. Pseudo-Validation
No empty functions or `return True`.

### 6. Test Coverage
- Normal: happy path with real registries
- Attack: 10 mutations using real validator functions with crafted inputs
- Attack tests are genuine — they create malicious docs and call real validators

### 7. Duplicate Test Logic
- `test_n7_q29r_hash_unchanged` also appears in Q34, Q35, Q36, Q37, Q38 (6 copies total, not shared)
- `test_a10_main_not_modified` also appears in Q34-Q38 (6 copies)
- These inflate test count by ~2 per stage = ~12 duplicate tests total

### 8. TODO / Placeholder
None found in validator or tests.

### 9. Registry Authority
Each registry type has one file. No duplicates.

### 10. Generated Output Authority
N/A — no generated outputs in Q33.

### 11. Propagation Closure Integration
**NOT INTEGRATED** — rights registries are not part of the Q32 propagation closure system.

### 12. System Map Integration
**NOT INTEGRATED** — no system map candidate entries.

### 13. Q32 Test Compatibility
Not tested in first pass.

### 14. Overclaiming
No overclaiming detected.

### 15. Assessment
**PARTIALLY_OPERATIONAL** — Real validator with real semantic checks. Missing:
- Cross-registry reference integrity (derivation-ledger references source-rights IDs that may not exist)
- Jurisdiction coverage check (what if a source has no matching jurisdiction?)
- Historical exposure is empty registry with no validation of why
- No integration with propagation closure or system map

---

## Q34: Discovery-Commitment

### 1. Quantitative
- 5 registries (discovery, commitment-candidates, promotion-decisions, demotion-decisions, residue-records)
- 1 schema (dual-plane)
- 1 validator (66 lines)
- 11 tests (5 normal + 6 attack)

### 2. Runtime Integration
No runtime. Validator reads static JSON.

### 3. Semantic Validation
Validator checks:
- Plane enum (exploration/commitment)
- Status enum (8 values)
- Gate completeness for committed items
- Discovery registry cannot have commitment plane entries
- Residue must have blocked reasons
- Epistemic level gate: low levels (analogy/inspiration/conjecture/model_sketch) blocked from commitment

**Verdict: SEMANTIC — good gate logic, but limited to single-entry checks**

### 4. Dead Code
None found.

### 5. Pseudo-Validation — CRITICAL FINDINGS
**Attack tests are fake:**
- `test_a1_conjecture_in_commitment_blocked`: Creates a malicious entry but NEVER calls the validator with it. Just checks that "conjecture" is in VALID_EPISTEMIC set. This test would pass even if the validator had no such check.
- `test_a2_missing_gate_blocks_promotion`: Creates a dict and asserts `gates["epistemic_gate"] != "pass"`. This tests Python dict access, not the validator.
- `test_a3_exploration_item_cannot_be_committed`: Asserts `entry["plane"] != "commitment"` on a dict it just created. Tests nothing.
- `test_a4_demotion_must_have_reason`: Creates a dict with empty reason, asserts it's empty. Tests nothing.
- `test_a5_feedback_is_not_evidence`: Asserts "feedback_received" is not in a set it just defined. Tests nothing.

**5 out of 6 attack tests are pseudo-tests that verify their own dicts.**

### 6. Test Coverage
- Normal tests: adequate happy path
- Attack tests: 5/6 are pseudo-tests (see above)
- Only `test_a6_main_not_modified` is real (git check)

### 7. Duplicate Test Logic
Q29R hash check + main check duplicated from Q33.

### 8-10. Clean.

### 11-12. NOT INTEGRATED.

### 13-14. Clean.

### 15. Assessment
**DEMO_ONLY_NOT_GENERALIZED** — Validator has real gate logic but 5/6 attack tests are self-referential pseudo-tests that prove nothing. The validator is never called with mutated inputs.

---

## Q35: Agent Duty

### 1. Quantitative
- 6 data files (task-states, duty-contracts, action-traces, escalation-records, tool-permissions)
- 1 schema (agent-duty)
- 1 validator (93 lines)
- 11 tests (5 normal + 6 attack)

### 2. Runtime Integration
No runtime state machine. State transitions defined in JSON but never enforced by executable runtime. Validator checks static consistency only.

### 3. Semantic Validation
Validator checks:
- State machine: all transitions reference valid states
- Contracts: rule, blocked_actions, requires_human_decision, claim_ceiling present
- Permissions: main push must not be allowed
- Traces: state_from and state_to must be valid, transitions must be in transition table

**Verdict: SEMANTIC — good static checks, but no runtime enforcement**

### 4. Dead Code
`escalation-records.json` is empty (no entries). Validator never reads it.

### 5. Pseudo-Validation
- `test_a4_no_self_accept`: Filters `blocked_actions` by `"self" in a.lower()` and asserts "accept" is not in the filtered list. This checks that no blocked action contains both "self" and equals "accept" — it does NOT test that self-review is blocked. The actual blocked_actions value is "self_review_accept", and `"self" in "self_review_accept".lower()` is True, so the filter returns ["self_review_accept"], then it asserts "accept" is not in ["self_review_accept"] — which passes because "accept" != "self_review_accept". This is a pseudo-test.

### 6-7. Q29R + main checks duplicated.

### 8-10. Clean.

### 11-12. NOT INTEGRATED.

### 15. Assessment
**PARTIALLY_OPERATIONAL** — Real state machine and permission validator. Missing:
- Runtime enforcement (state machine is data, not code)
- Escalation records unused
- No cross-agent conflict detection
- No permission escalation path check
- `test_a4_no_self_accept` is a pseudo-test

---

## Q36: Temporal Causality

### 1. Quantitative
- 4 registries (prediction-records, intervention-candidates, observation-records, expiry-decisions)
- 1 schema (temporal-causal)
- 1 validator (69 lines)
- 6 tests (3 normal + 3 attack)

### 2. Runtime Integration
No runtime. No expiry enforcement.

### 3. Semantic Validation
Validator checks:
- Predictions: 7 required fields present
- No "proof" in claim_ceiling
- Interventions: counterfactual field required
- No forbidden causal shortcuts (reachability, repetition, analogy, synchronization)

**Verdict: PARTIALLY SEMANTIC — field presence + string checks, no temporal logic**

### 4. Dead Code
`expiry-decisions.json` is empty. Validator never checks expiry against real dates.

### 5. Pseudo-Validation — CRITICAL BUG
- `test_a1_reachability_not_causation`: Creates a `doc` variable with malicious mechanism text but then calls `validate_no_reachability_as_causation()` which reads from the ORIGINAL data file, not the crafted `doc`. The `doc` variable is never used. This test does nothing.

### 6. Test Coverage
- 3 normal tests: adequate
- 3 attack tests: 1 is broken (see above), 2 are field presence checks

### 7-10. Clean.

### 11-12. NOT INTEGRATED.

### 15. Assessment
**DEMO_ONLY_NOT_GENERALIZED** — `test_a1` has a critical bug where the mutation is never applied. Expiry logic is missing. No observation-prediction consistency validation beyond ID reference.

---

## Q37: Analogy Audit

### 1. Quantitative
- 2 registries (analogy-candidates, non-correspondence-residue)
- 1 schema (analogy-audit)
- 1 validator (62 lines)
- 7 tests (3 normal + 4 attack)

### 2. Runtime Integration
No runtime. No analogy engine. Purely static registry + field checks.

### 3. Semantic Validation
Validator checks:
- Domains present (source_domain, target_domain)
- Structural correspondence exists (not empty)
- Non-correspondence residue exists
- Hidden premise transfer exists
- Claim ceiling present and not "formal_equivalence"
- Negative transfer analysis present
- Residue linkage: analogy_id references valid analogy

**Verdict: FIELD PRESENCE ONLY — never evaluates quality of structural correspondence, never checks if non-correspondence is meaningful**

### 4. Dead Code
None.

### 5. Pseudo-Validation
No pseudo-tests, but validator only checks field existence.

### 6-7. Duplicated Q29R + main checks.

### 8-10. Clean.

### 11-12. NOT INTEGRATED.

### 15. Assessment
**SCHEMA_ONLY_NOT_OPERATIONAL** — Validator only checks that fields exist and are non-empty. No runtime analogy evaluation. No structural correspondence algorithm. One fixture entry is the entire dataset.

---

## Q38: Structural Retrieval

### 1. Quantitative
- 3 registries (relation-signatures, case-structures, counterexample-set)
- 1 schema (structural-retrieval)
- 1 validator (57 lines)
- 7 tests (3 normal + 4 attack)

### 2. Runtime Integration
No runtime. No retrieval algorithm. No search engine.

### 3. Semantic Validation
Validator checks:
- Relation signatures have type and arguments
- Cases reference valid signature IDs
- Cases have claim_ceiling
- Counterexamples reference valid case pairs

**Verdict: REFERENCE INTEGRITY ONLY — no retrieval, no search, no matching algorithm**

### 4-5. Clean.

### 6. Test Coverage
- `test_a1_no_spurious_confidence`: Checks that "similarity_score" and "confidence" keys don't exist in case entries. This is a schema conformance check, not a test of behavior.
- `test_a3_vector_similarity_is_not_structural`: Asserts "vector_similarity" is not in a hardcoded set. This tests nothing about the actual data or validator.

### 7-10. Clean.

### 11-12. NOT INTEGRATED.

### 15. Assessment
**SCHEMA_ONLY_NOT_OPERATIONAL** — No retrieval algorithm exists. Only reference integrity between static registries. No way to query or search. Counterexample coverage is a single entry.

---

## Q39: Failure Memory

### 1. Quantitative
- 3 registries (failure-records with 11 entries, recurrence-signatures, repair-propagation)
- 1 schema (failure-memory)
- 1 validator (61 lines)
- 9 tests

### 2. Runtime Integration
No runtime failure detection. Static registry of past Q32 failures only.

### 3. Semantic Validation
Validator checks:
- Required fields (failure_class, mechanism, source_iteration, missed_gate, repair_type, regression_test)
- Claim ceiling present
- Missed gate present
- Recurrence signature references valid failure IDs
- Repair propagation references valid failure IDs
- Overfitting risk present

**Verdict: FIELD PRESENCE + REFERENCE INTEGRITY — no runtime failure detection, no recurrence detection algorithm**

### 4. Dead Code
`escalation-records.json` from Q35 exists but is never read by Q39.

### 5. Pseudo-Validation
No pseudo-tests, but validator only checks field presence.

### 6. Test Coverage
- 11 failure records from Q32 history
- But validator never checks if failure records accurately describe the actual failures
- No test that a NEW failure would be properly detected and recorded
- `test_a2_no_over_institutionalization`: Just checks `overfitting_risk` is in enum — field presence check

### 7-10. Clean.

### 11-12. NOT INTEGRATED.

### 15. Assessment
**DEMO_ONLY_NOT_GENERALIZED** — 11 pilot failures are a static registry. No runtime failure detection, no recurrence detection, no automatic repair propagation. The system cannot detect a NEW failure — it only validates that pre-recorded failures have required fields.

---

## Cross-Cutting Findings

### F1: Duplicated Guard Tests
Q29R hash check and main-not-modified check are copy-pasted across all 7 stages (12 duplicate tests total). These should be shared fixtures, not per-stage copies.

### F2: No Propagation Closure Integration
None of Q33-Q39 validators integrate with the Q32 propagation closure system. All operate in isolation.

### F3: No System Map Integration
None of Q33-Q39 objects appear in the system map candidate entries.

### F4: No Cross-Stage Communication
Each stage is a silo. No test verifies that Q33 rights gate blocks Q34 commitment, or that Q35 agent duty generates Q39 failure records.

### F5: Validators Read Only Own Data
Each validator reads only its own `data/<stage>/` directory. No validator checks references across stages.

### F6: No Runtime Enforcement
All validators are batch validators that read static JSON. No runtime component enforces any of these rules during actual operation.

### F7: Attack Test Quality
- Q33: 10/10 genuine (call real validator with mutated input)
- Q34: 1/6 genuine (5 are self-referential pseudo-tests)
- Q35: 5/6 genuine (1 is a logic confusion pseudo-test)
- Q36: 0/3 genuine (1 has broken mutation, 2 are field checks)
- Q37: 4/4 genuine but only test field presence
- Q38: 2/4 genuine (2 test hardcoded sets)
- Q39: reasonable but only field presence

**Overall genuine attack tests: ~22 out of 38 (58%)**

### F8: Claim Vocabulary
No overclaiming found. All stages use appropriate hedging language (LAB, SPECULATIVE, NON-AUTHORITATIVE).

### F9: Missing Stage Result Files
Only Q33 has a stage result file (`STAGE_RESULTS/LAB-121Q33-result.md`). Q34-Q39 are missing.
