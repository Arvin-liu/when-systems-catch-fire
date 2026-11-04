# Adaptive Relational Runtime / 自适应关系运行时(R1 Scaffold 主合同)

Status: DRAFT SCAFFOLD (stacked on production/ignition-run-promote-evolve-r1 @ 6723cdfa) — not a Current capability

This document is the **main architecture contract** of the Ignition Adaptive Relational Runtime (ARR) R1 scaffold. It is a Draft/candidate scaffold contract: it describes an architecture under independent review, not a merged Current capability, not a validated production runtime, and not evidence of real-world, scientific or causal validity. It follows the repository-native format of `docs/architecture/adaptive-relational-network.md` (Status line + Boundary Rules + Core Objects) and adds nothing to the canonical truth surfaces.

The ARR is a **horizontal runtime plane**: a connective contract layer that links the existing Foundation, Ψ₀ meta-judgment, Function OS candidate, Adaptive Relational Network (ARN), Multiscale Causal Fabric (MCF), Probabilistic System Dynamics (PSD), the production RUN/PROMOTE/EVOLVE runtime (`tools/ignition_runtime`), the evidence lifecycle vocabulary, reality feedback channels and iteration governance — without replacing, duplicating or subordinating any of them.

## The stable loop

The runtime expresses one closed loop, executed across existing components:

```
OBSERVE → OBJECTIFY → RELATE → PROJECT → MECHANIZE → RUN → EVALUATE → REFLECT → GOVERN → FEEDBACK
```

Loop stages map to planes and predecessors as follows:

| Stage | Plane / owner | Existing authority consumed (reference only) |
|---|---|---|
| OBSERVE | Plane 1 Source / Observation | typed references to text, audio, image, video, code, commits, PRs, CI, structured data, runtime receipts, institutions, declared real-world events |
| OBJECTIFY | Plane 2 Objectization | nine minimal primitives (see `object-relation-mechanism-model.md`) |
| RELATE | Plane 2 Relation records | typed, non-causal-by-default relation envelope |
| PROJECT | Plane 3 Relational Projection | routes to ARN / MCF / PSD without replacing their schemas or semantics |
| MECHANIZE | Plane 4 Mechanism contract | seven-element mechanism contract; executable surface points at existing Function OS capabilities or deterministic stubs only |
| RUN | external execution | production `tools/ignition_runtime` RUN mode is the only legitimate production execution surface; the scaffold itself never executes real-world actions |
| EVALUATE | Plane 5 Evidence / Lifecycle | claim ceilings, UNKNOWN preservation, ten-state lifecycle, no repetition-count promotion |
| REFLECT | Plane 6 Reflection | eight-class failure attribution (see `self-growth-control-plane.md`) |
| GOVERN | kernel + Charter | Charter Gate, claim ceilings, anti-auto-PROMOTE / anti-auto-EVOLVE hard boundaries |
| FEEDBACK | Plane 6 Growth signals | engineering signals and a structurally execution-free EVOLVE-candidate gate |

The loop is a **contract, not a pipeline implementation**. The R1 scaffold defines the records, registries, routing rules and receipt formats that would let the loop be replayed deterministically offline; it does not close the loop in production.

## One kernel, six planes

### Kernel — judgment and governance core

The kernel **references** existing authoritative boundaries rather than duplicating them:

- Foundation object / evidence / claim status (`FOUNDATION.md`, `data/foundation/`, `docs/foundation/status-system.md`).
- Ψ₀ meta-judgment and convergence boundaries (`docs/phi_meta_law.md`, `ARCHITECTURE.md` core-system classification: Ψ₀ is a workflow orchestrator, not a proof function).
- Claim ceilings and UNKNOWN preservation (`tools/ignition_runtime/epistemic.py` tier/ceiling vocabulary).
- Charter normative constraints (`docs/governance/life-community-value-charter.md`, Charter Gate in `ARCHITECTURE.md`).
- Iteration propagation, rollback and completion semantics (`ITERATION.md`, method version 1.3.0, unchanged).

The scaffold must not modify the Ψ₀ formula, create a second Foundation, or claim a new truth layer.

### Plane 1 — Source / Observation

Accepts typed references to sources and separates the act of observation from the source bytes. Invariant:

`source bytes/reference ≠ observation ≠ interpretation ≠ assertion ≠ mechanism`

### Plane 2 — Objectization

Nine minimal primitives — Source, Observation, Object, State, Event, Assertion, Relation, Mechanism, Action — with a shared closed envelope, deterministic identity, six time scales and a five-level explicitness vocabulary. Full contract: `docs/architecture/object-relation-mechanism-model.md`. No giant domain ontology; domain types live in versioned registries.

### Plane 3 — Relational Projection

Deterministic routing of relation records toward existing engines:

- broad heterogeneous, temporal, role, support, conflict and dependency relations → ARN;
- explicit causal claim or intervention semantics → MCF review/delegation (handoff record only; the scaffold never writes MCF fabric);
- stochastic state evolution, risk or probabilistic dynamics → PSD with declared system boundaries; causal claims still require MCF.

Adjacency, recurrence, similarity, embedding distance, graph paths and repeated statements do not become causality, truth, importance or value. Routing is a pre-gate that reuses the existing engine validators; it does not re-validate engine internals and does not widen engine semantics.

### Plane 4 — Mechanism Runtime

A mechanism contract (seven required elements: input contract, preconditions, executable surface, side effects, rollback, output contract, claim ceiling) that can route valid executable work to **existing registered Function OS capabilities** and can consume authoritative operation receipts from `tools/ignition_runtime`. The scaffold is not a second general executor: it may contain validators, adapters, planners and deterministic stubs only, and it emits receipts rather than performing actions.

### Plane 5 — Evidence / Lifecycle

Every assertion, relation and mechanism carries provenance, temporal scope, evidence, alternatives, uncertainty, claim ceiling and lifecycle state. Lifecycle vocabulary (orthogonal axis, ten states):

`OBSERVED / PROVISIONAL / CANDIDATE / SUPPORTED / CONTESTED / SUPERSEDED / ARCHIVED / REACTIVATED / REJECTED / UNKNOWN`

Transitions are explicit, validated against a versioned transition registry (26 edges), and never driven by repetition counts.

### Plane 6 — Reflection / Growth

Failure attribution in eight classes (input/source, extraction/model, representation, mechanism, infrastructure/runtime, architecture, governance/value-boundary refusal, unresolved/UNKNOWN), feedback records, growth signals, and an EVOLVE-candidate gate whose state machine has **no structural out-edge to execution**. Full contract: `docs/architecture/self-growth-control-plane.md`. No actual EVOLVE is authorized.

## Relationship to predecessors (reference only, nothing copied)

| Predecessor | Relationship of the ARR scaffold |
|---|---|
| Foundation (`data/foundation/`, `docs/foundation/`) | Remains authoritative for object, evidence and claim status. The scaffold references the nine-axis status system and never derives lifecycle state from it (orthogonal axes, ADR-6). |
| Ψ₀ (`docs/phi_meta_law.md`) | Referenced as the existing meta-judgment boundary. Formula untouched. |
| Function OS (`function-os-candidate/`) | Consumed as the only legitimate executable capability surface, via read-only capability queries and adapter receipts. The scaffold does not implement N1–N9 nodes. |
| ARN (`tools/adaptive_relational_network/`) | Receives routed relation projections under its own existing schema and validators. Semantics not widened. |
| MCF (`tools/causal_fabric/`) | Receives causal review handoff records only. Causal establishment remains an MCF-internal process. |
| PSD (`tools/probabilistic_system_dynamics/`) | Receives stochastic/risk projections only with a complete declared system boundary. |
| `tools/ignition_runtime` | Production receipts are consumed through a typed read-only adapter that re-verifies schema, identity and the closed-manifest invariants. The scaffold never imports or calls RUN-write, PROMOTE or EVOLVE paths. |
| ITERATION.md | Method version 1.3.0 semantics unchanged; the scaffold only registers itself as a component at synchronization time (commit 5). |

Interoperability details are in `docs/architecture/adaptive-relational-runtime-interop.md`.

## Boundary rules

- The scaffold is a Draft contract and skeleton, not a Current capability.
- The scaffold is not a new L7 and not a new truth layer.
- Representation is not truth; execution success is not truth; repetition is not consensus; graph structure is not causality, importance or value.
- The runtime does not perform external real-world actions, does not call networks silently, and does not invoke PROMOTE or EVOLVE.
- A growth signal is not an EVOLVE candidate from one failure; an EVOLVE candidate is a status, not an action; no EVOLVE execution exists in this scaffold.
- Schema validation and passing tests are repository evidence only; they do not establish scientific, causal, universal or production validity.
- Private external stress corpora (e.g. WAIC) appear only as content hashes, typed references and short original paraphrases (≤ 280 characters) with explicit rights boundaries; no corpus text, bulk titles or audio transcripts are copied.

## Explicit non-goals (R1)

Per the task contract, this scaffold does not:

- run all 836 WAIC notes or summarize WAIC as the task outcome;
- copy private/copyrighted corpus content into the public repository;
- add L7; replace Foundation, Ψ₀, Function OS, ARN, MCF or PSD; modify the Ψ₀ formula;
- create a giant ontology or a second canonical truth store or a second general executor;
- perform external real-world actions; auto-PROMOTE; auto-EVOLVE; promote formal functions, cases or knowledge assets;
- modify PR #109–#119; merge or mark any PR Ready; modify Main; force-push or rewrite history;
- claim scientific, causal, universal or production validity from schemas or tests alone.

## Companion contracts

- `docs/architecture/object-relation-mechanism-model.md` — nine-primitive object model contract.
- `docs/architecture/self-growth-control-plane.md` — reflection / growth control-plane contract.
- `docs/architecture/adaptive-relational-runtime-interop.md` — interoperability contract with ARN / MCF / PSD / Function OS / production runtime / project registry.
- `docs/architecture/adaptive-relational-runtime-adrs.md` — architecture decision records.

All four are equally Draft scaffold contracts, stacked on the same predecessor head, and none of them asserts Current capability status.
