# SCIENTIFIC-METACOGNITION-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `SCIENTIFIC-METACOGNITION-I1-REPAIR-R1` |
| capability | `epistemic_state_control_plane` |
| original frozen head | `2b18e1f2d11511dc758734338e7c715566d01394` (original PR #74) |
| direct predecessor | `DECISION-INTEGRITY-I1` → repair branch `repair/decision-integrity-r1-principle-process-binding` |
| repair branch | `repair/scientific-metacognition-r1-epistemic-state-binding` |
| repair tag | `archive/scientific-metacognition-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The epistemic-state control plane gate previously bound evidence only to the
**mutable working tree** (`artifact_digest` recomputed from `path.read_text()`)
and merely regex-checked `exact_head` format. It never verified that
`exact_head`/`commit_sha` resolves to a real Git object, nor that the artifact
bytes at that commit match the claimed `blob_sha`/`sha256`. This allowed an
evidence record to claim a commit while the bytes were unverifiable (the
original-evidence-binding-failure repro passed the gate). Real CLI reproduced it:

```
python tools/metacognition/validate_epistemic_state_control_plane_gate.py \
  --bundle data/metacognition/repro/original-evidence-binding-failure.json
=> EVIDENCE_BINDING_INVALID (exit 4)
```

## R0–R4

| step | commit | what |
| --- | --- | --- |
| merge (propagation) | `b46a4668cdf154832c899eb4de256e80c2471167` | `--no-ff` merge of direct predecessor repair head `repair/decision-integrity-r1-principle-process-binding` into the original frozen head `2b18e1f2…` |
| R0 | `27649857e3a651b2ea1e0323f0955fc8e6e3482e` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc |
| R1 | `bfff223ab56c900c3aa20c65f96a282fa197e901` | Bound every evidence object to real Git objects (`repository_relative_path`,`commit_sha`,`blob_sha`,`sha256`,`record_type`,`declared_role`); relaxed schema; added opt-in fail-closed Git-object pre-check to the shared validator (`tools/governance/structured_capability_gate.py`) |
| R2 | `59b75db9c4170d2fb655ac8b16c22a07143c78bd` | 24 verified fixtures (all exit codes, incl. new Git-object fail-closed modes) + `test_git_object_binding_is_enforced` + `test_decision_integrity_predecessor_regression` |
| R3 | `f722ff4900fc9e567bb555b88542ea71e49f50cb` | Manifest/seal/propagation synchronized to this repair branch (PR #91); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `27649857e3a651b2ea1e0323f0955fc8e6e3482e`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/failure/pilot-q39-failure-lineage.json` | `7cd19ee0dd6c0da1c47da895e9021b2e09e12ca4` | `sha256:ca11da2279caac2b99e783b1cdebeb3ca362536986b0f1c8ee78ba2c9f2bd805` |
| evidence.2 | `data/decision/pilot-decision-integrity-i1.json` | `31a7c97276698454663b4b9efc893174bdb67127` | `sha256:a5f07e227568ccf48d93df15edef6f24677ae7ac7e9ebce6567e07766c81b281` |
| evidence.3 | `data/retrieval/pilot-q38-repository-evidence-retrieval.json` | `2a0e7841a8093c2c1df208c7e2c358ac67738bfc` | `sha256:ea1cbf363efb5afa534340b09ab706386aea10c7e81a9658a08f306a86bd4778` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4).
Tampering a `sha256`, `commit_sha`, `blob_sha`, or using an unresolvable
`commit:path` all fail closed.

## Test / residue summary

- Epistemic-state control plane gate: **6/6** pytest pass (pilot exit 0; 24-fixture fail-closed matrix each returns its distinct exit code: 2,3,4×7,5–16,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable `commit:path`, unknown ref, duplicate id → exit 4; placeholder/self-rating → exit 4.
- `DECISION-INTEGRITY` repair predecessor regression: **PASS** (pilot + 24 fixtures unchanged) — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical `closure_hash=07d586457d6098f43e6bb62e68bfd842367859249dda192a66a69814ab8444c3` recomputed by `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (`implementation_consistency` PASS, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (repository-local human front-door consistency).
- Inherited baseline debt (DECISION-INTEGRITY chain) not disguised as new green; repair scope limited to evidence→Git-object binding integrity.

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #74 untouched.

## Publish

- Annotated repair tag `archive/scientific-metacognition-repair-r1-frozen-head` → this commit.
- Independent Draft PR #91 (base = `repair/decision-integrity-r1-principle-process-binding`).
- 1111 receipt `agent-results/remaining-repair-train/SCIENTIFIC-METACOGNITION-I1-receipt.{json,md}` + total repair index.
