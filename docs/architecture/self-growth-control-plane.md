# Self-Growth Control Plane / 自成长控制面(反思–成长合同)

Status: DRAFT SCAFFOLD (stacked on production/ignition-run-promote-evolve-r1 @ 6723cdfa) — not a Current capability

This document is the **reflection / growth control-plane contract** (Plane 6) of the Adaptive Relational Runtime (ARR) R1 scaffold. It is a Draft/candidate scaffold contract, not a Current capability. It defines failure attribution, feedback records, growth signals and the EVOLVE-candidate gate. **No actual EVOLVE is authorized, designed or reachable in this scaffold**: the gate state machine structurally contains no out-edge to any execution state. An engineering signal never becomes an EVOLVE candidate from one failure.

## Boundary rules

- A failure record is evidence, not a defect verdict; governance/value-boundary refusal is a legitimate failure class, not an error.
- One failure can never produce an EVOLVE candidate; recurrence without measured loss remains an engineering signal only.
- An EVOLVE candidate is a status, not an action; the state machine has no EXECUTING / APPLIED / CONSUMED states and no execute/apply/trigger/auto-* fields.
- Feedback and growth signals are Plane 6 record kinds; they never rewrite Plane 1–5 records.
- UNKNOWN is a legitimate terminal state, not a wastebasket; unclassifiable failures classify as UNKNOWN, never as the "nearest" class.
- Decorative confidence numbers, priorities and scores are forbidden fields.
- Negative history is preserved: superseded, rejected, withdrawn and archived records remain replayable (aligned with `case_failures/` conventions).

## 1. Failure taxonomy (eight classes)

Versioned `failure-classes` registry; each entry carries `class_id / definition / machine_criteria / boundary_tests / disposition_policy / q39_mapping` (lineage to the predecessor Q39 failure-lineage enum).

| class_id | Definition (failure located in …) | Sole allowed disposition |
|---|---|---|
| `INPUT_SOURCE` | source side: missing/corrupt/unreadable source, provenance fail-closed, rights-restricted content, malformed temporal metadata held as UNKNOWN; no Object record yet produced; removable by repairing/replacing the source | `REPAIR_SOURCE` |
| `EXTRACTION_MODEL` | interpretation/extraction: source intact, but source→observation→object transform mismatches the source (misread, reconstruction written as explicit, missing alternatives) | `REPAIR_EXTRACTOR` |
| `REPRESENTATION` | representation capacity: extraction correct, but the target schema/envelope cannot carry it losslessly (higher-order collapse, state/event conflation, temporal-semantic loss, projection semantic mismatch while routing itself executed per contract) | `EXTEND_REPRESENTATION` (explicit namespace + schema contract; silent field addition forbidden) |
| `MECHANISM` | mechanism contract/execution binding: missing input contract, undeclared side effect, unregistered capability, failed precondition, output-contract violation, deterministic stub mismatching its declaration | `REPAIR_MECHANISM_CONTRACT` |
| `INFRASTRUCTURE_RUNTIME` | substrate: store crashes, pointer/manifest corruption, validator self-failure, environment-induced replay divergence, CI/toolchain failure | `REPAIR_INFRA` |
| `ARCHITECTURE` | the architecture contract itself: missing/contradictory plane boundaries, undecidable routing on legal input, contract-vs-invariant conflicts, unsatisfiable cross-plane composition; counterfactual test: failure persists with a perfect source and per-component compliance, across all objects on the path | `ARCHITECTURE_REVIEW` (ADR + independent acceptance; no component self-repairs) |
| `GOVERNANCE_REFUSAL` | governance/value-boundary refusal: the system correctly refuses per governance contract (rights boundary, Charter, claim ceiling, auto-PROMOTE/auto-EVOLVE prohibition, external-action prohibition) while the requester's goal is unmet | `GOVERNANCE_REVIEW` (human-initiated only) |
| `UNKNOWN` | unclassifiable: insufficient or contradictory criterion inputs; fail-closed | `NEED_MORE_EVIDENCE` |

Two boundary tests are machine-executed by the classifier:

- **Boundary A — INPUT_SOURCE vs ARCHITECTURE**: (i) counterfactual — does the failure reproduce with a synthetic perfect source? yes ⇒ ARCHITECTURE-leaning, no ⇒ INPUT_SOURCE; (ii) scope — failure confined to objects derived from this source ⇒ INPUT_SOURCE; spanning all objects on the same contract path ⇒ ARCHITECTURE-leaning. Recurrent INPUT_SOURCE failures never auto-upgrade to ARCHITECTURE; reclassification requires the counterfactual test and leaves a supersession trail.
- **Boundary B — EXTRACTION_MODEL vs MECHANISM**: (i) removal test — remove mechanism execution; failure persists ⇒ EXTRACTION_MODEL or REPRESENTATION; (ii) input-object review — mechanism consumer's input object correct + failure at a mechanism-contract check ⇒ MECHANISM; object itself mismatches source ⇒ EXTRACTION_MODEL.

Any missing or contradictory criterion input forces `UNKNOWN`. UNKNOWN-classified signals never satisfy gate G1 (§3).

## 2. FeedbackRecord contract

Closed schema (`additionalProperties: false`), Draft 2020-12:

- `feedback_id = "fb_" + sha256(canonical(failure_event_ref, failure_class, affected_object_refs))[:32]` — deterministic, independent of list order, wall clock and file paths.
- `schema_version`, `contract_version`.
- `failure_event_ref` — typed reference to the triggering record (operation receipt id / validator receipt / human record id); content never embedded.
- `failure_class` — one of the eight classes.
- `classification_evidence` — array of `{criterion_id, result: HIT | EXCLUDED | NOT_EVALUABLE, evidence_ref}`, recording both hit and excluded criteria.
- `classification_status ∈ {CLASSIFIED, PROVISIONAL, UNKNOWN_FALLBACK}`; no `classification_confidence`-style numeric field exists.
- Time separation: `event_at` (failure), `observed_at` (observation), `ingested_at` (Plane 6 ingestion); nullable; malformed temporal metadata stays UNKNOWN, never guessed.
- `affected_object_refs`, `source_refs`; private-corpus sources appear only as content hash + typed reference + rights-boundary declaration.
- `environment` — `{runtime_version, contract_version, provider_identity}` (self-declared; does not constitute provenance truth).
- `disposition_hint` — the class's sole allowed disposition enum value; a hint, not a repair action.
- `causal_status ∈ {UNKNOWN, CANDIDATE, NOT_ESTABLISHED}` (Q39 lineage; feedback never asserts established causality).
- `claim_ceiling` — default UNKNOWN or SECONDARY, never above the ceiling the source tiers allow.

## 3. GrowthSignal contract and the EVOLVE-candidate gate

Closed schema; `signal_id = "gs_" + sha256(canonical(failure_class, sorted(feedback_refs)))[:32]`. One signal per failure class — mixed-class signals are forbidden. Required fields: `failure_class`, `feedback_refs` (minItems 1), `title`, `description`, the six gate fields below, `gate_evaluation`, `status`.

Six gate fields (any missing ⇒ gate FAIL; no defaults):

1. `scope {object_refs, source_refs, domain_span}` — G2: ≥ 2 distinct object refs and ≥ 2 distinct, non-overlapping source refs.
2. `measured_loss {loss_type, metric, value, unit, measurement_method, baseline}` or `null` — G3: non-null and `measurement_method` deterministically replayable. `loss_type ∈ {VALIDATION_FAILURE, REPLAY_DIVERGENCE, CLAIM_DOWNGRADE, THROUGHPUT_BLOCK, HUMAN_REVIEW_LOAD, OTHER_DECLARED}`.
3. `recurrence_evidence` — array of `{object_ref, source_ref, failure_event_ref, reproduction_method, reproduction_digest}` — G1: ≥ 2 entries, object refs pairwise distinct, source refs pairwise distinct, every reproduction digest replay-verifiable.
4. `workaround_assessment {assessed, adequate_low_cost_exists, candidates_considered, rationale}` — G4: `assessed = true` and `adequate_low_cost_exists = false`. If an adequate low-cost workaround exists, the disposition is "adopt workaround and record"; the signal stays SIGNAL_ONLY.
5. `minimal_repair_hypothesis {hypothesis, touched_surface, falsification_test, rollback_path}` — G5: all four non-empty; `falsification_test` falsifiable (references an executable check); `touched_surface` declares the minimal affected surface. Specialization G5g: for GOVERNANCE_REFUSAL signals, a hypothesis touching removal/weakening of a governance registry entry, claim ceiling, Charter boundary or the auto-EVOLVE prohibition is a hard gate rejection.
6. `human_authorization {authorized_by, authorization_ref, authorized_at, scope_of_authorization, verified}` — G6: `authorization_ref` is an externally verifiable reference; `verified` is written **by the gate evaluator** (fail-closed; callers can never self-assert `verified: true`).

Forbidden fields on a growth signal: `confidence`, `priority`, any `auto_*` trigger field, any execute/apply/trigger-semantics field.

`gate_evaluation`: `{items: [{gate_id: G1..G6, result: PASS|FAIL, evidence_ref}], evaluated_at, evaluator_version, decision_digest}`.

## 4. Gate state machine (no execution out-edges)

```
                 (created into)
                      │
                      ▼
              ┌──────────────┐   all six gates PASS + explicit human authorization
              │ SIGNAL_ONLY  │ ──────────────────────────────┐
              └──────────────┘                               ▼
                 │  ▲                                 ┌──────────────────┐
                 │  │ any gate FAILs / evidence       │ EVOLVE_CANDIDATE │   terminal status of
                 │  └──────────────────────────────── │ (status, not     │   this scaffold:
                 ▼                                    │  an action)      │   zero out-edges to
        REJECTED / ARCHIVED / SUPERSEDED /            └──────────────────┘   execution
        WITHDRAWN  (human- or expiry-driven terminal/history states, full history preserved)
```

- **R1 (single-failure hard block)**: `feedback_refs` length 1 or `recurrence_evidence` < 2 independent objects ⇒ G1 FAIL; the signal stays SIGNAL_ONLY forever. No "single failure → candidate" transition exists in the state machine.
- **R2 (recurrence without loss)**: G1/G2 PASS but `measured_loss = null` ⇒ G3 FAIL; stays SIGNAL_ONLY (an informational "reproduced" marker is allowed).
- **R3 (all six ⇒ candidate only)**: the only reachable target of a full pass is `EVOLVE_CANDIDATE`; that state has **no out-edge** to EXECUTING / APPLIED / CONSUMED — those enum values do not exist in the schema. This is a structural absence, not a disabled transition.
- **Regression**: if the evidence behind a previously PASS gate item fails on replay (e.g. reproduction-digest mismatch), status regresses to SIGNAL_ONLY with a receipt; history is never deleted.

Every evaluation/transition emits a `GateEvaluationReceipt`: `{receipt_id, signal_id, from_status, to_status, gate_items[6], evaluator_version, evaluated_at, decision_digest, self_final_sha_claimed: false, live_refetch_required: true}` — deterministic, offline, replayable; same signal content + same evaluator version ⇒ same decision digest. Receipts are Plane 6 records and never write back to the predecessor engineering-signal ledger.

## 5. Lifecycle orthogonality (ten states, 26 edges)

Plane 6 records reuse the Plane 5 lifecycle vocabulary as an **orthogonal axis** beside the Foundation nine-axis status system and the classification states; no axis value is derived from another axis. Ten states: `OBSERVED / PROVISIONAL / CANDIDATE / SUPPORTED / CONTESTED / SUPERSEDED / ARCHIVED / REACTIVATED / REJECTED / UNKNOWN`. The legal directed edges (26) are registered in the versioned `lifecycle-transitions` registry with per-edge guard-expression hashes:

```
OBSERVED    → PROVISIONAL | UNKNOWN | REJECTED
PROVISIONAL → CANDIDATE | UNKNOWN | REJECTED
CANDIDATE   → SUPPORTED | CONTESTED | REJECTED | UNKNOWN | ARCHIVED
SUPPORTED   → CONTESTED | SUPERSEDED | ARCHIVED | UNKNOWN
CONTESTED   → SUPPORTED | REJECTED | SUPERSEDED | UNKNOWN | ARCHIVED
SUPERSEDED  → ARCHIVED
ARCHIVED    → REACTIVATED
REACTIVATED → PROVISIONAL | CANDIDATE
REJECTED    → (terminal, no out-edge)
UNKNOWN     → OBSERVED | PROVISIONAL
```

Machine-checked reject reason codes (11): `EDGE_NOT_IN_TRANSITION_REGISTRY`, `UNKNOWN_TO_SUPPORTED_DIRECT`, `REACTIVATED_TO_SUPPORTED_DIRECT`, `REJECTED_IS_TERMINAL`, `SUPERSESSION_HISTORY_MISSING`, `REPETITION_COUNT_PROMOTION`, `CEILING_EXCEEDED`, `INDEPENDENCE_NOT_DECLARED`, `OPPOSING_EVIDENCE_UNDISPOSED`, `TEMPORAL_MALFORMED_FAIL_TO_UNKNOWN`, `PROVENANCE_MISSING`. Repetition-count promotion is blocked at three layers: the schemas contain no occurrence-count fields; transition guards evaluate only deduplicated independent-evidence sets; the transition registry pins each guard's expression hash.

ARCHIVED → REACTIVATED preserves identity (same `record_id`, content digest unchanged) and appends a reactivation event; the archive record is neither deleted nor modified. SUPERSEDED preserves the original record, its digest and its valid time range in full.

## 6. Anti-auto-EVOLVE structural guarantees

1. **Zero reference**: no module under `tools/adaptive_relational_runtime/` imports or string-references the predecessor promote/evolve/transaction paths; CI static scanning fails the build on violation.
2. **Zero call path**: no subprocess/CLI/function call toward EVOLVE/PROMOTE exists; the call-point whitelist is empty; the production receipt adapter is consume-only.
3. **No execution edge**: the growth-signal-gates registry and the state-machine schema contain no EVOLVE_CANDIDATE out-edge and no execute/apply/trigger/auto-* fields; violating documents fail Draft 2020-12 validation directly.
4. **Receipts only**: the skeleton can validate, classify, evaluate and emit receipts; it never silently calls networks, PROMOTE or EVOLVE.
5. **Counters**: `AUTO_EVOLVE_STARTED=0` and `FORMAL_ASSETS_PROMOTED=0` enter the final task counters.

## 7. Governance boundary

A `GOVERNANCE_REFUSAL` record makes refusals countable, auditable and reviewable; it never enters the repair pipeline. Governance boundary changes travel exclusively through the ITERATION.md §13 self-iteration path (human initiation + independent acceptance + ordinary merge), entirely outside this runtime. Value grounds are referenced by typed reference to `docs/governance/life-community-value-charter.md` and the non-sycophancy protocol; texts are never copied. This scaffold does not change the ITERATION.md method version (1.3.0) or its semantics.
