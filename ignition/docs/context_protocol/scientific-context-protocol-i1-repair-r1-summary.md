# SCIENTIFIC-CONTEXT-PROTOCOL-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `SCIENTIFIC-CONTEXT-PROTOCOL-I1-REPAIR-R1` |
| capability | `open_scientific_context_protocol` |
| original frozen head | `77adc367b560a1e004884fe96b470fa7615e5493` (original PR #81) |
| direct predecessor | `Q44-I1` → repair branch `repair/q44-r1-coaching-consent-binding` (head `4d15ccaf2e574248c0e224c05716c3af46203a39`) |
| repair branch | `repair/scientific-context-protocol-r1-context-capability-binding` |
| repair tag | `archive/scientific-context-protocol-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The `open_scientific_context_protocol` subcapability pilot previously bound its
evidence only to the **mutable working tree** (`artifact_digest` recomputed from
`path.read_text()`) and merely regex-checked `exact_head` format. It never
verified that `exact_head`/`commit_sha` resolves to a real Git object, nor that
the artifact bytes at that commit match the claimed `blob_sha`/`sha256`. This
allowed an evidence record to claim a commit while the bytes were unverifiable.
Real CLI reproduced it (the repro's `parent_binding.exact_head` was aligned to
the repair predecessor head `4d15ccaf…` so the gap — not a parent-binding check
— is what surfaces):

```
python tools/context_protocol/validate_open_scientific_context_protocol_gate.py \
  --bundle data/context_protocol/repro/original-evidence-binding-failure.json
=> GATE_PASS (exit 0)   # working-tree-only binding accepted — the original gap
```

R1 closes the gap with an opt-in, fail-closed Git-object pre-check in the shared
validator: any evidence that carries BOTH `commit_sha` and
`repository_relative_path` is verified against real Git objects; tampering a
`sha256`/`commit_sha`/`blob_sha`, or an unresolvable `commit:path`, fails closed
(`EVIDENCE_BINDING_INVALID`, exit 4).

## R0–R4

| step | commit | what |
| --- | --- | --- |
| merge (propagation) | `d1f7cc43d886a664a282e8cc27ae3a5581d7912e` | `--no-ff` merge of direct predecessor repair head `repair/q44-r1-coaching-consent-binding` (`4d15ccaf…`) into the original frozen head `77adc367…` |
| R0 | `423727557268f67ae2a020a91ced8af20b5b4969` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc distinguishing capability negotiation / identity / authority / artifact / failure / retry / version / boundary; stated explicit non-claims (no hardware execution, no external action) |
| R1 | `129fea7b74643b11e15d71beb65a3de9b7df0ddb` | Bound every evidence object to real Git objects (`commit_sha`,`repository_relative_path`,`blob_sha`,`sha256`); relaxed `evidence` schema (`additionalProperties:true`); retargeted predecessor repair head `e603e450…`→`4d15ccaf…` |
| R2 | `350ae81d6f8900bea23aa88e1cc62c79ee1f114c` | 24 regenerated fixtures; re-bound pilot; added `test_git_object_binding_is_enforced` + `test_q44_predecessor_regression`; full suite 6 tests pass |
| R3 | `69b3fceeeee749a5d2824989d516f9199b554d2f` | Manifest/seal/propagation synchronized to this repair branch (PR #98); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `4d15ccaf2e574248c0e224c05716c3af46203a39`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/coaching/pilot-q44-i1.json` | `fce931e1bd839f1eeffdeac990938b2f172f4297` | `sha256:197586b318d7634ab6bda533e48e6a03130c4aea5a8fe2db1eb41a5b1fdcd4a0` |
| evidence.2 | `data/escalation/pilot-q43-i1.json` | `2968536a71c583969de5f1e7bd367afa6c75d405` | `sha256:c2641c1adecd6e86cfe55593288afce8321867468ba1a3ad6c937fb8454adf76` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4).
All three `blob_sha` values resolve to real Git objects at `4d15ccaf…` and the
`sha256` of the real Git bytes matches the claimed values exactly (verified).

## Test / residue summary

- `open_scientific_context_protocol` gate: **6/6** pytest pass (pilot exit 0;
  24-fixture fail-closed matrix each returns its declared exit code:
  0,2,3,4,5–14,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable
  `commit:path` → exit 4 (proved by `test_git_object_binding_is_enforced`).
- `Q44-I1` repair predecessor regression: **PASS** (pilot binds `4d15ccaf…`;
  wrong parent → exit 3) — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical
  `closure_hash=85a4bd113fd15422d2f1759f1dabe40a42420242d8d3c67481c86f574b76815e`
  recomputed by `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (41 checked, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (99 frontend nodes).
- Production-execution-authority / hardware execution: not claimed. Claim ceiling
  = `candidate_only_repository_governance`; no external-action, L7, or
  truth-layer upgrade. The protocol records a hardware **request** and a result
  placeholder — it never executes hardware (gate would return
  `EXTERNAL_ACTION_FORBIDDEN`, exit 21).
- Inherited baseline debt (the Q41→…→D2 chain, and q33 governance validation
  121Q33 era_resolver debt) not disguised as new green; repair scope limited to
  evidence→Git-object binding integrity. SCIENTIFIC-CONTEXT-PROTOCOL-I1 remains a
  Draft candidate (unreviewed/unready/unmerged/not Current).

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #81 untouched.

## Publish

- Annotated repair tag `archive/scientific-context-protocol-repair-r1-frozen-head` → this commit.
- Independent Draft PR #98 (base = `repair/q44-r1-coaching-consent-binding`).
- 1111 receipt `agent-results/remaining-repair-train/SCIENTIFIC-CONTEXT-PROTOCOL-I1-receipt.{json,md}` + total repair index.
