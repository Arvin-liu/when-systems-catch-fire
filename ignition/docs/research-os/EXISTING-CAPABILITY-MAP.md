# Existing Capability Map — Pointfire Research Executive OS (Checkpoint A)

This document audits the capabilities that already exist in
`Arvin-liu/when-systems-catch-fire` (formal repository, baseline `cac043d4`)
before the Research OS candidate is built. Its purpose is to prove that the
Research OS **integrates with**, rather than duplicates, the existing system.

Scope of audit (authoritative sources read at baseline):

- `ARCHITECTURE.md` — L0–L6, language–thought logic plane, Q12/Q13/Q14 overlays
- `docs/PROJECT-ARCHITECTURE.md` — compatible entry summary
- `schemas/architecture/iteration-delta.schema.json` — Q13 IterationDelta contract
- `function-os-candidate/v0.1/MANIFEST.md` — Function OS executor candidate

## 1. Existing capability inventory

### 1.1 L0–L6 research layers (the truth-bearing spine)

| Layer | Role | State held |
|-------|------|-----------|
| L0 | Source & evidence | Provenance, source identities, access levels |
| L1 | Controlled semantic propositions | Disambiguated claim language |
| L2 | Formal objects | Constructs, outcomes, denominators |
| L3 | Logical argument | Argument structure |
| L4 | Mathematical model & proof | Models, recomputation targets |
| L5 | Validation & validity | Verification, validity checks |
| L6 | Interpretation, application, publication | Output, **claim ceiling bound** |

Key boundary already enforced by the architecture: **L6 may only point back; it
cannot manufacture truth. There is no L7.** The Research OS must respect this and
must not introduce a covert L7.

### 1.2 Foundation

Anchors truth and prevents uncontrolled drift. The Research OS is a controller,
not a Foundation replacement.

### 1.3 Function OS (executor)

Candidate (`function-os-candidate/v0.1`) defines execution nodes N1–N9
(parse / compile / interpret / package / feedback / cross-node / provenance /
registry). Constraints: Python 3.10+ stdlib only, no `eval`/`exec`/shell/
network/fs I/O (except the trace archiver), JSON file storage, append-only
registry, SHA-256 content integrity. **Function OS executes actions; it does not
decide whether an action is worth doing.** This is the natural executor target
for Research OS dispatch.

### 1.4 Q12 — effectual action plane + mechanism adjudication

- Effectual action plane: reversible, affordable-loss state-changing actions.
- Mechanism adjudication plane: M0 (pre-action sketch) / M1 (post-action
  adjudication).
- Charter Gate: decides whether an action may be done at all.

Research OS **must route every state-changing dispatch through Charter Gate** and
record M0/M1. It does not re-implement Q12.

### 1.5 Q13 — attention / distribution / compression controls

- `IterationDelta` schema (`delta_status` × `required_response`) — the canonical
  information-gain signal.
- Attractor audit / `SampleEnvelope` / `HypothesisDistribution` / `DecisionCollapseRecord`.
- `ChunkAudit` compression-integrity gate.

Research OS integrates Q13 by reading `IterationDelta` to decide
continue / stop / branch / downgrade, and by honoring attractor-loop and
no-information-gain stops. It does not re-implement Q13.

### 1.6 language–thought logic plane

An orthogonal control plane across L0–L6 with a finite twelve-dimensional basis.
Used for bounded multilingual source transformation (Japanese / Turkish pilots).
Research OS uses it only as an adapter for source-language normalization; it is
not a reasoning substitute.

### 1.7 Q14 — ignition map atlas

Versioned map projection and navigation; not a permanent single total map.
Research OS references the current system/component map for topology registration
but does not own the map.

### 1.8 Validation & publication layer

Existing gates decide what may enter the research-output layer. Research OS emits
only a candidate packet; publication remains gated by the existing layer and the
claim-ceiling constraint.

## 2. Non-duplication adjudication

For every Research OS function, the table states the **existing owner** and the
**integration rule**. "Integrate" means call through an adapter; "Do not
duplicate" means do not re-name or re-define the existing component.

| Research OS function | Existing owner | Verdict | Integration rule |
|----------------------|----------------|---------|------------------|
| Hold source / evidence state | L0 | Integrate | Read/write through L0 adapters; never redefine L0 |
| Hold claim / proposition state | L1–L3 | Integrate | Reference claim ids; no new claim language |
| Hold constructs / denominators | L2 | Integrate | Use L2 object ids in obligation graph |
| Recompute / reproduce | L4 + Function OS | Integrate | Dispatch `RECOMPUTE_RESULT` to Function OS node |
| Validation / validity | L5 | Integrate | Record L5 verdicts as obligation evidence |
| Publication packet | L6 + pub layer | Integrate | Emit candidate only; claim ceiling enforced by L6 |
| Execute search/read/compute/write | Function OS | Integrate | Executor Adapter Contract → Function OS nodes |
| Gate state-changing actions | Charter Gate (Q12) | Integrate | Every dispatch passes Charter Gate |
| Pre/post action sketch & adjudication | Q12 M0/M1 | Integrate | Record M0 before, M1 after dispatch |
| Information-gain / stop signal | Q13 IterationDelta | Integrate | Diagnosis consumes IterationDelta |
| Attractor / no-gain stop | Q13 attractor audit | Integrate | `NO_INFORMATION_GAIN` / `ATTRACTOR_LOOP_RISK` map to Q13 |
| Multilingual source normalization | language–thought logic | Integrate | Adapter only; no new logic plane |
| System topology registration | Q14 map atlas | Integrate | Reference current map; no new map ownership |
| Decide research direction / values | GPT/owner | Defer | Escalate; never self-decide |
| Anchor truth / prevent drift | Foundation | Defer | No overlap |

## 3. Conclusion

The seven-layer spine, Foundation, Function OS, Q12 (Charter Gate + M0/M1), Q13
(IterationDelta + attractor controls), language–thought logic and Q14 already
perform truth-bearing, execution, gating, information-gain and mapping duties.
The Research OS adds **one missing capability**: a continuous cross-layer
controller that *observes state, diagnoses gaps, schedules the next action,
dispatches to the existing executor, inspects the return, and decides
continue/branch/stop/escalate* — preserving resumable state. It is additive and
non-duplicative by construction.
