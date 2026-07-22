# Q42-I1 Repair-R1 Architecture & Boundary (counterfactual ledger binding)

- **Task:** Q42-I1
- **Capability:** `counterfactual_unrealized_path`
- **Repair phase:** R1 (evidence-as-object binding)
- **Predecessor binding:** D2-I1 → Q42-I1 (direct predecessor repair branch `repair/d2-r1-multi-history-world-projection`)
- **Status:** R0 complete. Reproduction of the original evidence-binding gap captured at `data/counterfactual/repro/original-evidence-binding-failure.json`.

## 1. Intent

The Q42 capability keeps four related-but-distinct reasoning artifacts separated so that a
"what-if" statement about an identifiable portion of a system is never silently upgraded into a
causal fact about the whole system. R1 hardens the evidence layer: every evidence record must be
pinned to an **immutable Git object**, not merely to a mutable working-tree digest.

## 2. The four distinct types

These are deliberately different objects. Confusing them is the core hazard the gate prevents.

### 2.1 Counterfactual
A bounded "what-if X had happened instead" statement about an **identifiable** portion of the
observed system. Only the identifiable portion may receive bounded counterfactual status.
- Boundary: it is a contrast against a recorded state; it is not a prediction and not a causal claim.

### 2.2 Alternative decomposition
A different way to **break down the same observed system**. It is a reframing / descriptive
restructuring.
- Boundary: decomposing the system differently does **not** establish what would have happened.
  An alternative decomposition is **not** a counterfactual proof.

### 2.3 Unrealized path
A decision or trajectory that was **not taken**. It is speculative by construction: it was never
realized and cannot be directly observed.
- Boundary: an unrealized path stays speculative; it is never promoted to an observed fact.

### 2.4 Speculative narrative
An if-then story used for reasoning. It is explicitly labeled as speculation.
- Boundary: an if-then narrative is **not** a causal fact. It supports reasoning, not proof.

## 3. Evidence-binding boundary (the R1 fix)

The original gate (`tools/governance/structured_capability_gate.py`) checks a working-tree
`artifact_digest` for every evidence record, but only performs **Git-object integrity** (pinning to
`blob_sha` / `sha256` of an immutable commit) when the evidence record declares **both**
`commit_sha` and `repository_relative_path`. Bundles that omit those fields pass on working-tree
digest alone — which is mutable and therefore not tamper-evident.

**R1 closes this gap** by rebinding every Q42 evidence record to real Git objects at the D2-I1 R4
frozen head (`1904628103d8c23133107d501a22e3f17d08221d`):

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

- An if-then story is **not** a causal fact.
- The unobservable portion **remains unobservable**; it is never promoted.
- An alternative decomposition is **not** a counterfactual proof.
- **No external intervention** is performed by this repository candidate; any external action would
  fall under a different capability boundary and is request-only.

## 5. Reproduction evidence (R0)

`data/counterfactual/repro/original-evidence-binding-failure.json` is a schema-valid Q42 bundle
whose evidence is bound only to the working tree (no `commit_sha` / `repository_relative_path`).
Validated against the original gate:

```
$ python tools/counterfactual/validate_counterfactual_unrealized_path_gate.py \
    --bundle data/counterfactual/repro/original-evidence-binding-failure.json
{"boundary": "...", "errors": [], "exit_code": 0, "exit_name": "GATE_PASS", ...}
```

Exit 0 proves the original gate accepts evidence without an immutable Git-object pin — the gap R1
removes.

## 6. R0–R4 plan

- **R0** — reproduce the gap via real CLI; write this architecture/boundary doc.
- **R1** — retarget validator `parent_head` to the D2-I1 R4 head; rebind pilot `parent_binding` and
  every evidence record to real Git objects; confirm the validated bundle now fails closed on any
  tamper.
- **R2** — regenerate 24 fixtures; add a Git-object tamper test and a D2 predecessor regression test;
  run the full counterfactual suite.
- **R3** — propagate closure from the D2-I1 R4 head (residue 0); sync manifest + seal; create
  Draft PR #95.
- **R4** — freeze this doc; annotated tag `archive/q42-repair-r1-frozen-head`; PR body; 1111 receipt.
