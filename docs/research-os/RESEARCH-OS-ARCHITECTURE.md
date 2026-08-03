# Pointfire Research Executive OS — Architecture (Checkpoint A)

`Pointfire Research Executive OS` / `点火研究执行总控 OS` (short: **Research OS**)
is an active, cross-layer operating system spanning exact **L0–L6**. It is the
continuous controller that the night-shift R1 incident proved was missing: a
system that keeps asking *what is epistemically missing, what is the next
highest-value action, and should we continue, branch, stop or escalate*.

This document is the Checkpoint A architecture. The executable kernel, diagnosis
engine, scheduler and CLI land in Checkpoints B–C. The authoritative contract is
`relay/tasks/115-RESEARCH-EXECUTIVE-OS-DRAFT-PR-R1.md`.

## 1. Identity and hard boundaries

The Research OS is **explicitly and permanently**:

- **not L7** — it adds no truth layer;
- **not a truth authority** — L0–L6 hold truth; L6 may only point back;
- **not an autonomous permission to publish** — publication stays gated by the
  existing validation/publication layer and the claim-ceiling constraint;
- **not a replacement** for Function OS, Q12, Q13, Foundation, Charter Gate,
  language–thought logic or lifecycle governance;
- **not an LLM prompt disguised as architecture** — the deterministic core runs
  without any model; an LLM may only supply *optional candidate* proposals.

## 2. Required relationship (from contract §2)

```text
Research OS: observe → diagnose → choose → dispatch → inspect → update → stop/escalate
Function OS: execute the chosen operation
L0-L6: hold source, claim, object, argument, model, validation and output state
Q12: constrain state-changing actions and mechanism adjudication
Q13: constrain information gain, attractor loops and stopping
GPT/owner: retain research direction, values, exceptional review and formal acceptance
```

## 3. Control loop

```
        +-------------------------------------------------------+
        |                                                       |
        v                                                       |
  OBSERVE (read live episode state + L0-L6)                     |
        |                                                       |
        v                                                       |
  DIAGNOSE (deterministic gap engine over structured state)     |
        |                                                       |
        v                                                       |
  CHOOSE (inspectable scheduler over finite action vocabulary)  |
        |                                                       |
        v                                                       |
  DISPATCH (Executor Adapter Contract -> Function OS / Agent) --+
        |                                                       |
        v                                                       |
  INSPECT (executor return; no self-approval)                   |
        |                                                       |
        v                                                       |
  UPDATE (append-only event log + obligation graph)             |
        |                                                       |
        v                                                       |
  STOP / ESCALATE (review gates, budget, human judgment)        |
```

A report file, word count, elapsed time or round count **never** alone causes a
completion transition. Completion requires satisfied obligations and passed
review gates.

## 4. Core modules (delivered across Checkpoints A–D)

| Module | Contract ref | Checkpoint | Draft artifact (this checkpoint) |
|--------|-------------|-----------|----------------------------------|
| Research Episode State Kernel | §5.1 | B | `schemas/research-os/episode-state.schema.json`, `data/research-os/episode-states.json` |
| Claim & Evidence Obligation Graph | §5.2 | B | `schemas/research-os/obligation-graph.schema.json`, `data/research-os/obligation-classes.json` |
| Epistemic Gap Diagnosis Engine | §5.3 | B | `schemas/research-os/gap-codes.schema.json`, `data/research-os/gap-codes.json` |
| Next-Action Scheduler | §5.4 | B | `schemas/research-os/action-vocabulary.schema.json`, `data/research-os/action-vocabulary.json` |
| Strategy Packs (8) | §5.5 | C | `data/research-os/strategy-packs/` (Checkpoint C) |
| Executor Adapter Contract | §5.6 | B/C | `schemas/research-os/executor-contract.schema.json` (Checkpoint B/C) |
| Review / Stop / Escalation gates | §5.7 | C | `docs/research-os/REVIEW-GATES.md` (Checkpoint C) |

### 4.1 Episode State Kernel (§5.1)

Versioned, resumable episode state with explicit, validated transitions. Minimum
states `INTAKE → QUESTION_FROZEN → EVIDENCE_GATHERING → ANALYSIS → CHALLENGE →
REVISION → CANDIDATE_COMPLETE` plus alternatives `BLOCKED`,
`INSUFFICIENT_EVIDENCE_COMPLETE`, `ESCALATED_TO_GPT_OWNER`, `PAUSED_RESUMABLE`,
`REOPENED`. `CANDIDATE_COMPLETE` is **not** a success terminal.

### 4.2 Obligation Graph (§5.2)

Each material claim carries obligations from 12 classes
(`data/research-os/obligation-classes.json`). Statuses: `OPEN`, `PARTIAL`,
`SATISFIED`, `WAIVED_WITH_REASON`, `BLOCKED_WITH_EVIDENCE`, `NOT_APPLICABLE`. A
waiver can **never** raise a claim ceiling.

### 4.3 Gap Diagnosis Engine (§5.3)

Deterministic diagnosis over structured state. 24 gap codes
(`data/research-os/gap-codes.json`; the contract enumerates 23 minimum and this
registry adds `TIMESTAMP_BATCH_NOT_PROOF_OF_READING`, justified by §7.1 R1
replay). Every finding carries evidence, severity, affected target and candidate
correcting actions. Free-prose regex is **not** the primary capability.

### 4.4 Next-Action Scheduler (§5.4)

Closed, finite vocabulary of 24 actions
(`data/research-os/action-vocabulary.json`). Selection is inspectable and records
prerequisite gaps, expected information gain, discriminating power, cost,
reversibility, dependency ordering, risk multiplier, rejected alternatives and the
observation that would change the next decision. A deterministic baseline
scheduler is mandatory; LLM proposals are optional candidate inputs only.

### 4.5 Strategy Packs (§5.5, Checkpoint C)

Eight bounded packs over the shared kernel — not one OS per discipline:
`QUANTITATIVE_DATA_RECONCILIATION`, `RANDOMIZED_CLINICAL_EVIDENCE`,
`OBSERVATIONAL_CAUSALITY`, `POLICY_EFFECT_EVALUATION`, `ENGINEERING_BENCHMARK`,
`SYSTEMATIC_EVIDENCE_SYNTHESIS`, `HISTORICAL_SOURCE_ADJUDICATION`,
`PUBLIC_CLAIM_FACT_CHECK`. Each declares required obligations, typical gaps,
mandatory calculations/audits, common failure modes, max claim ceilings,
escalation conditions and stop criteria. The eight R1 topics are **not**
hard-coded as the whole architecture.

### 4.6 Executor Adapter Contract (§5.6, Checkpoint B/C)

Tool-agnostic dispatch/return contract so Codex, WorkBuddy, other agents or
scripts can act as executors. OS sends action type, bounded objective, required
inputs/locators, expected output schema, success/failure evidence, prohibited
claims, budget and stop condition. Executor returns observations, exact
source/file/command identities, access level, calculation result, errors,
provenance and timestamps — **with no self-approval**. The OS then diagnoses the
returned state; an executor cannot mark its episode complete by returning
`success`.

### 4.7 Review / Stop / Escalation (§5.7, Checkpoint C)

Separate gates: source/provenance, method/calculation, source-dependence,
adversarial claim, claim-ceiling, high-stakes escalation, owner/GPT acceptance.
Required stop states: sufficient bounded result, reliable null/insufficient
evidence, verifiable source/data blocker, no information gain, budget boundary
with resumable checkpoint, mandatory human escalation.

## 5. Integration adapters (non-duplicative)

| Adapter | Target | Mechanism |
|---------|--------|-----------|
| L0–L6 | truth spine | read/write through layer adapters; reference existing ids |
| Function OS | executor | Executor Adapter Contract → N1–N9 nodes |
| Q12 Charter Gate | action gate | every dispatch passes Charter Gate; M0 before, M1 after |
| Q13 IterationDelta | stop signal | diagnosis consumes IterationDelta; attractor/no-gain stops |
| language–thought logic | source normalization | adapter only (JA/TR pilots) |
| publication claim ceiling | L6 bound | candidate packet respects ceiling |
| Q14 system map | topology | reference current map for component registration |

## 6. Determinism and resumability

- The deterministic core runs **without an LLM**. An LLM may only supply optional
  candidate proposals; it is never the sole scheduler or validator.
- Every state transition and executor return appends an immutable event to the
  episode event log (SHA-256 addressed), making episodes resumable across models,
  sessions and interruptions.

## 7. Phase boundary (reminder)

This Draft-PR phase implements the candidate and opens one Draft PR against
`main`. It does **not** merge, mark ready, terminalize, create `FINAL_STATE`, or
create Task 116. The PR carries the marker `R2_EMPIRICAL_CALIBRATION_PENDING`.
R1 is failure evidence; R2 is a human-authored comparison target, not empirical
proof. A later same-number continuation absorbs R2 results and performs final
adjudication.
