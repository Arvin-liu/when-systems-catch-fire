# Q43-I1 Repair-R1 Architecture & Boundary (escalation authority binding)

- **Task:** Q43-I1
- **Capability:** `graded_intervention_escalation`
- **Repair phase:** R1 (evidence-as-object binding)
- **Predecessor binding:** Q42-I1 → Q43-I1 (direct predecessor repair branch `repair/q42-r1-counterfactual-ledger-binding`)
- **Status:** R0 complete. Reproduction of the original evidence-binding gap captured at `data/escalation/repro/original-evidence-binding-failure.json`.

## 1. Intent

The Q43 capability grades interventions by risk, reversibility, evidence grade, authority and
expertise so that **only repository-local reversible actions are automatic**, and any
**high-risk external action is converted into a request-only escalation** to a human with the
required authority. R1 hardens the evidence layer: every evidence record must be pinned to an
**immutable Git object**, not merely to a mutable working-tree digest.

## 2. The distinct concepts

These are deliberately different objects. Confusing them is the core hazard the gate prevents.

### 2.1 Action risk class
A graded classification of an action's potential harm if it goes wrong (e.g.
`REPOSITORY_LOCAL_REVERSIBLE` vs `HIGH_RISK_EXTERNAL`).
- Boundary: each action receives exactly one bounded risk class; the class is recorded, not assumed.

### 2.2 Reversibility
Whether an action can be undone without external side effects. Reversible actions may be automatic
repository-local; irreversible ones require confirmation or escalation.
- Boundary: reversibility is graded and recorded; an irreversible action is never silently made automatic.

### 2.3 Authority
The bounded authority level under which an action may be taken (repository candidate, expert,
institutional). Authority is **never self-upgraded** by the candidate.
- Boundary: the candidate operates only within `REPOSITORY_CANDIDATE_ONLY`; expert/institutional
  authority is requested, never assumed.

### 2.4 Escalation
The path an action takes when it exceeds the candidate's bounded authority: it becomes a
**request-only** escalation to a human expert or institution.
- Boundary: escalation is a request, not an automatic external execution. `is_automatic_external`
  is false.

## 3. Evidence-binding boundary (the R1 fix)

The original gate (`tools/governance/structured_capability_gate.py`) checks a working-tree
`artifact_digest` for every evidence record, but only performs **Git-object integrity** (pinning to
`blob_sha` / `sha256` of an immutable commit) when the evidence record declares **both**
`commit_sha` and `repository_relative_path`. Bundles that omit those fields pass on working-tree
digest alone — which is mutable and therefore not tamper-evident.

**R1 closes this gap** by rebinding every Q43 evidence record to real Git objects at the Q42-I1 R4
frozen head (`2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98`):

- `commit_sha` — the frozen predecessor commit the evidence is pinned to.
- `repository_relative_path` — the path of the artifact inside that commit.
- `blob_sha` — `git rev-parse {commit}:{rel}` (must match).
- `sha256` — `sha256` of `git show {commit}:{rel}` bytes (must match).
- `record_type` / `declared_role` — semantic role of the artifact.
- `artifact_digest` — kept equal to the working-tree `sha256:` digest (the gate checks both; any
  mismatch fails closed).

The shared engine is fail-closed: if a record declares both `commit_sha` and
`repository_relative_path`, it MUST resolve to a real Git object whose `blob_sha` and `sha256`
match, or the gate returns `EVIDENCE_BINDING_INVALID` (exit 4).

## 4. Explicit non-claims

The following are **not** asserted by this candidate repair:

- **No legal action** is performed by this repository candidate.
- **No medical action** is performed by this repository candidate.
- **No financial action** is performed by this repository candidate.
- **No safety-critical external action** is performed by this repository candidate.
- This candidate does **not** establish a universal truth.
- This candidate does **not** establish a causal proof.
- This candidate is **not** deployed to an ecosystem.

## 5. Reproduction evidence (R0)

`data/escalation/repro/original-evidence-binding-failure.json` is a schema-valid Q43 bundle whose
evidence is bound only to the working tree (no `commit_sha` / `repository_relative_path`).
Validated against the original gate:

```
$ python tools/escalation/validate_graded_intervention_escalation_gate.py \
    --bundle data/escalation/repro/original-evidence-binding-failure.json
{"boundary": "...", "errors": [], "exit_code": 0, "exit_name": "GATE_PASS", ...}
```

Exit 0 proves the original gate accepts evidence without an immutable Git-object pin — the gap R1
removes.

## 6. R0–R4 plan

- **R0** — reproduce the gap via real CLI; write this architecture/boundary doc.
- **R1** — retarget validator `parent_head` to the Q42-I1 R4 head; rebind pilot `parent_binding`
  and every evidence record to real Git objects; confirm the validated bundle now fails closed on
  any tamper.
- **R2** — regenerate 24 fixtures; add a Git-object tamper test and a Q42 predecessor regression
  test; run the full escalation suite.
- **R3** — propagate closure from the Q42-I1 R4 head (residue 0); sync manifest + seal; create
  Draft PR #96.
- **R4** — freeze this doc; annotated tag `archive/q43-repair-r1-frozen-head`; PR body; 1111
  receipt.
