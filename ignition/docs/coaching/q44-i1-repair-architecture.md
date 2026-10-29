# Q44-I1 Repair-R1 Architecture & Boundary (coaching consent binding)

- **Task:** Q44-I1
- **Capability:** `coaching_commitment_subcapability`
- **Repair phase:** R1 (evidence-as-object binding)
- **Predecessor binding:** Q43-I1 → Q44-I1 (direct predecessor repair branch `repair/q43-r1-escalation-authority-binding`)
- **Status:** R0 complete. Reproduction of the original evidence-binding gap captured at `data/coaching/repro/original-evidence-binding-failure.json`.

## 1. Intent

The Q44 capability supports user-declared informed commitments while preserving **autonomy,
consent, multiple narratives, process/outcome separation and revise/pause/stop rights**. R1 hardens
the evidence layer: every evidence record must be pinned to an **immutable Git object**, not merely
to a mutable working-tree digest.

## 2. The distinct concepts

These are deliberately different objects. Confusing them is the core hazard the gate prevents.

### 2.1 User-declared goal
The goal is declared by the user, not inferred, substituted or silently upgraded by the candidate.
- Boundary: goal substitution is false; the candidate never rewrites the user's declared goal.

### 2.2 Informed commitment
Any commitment is made with informed understanding of scope, costs, risks and alternatives.
- Boundary: commitment is informed and non-coerced.

### 2.3 Autonomy & consent
Consent is reversible and belongs to the user; autonomy is preserved at every step.
- Boundary: consent is never irrevocable; the user may withdraw at any time.

### 2.4 Revise / pause / stop
The user retains the right to revise, pause or stop at any checkpoint without penalty.
- Boundary: there is no penalty for stopping; `revise_pause_stop` is always available.

### 2.5 Non-manipulation constraint
No manipulative persuasion, no shame-driven compliance, no hidden goal substitution.
- Boundary: `manipulation_present` is false; multiple narratives are preserved.

### 2.6 Outcome / process separation
A successful outcome does not retroactively legitimate the process; a poor outcome does not
automatically condemn a sound process.
- Boundary: `outcome_proves_process` is false; the result never justifies the intervention.

### 2.7 Escalation boundary
When a request exceeds the candidate's bounded authority, it becomes a **request-only** escalation
to a human with the required authority.
- Boundary: escalation is a request, not an automatic external execution. `is_automatic_external`
  is false.

## 3. Evidence-binding boundary (the R1 fix)

The original gate (`tools/governance/structured_capability_gate.py`) checks a working-tree
`artifact_digest` for every evidence record, but only performs **Git-object integrity** (pinning to
`blob_sha` / `sha256` of an immutable commit) when the evidence record declares **both**
`commit_sha` and `repository_relative_path`. Bundles that omit those fields pass on working-tree
digest alone — which is mutable and therefore not tamper-evident.

**R1 closes this gap** by rebinding every Q44 evidence record to real Git objects at the Q43-I1 R4
frozen head (`5efbce81e96d90d5ebd246891e4762928365d6b8`):

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

- **No manipulative persuasion** is performed by this repository candidate.
- **No hidden goal substitution** is performed by this repository candidate.
- **No shame-driven compliance** is elicited by this repository candidate.
- **Outcome does not prove intervention legitimacy** — a result never justifies the intervention.
- This candidate does **not** establish a universal truth.
- This candidate does **not** establish a causal proof.
- This candidate is **not** deployed to an ecosystem.

## 5. Reproduction evidence (R0)

`data/coaching/repro/original-evidence-binding-failure.json` is a schema-valid Q44 bundle whose
evidence is bound only to the working tree (no `commit_sha` / `repository_relative_path`).
Validated against the original gate:

```
$ python tools/coaching/validate_coaching_commitment_subcapability_gate.py \
    --bundle data/coaching/repro/original-evidence-binding-failure.json
{"boundary": "...", "errors": [], "exit_code": 0, "exit_name": "GATE_PASS", ...}
```

Exit 0 proves the original gate accepts evidence without an immutable Git-object pin — the gap R1
removes.

## 6. R0–R4 plan

- **R0** — reproduce the gap via real CLI; write this architecture/boundary doc.
- **R1** — retarget validator `parent_head` to the Q43-I1 R4 head; rebind pilot `parent_binding`
  and every evidence record to real Git objects; confirm the validated bundle now fails closed on
  any tamper.
- **R2** — regenerate 24 fixtures; add a Git-object tamper test and a Q43 predecessor regression
  test; run the full coaching suite.
- **R3** — propagate closure from the Q43-I1 R4 head (residue 0); sync manifest + seal; create
  Draft PR #97.
- **R4** — freeze this doc; annotated tag `archive/q44-repair-r1-frozen-head`; PR body; 1111
  receipt.
