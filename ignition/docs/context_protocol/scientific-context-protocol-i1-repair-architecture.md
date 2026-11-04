# SCIENTIFIC-CONTEXT-PROTOCOL-I1 Repair-R1 Architecture & Boundary

**Task:** SCIENTIFIC-CONTEXT-PROTOCOL-I1 · **Phase:** repair-r1 · **Order:** 9/9
**Original candidate:** PR #81 · `agent/scientific-context-protocol-i1-open-research-context` · frozen head `77adc367b560a1e004884fe96b470fa7615e5493`
**Repair branch:** `repair/scientific-context-protocol-r1-context-capability-binding`
**Direct predecessor:** `repair/q44-r1-coaching-consent-binding` (Q44 R4, frozen head `4d15ccaf2e574248c0e224c05716c3af46203a39`)

## 1. Defect (reproduced in R0)

The original `open_scientific_context_protocol` subcapability pilot bound its
evidence only to the **mutable working tree**:

- `evidence_registry[*].exact_head` was a bare 40-hex string checked by regex only.
- `evidence_registry[*].artifact_digest` was compared against `sha256(working-tree text)`.
- No `commit_sha`, `repository_relative_path`, `blob_sha`, or `sha256` of the
  immutable Git object was recorded.

Consequence (proven by `data/context_protocol/repro/original-evidence-binding-failure.json`):
the shared `structured_capability_gate.run()` returns `GATE_PASS` (exit 0) for a
bundle that anchors nothing to an immutable Git object. The working tree can be
rewritten (or a commit force-pushed) without the gate detecting it — the
"evidence" is not tamper-evident.

## 2. Repair shape (R0–R4)

- **R1 — bind to real Git objects (fail-closed).** Relax the schema `evidence`
  `$def` to `additionalProperties: true` so Git-object binding fields validate.
  Retarget the validator `parent_head` from the Q44 *original* head
  (`e603e450…`) to the Q44 **R4** frozen head (`4d15ccaf…`). Bind each evidence
  record to real Git objects at `4d15ccaf…`:
  `commit_sha` + `repository_relative_path` + `blob_sha` + `sha256` +
  `record_type` + `declared_role`. The shared gate's opt-in Git-object check now
  runs: it recomputes `git rev-parse {commit}:{path}=blob_sha` and
  `sha256(git show {commit}:{path})`; any mismatch → `exit 4 EVIDENCE_BINDING_INVALID`.
- **R2 — fixtures + predecessor regression.** Retarget the builder to Q44 R4,
  regenerate the 24 fixtures, re-bind the pilot to Git objects, and add
  `test_git_object_binding_is_enforced` (tamper of blob_sha/sha256/commit_sha →
  exit 4) plus `test_q44_predecessor_regression` (wrong parent `e603e450…` →
  exit 3 `PARENT_BINDING_INVALID`).
- **R3 — propagation closure.** `compute_change_propagation` (era-ref
  `77adc367…`, head-ref R2) writes then `--check` verifies: persisted products
  byte-equal recomputed, `residue=[]`, `closure_complete=true`. Sync the
  iteration manifest + completion seal. Validators PASS
  (`validate_iteration_sync`, `validate_human_front_door`).
- **R4 — freeze.** Freeze doc, annotated tag
  `archive/scientific-context-protocol-repair-r1-frozen-head`, independent Draft
  PR #98 (base = direct predecessor `repair/q44-r1-coaching-consent-binding`).

## 3. Subcapability semantics (must hold)

`open_scientific_context_protocol` is repository-local and exchanges
**negotiated, bound scientific context**:

- **capability negotiation** — request/response envelope negotiates supported
  fields and the exact_head each artifact is bound to.
- **identity authorization** — the executor identity is authorized only for
  repository-local, reversible, mock protocol exchange.
- **capability-not-authority** — the ability to exchange context is never
  conflated with authority to act in the world.
- **artifact binding** — every exchanged artifact carries `exact_head`
  provenance verifiable against an immutable Git object.
- **failure/retry** — failures are typed and retries bounded/explicit.
- **compatibility fail-closed** — on incompatible version or unverifiable
  artifact, the exchange fails closed (no silent downgrade).
- **sensitive-local-first** — sensitive data stays repository/network-local; no
  boundary bypass.
- **hardware-request-only** — hardware access is request-only; the protocol
  records a request and a result placeholder, **never executes hardware**.
- **no-ecosystem-overclaim** — no deployed ecosystem, no platform model copying.

## 4. Hard boundaries (builder-only)

This is a candidate-only repository governance repair. No external action,
hardware execution, real-world authority, L7, truth-layer, or universal-causal
upgrade is claimed. The branch is not merged, not marked Current, and the
original PR #81 is neither retargeted nor closed. Awaiting independent re-review.
