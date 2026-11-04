# Adaptive Relational Runtime ADRs / 架构决策记录

Status: DRAFT SCAFFOLD (stacked on production/ignition-run-promote-evolve-r1 @ 6723cdfa) — not a Current capability

Architecture decision records for the Adaptive Relational Runtime (ARR) R1 scaffold. Each ADR records a decision made during scaffold drafting, its context, the rejected alternatives and its consequences. These ADRs are part of a Draft/candidate scaffold; they record design intent under independent review, not accepted project direction.

---

## ADR-1: Nine primitives instead of a large domain ontology

- **Status**: Draft (proposed for this scaffold)
- **Context**: Plane 2 (Objectization) needs a cross-domain object model that can carry text, Git/code, structured data, runtime receipts and declared events without per-domain schema forking. A large domain ontology would freeze premature type commitments, invite silent semantic drift, and duplicate the Foundation's existing object/evidence/claim registries.
- **Decision**: Adopt exactly nine primitives — Source, Observation, Object, State, Event, Assertion, Relation, Mechanism, Action — behind one shared closed envelope (12 fields), with deterministic identity, six time scales, a five-level explicitness vocabulary and an explicit rights boundary. Domain-specific vocabulary lives exclusively in versioned registries (`object-types`, `assertion-types`, `relation-types`, `mechanism-types`) and in a registered `x_`-prefixed extension namespace.
- **Rejected alternatives**: (a) a large domain ontology — rejected as over-commitment and a maintenance hazard; (b) per-source-type record families — rejected because they break cross-object fixtures and deterministic replay; (c) open/duck-typed records — rejected because stable interoperability objects must reject undeclared fields.
- **Consequences**: every record is exactly one `record_kind`; mixing layers is a schema error; domain growth is a registry-version event with `status`/`since_version` tracking; schema closures (`additionalProperties: false`) make undeclared-field attacks fail at validation.

## ADR-2: Routing is a pre-gate that reuses existing engine validators

- **Status**: Draft
- **Context**: Plane 3 must decide where a relation record goes (ARN, MCF review, PSD with boundary, REJECT, QUARANTINE_UNKNOWN). ARN, MCF and PSD each already carry complete validators with anti-overclaim guards, temporal mechanics and residue obligations. Re-implementing engine validation inside the router would duplicate authority and drift from it.
- **Decision**: The projection router is a **pre-gate only**: deterministic R1–R13 routing rules, cue lexicons and anti-overclaim bindings held in versioned data registries, plus engine-specific preconditions it must guarantee up front (PSD five-part boundary, MCF handoff initial-class restriction, temporal impossibility rejection). After routing, the existing engine validators remain the authority on their own instances; the router never widens engine semantics and never skips engine validation.
- **Rejected alternatives**: (a) router re-validates engine instances — rejected as duplicated authority; (b) router bypasses engine validators and writes engine objects directly — rejected as semantic widening; (c) natural-language routing conditions — rejected; all criteria must be machine-executable registry data.
- **Consequences**: routing decisions are pure functions of (relation record, registry snapshot) and emit replayable receipts carrying the registry snapshot hash; engine validators stay untouched; "sent to the wrong engine" or "sent with overclaiming semantics" fails at the pre-gate.

## ADR-3: The skeleton is a non-executor; it emits receipts only

- **Status**: Draft
- **Context**: Plane 4 must connect mechanism contracts to execution without creating a second general executor beside Function OS and the production runtime. Any real execution capability inside the scaffold would violate the task's anti-second-executor invariant and blur the RUN/PROMOTE/EVOLVE mode boundaries.
- **Decision**: The runtime skeleton's capability whitelist is exactly five verbs — validate, transform, route, diff, emit receipts. Real executable work routes only to existing registered Function OS capabilities (via read-only capability queries, terminating in adapter receipts inside R1) or to deterministic stubs (which emit receipts with `stub: true`, `side_effects_realized: []`, `real_world_action: false`). Production receipts are consumed through a read-only adapter. The skeleton never imports RUN-write/PROMOTE/EVOLVE paths, never calls networks, never performs external actions; static AST/text scanning and a runtime `sys.modules` assertion make this machine-checkable.
- **Rejected alternatives**: (a) a thin executor with "safe" subprocess calls — rejected (second executor); (b) direct invocation of production RUN writes — rejected (mode-boundary violation); (c) optional network access behind flags — rejected (non-deterministic, un-auditable).
- **Consequences**: all scaffold outputs are deterministic, offline and replayable; execution success is never evidence for claim elevation; `REAL_WORLD_ACTIONS=0` and `AUTO_EVOLVE_STARTED=0` stay structurally guaranteed rather than policy-guarded.

## ADR-4: Schemas live under `schemas/architecture/adaptive-relational-runtime/`

- **Status**: Draft
- **Context**: The repository splits schemas by domain directory with two naming conventions: `schemas/architecture/` holds kebab-case schemas for derived/candidate representations (ARN, MCF, PSD, Q12–Q14 overlays), while `schemas/ignition_runtime/` holds snake_case schemas for the production runtime. The ARR scaffold is a horizontal architecture plane built on top of — but not part of — the production runtime.
- **Decision**: Place the 13 record schemas plus the registry envelope schema under `schemas/architecture/adaptive-relational-runtime/` in kebab-case (`source-record.schema.json`, …, `adaptive-relational-runtime-registry.schema.json`). Registries themselves live under `data/architecture/adaptive-relational-runtime/registries/`, mirroring the `data/architecture/adaptive-relational-network/` precedent. The execution-receipt adapter schema **references** the predecessor `schemas/ignition_runtime/operation_receipt.schema.json` field contract verbatim (13 required fields, const gates) but lives in the architecture directory as an adapter record, because it is a consumer-side contract, not a producer schema.
- **Rejected alternatives**: (a) `schemas/ignition_runtime/` — rejected: the scaffold is not part of the production runtime and must not enter its CI blast radius or its snake_case production contract surface; (b) a new top-level `schemas/adaptive-relational-runtime/` — rejected: breaks the existing domain-directory convention; (c) flattening all 13 records into one mega-schema — rejected: per-record files match the satellite-schema convention and keep validation errors attributable.
- **Consequences**: `schemas/architecture/**` and `data/architecture/**` are already inside the foundation-validation CI path filter, so commit-2 content is covered without workflow edits; the production-runtime CI (`ignition-production-validation.yml`) stays untouched, consistent with the scaffold's read-only relationship to it.

## ADR-5: Tests live under `tests/adaptive_relational_runtime/` (pytest, runtime-level)

- **Status**: Draft
- **Context**: Two repository-native test layouts exist: top-level `tests/test_*.py` in unittest style (the Q21–Q23 derived-representation convention) and `tests/ignition_runtime/` in pytest style (the runtime convention with the 45-scenario suite). The ARR scaffold includes a runtime skeleton whose fixtures must replay deterministically and whose scenario evidence (40-scenario matrix) resembles the production runtime's adversarial suite more than the derived-representation smoke tests.
- **Decision**: Adopt the runtime-level layout `tests/adaptive_relational_runtime/` with pytest, mirroring `tests/ignition_runtime/`: fixture-driven, scenario-indexed, replayable, with raw command/exit-status capture for the acceptance matrix. The scaffold deliberately does **not** mix both conventions.
- **Rejected alternatives**: (a) top-level `tests/test_adaptive_relational_runtime*.py` unittest trio — rejected: the scenario/replay character of the acceptance matrix fits the pytest runtime convention better, and the unittest trio convention belongs to derived representations (ARN/MCF/PSD) whereas this scaffold spans a runtime plane; (b) mixing both — rejected explicitly by repository convention (choose one).
- **Consequences**: CI wiring (adding the new test path to the appropriate workflow) is a commit-5 obligation and is recorded as such; test evidence maps one-to-one onto the 40-scenario acceptance matrix.

## ADR-6: Lifecycle is an orthogonal axis; no derivation between the lifecycle ten-state machine and the Foundation nine axes

- **Status**: Draft
- **Context**: The Foundation already maintains a nine-axis status system (workflow, semantic, formal, logic, proof, evidence, scope, provenance, migration) plus classification states (`PROVISIONAL / ADJUDICATED / CONTESTED`). Plane 5/6 need an asset-level lifecycle (OBSERVED … UNKNOWN, ten states, 26 registered edges). Letting either system derive states from the other would create hidden coupling, let a single-axis success masquerade as overall validity, and contradict the Foundation rule that no axis's success propagates to another axis.
- **Decision**: The lifecycle ten-state machine is a **new, orthogonal axis**: it describes an object's persistence stage as an asset, while the nine axes describe evaluation status of propositions, and classification states record adjudication outcomes. No transition in the lifecycle machine reads a nine-axis value as its guard; no nine-axis update reads lifecycle state. ARCHIVED → REACTIVATED preserves identity and history within the lifecycle axis only. Shared vocabulary (e.g. `PROVISIONAL`, `CONTESTED`, `UNKNOWN`) is documented as axis-local and never cross-derived.
- **Rejected alternatives**: (a) deriving lifecycle from the evidence axis (e.g. "enough evidence ⇒ SUPPORTED") — rejected: repetition-count promotion in disguise; (b) collapsing the classification states into the lifecycle — rejected: destroys the Foundation's independent-adjudication semantics; (c) a single merged mega-status — rejected: hides provenance of every judgment.
- **Consequences**: transitions require explicit events with machine-checked reason codes (11 codes in the registry); UNKNOWN can never silently become SUPPORTED on any axis; auditors can replay lifecycle history without re-evaluating Foundation claims.

---

These ADRs cover the minimum decision set for commit 1. Further decisions (fixture policy, CI wiring, registry synchronization) are recorded with their respective commits.
