# Q43-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `Q43-I1-REPAIR-R1` |
| capability | `graded_intervention_escalation` |
| original frozen head | `3756cd6453135a333771243ffa6eb3d4f86344a0` (original PR #79) |
| direct predecessor | `Q42-I1` → repair branch `repair/q42-r1-counterfactual-ledger-binding` (head `2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98`) |
| repair branch | `repair/q43-r1-escalation-authority-binding` |
| repair tag | `archive/q43-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The graded-intervention / escalation gate previously bound evidence only to the **mutable working
tree** (`artifact_digest` recomputed from `path.read_text()`) and merely regex-checked `exact_head`
format. It never verified that `exact_head`/`commit_sha` resolves to a real Git object, nor that the
artifact bytes at that commit match the claimed `blob_sha`/`sha256`. This allowed an evidence record
to claim a commit while the bytes were unverifiable. Real CLI reproduced it (the repro's
`parent_binding.exact_head` was aligned to the repair predecessor head `2f7777b2…` so the gap — not
a parent-binding check — is what surfaces):

```
python tools/escalation/validate_graded_intervention_escalation_gate.py \
  --bundle data/escalation/repro/original-evidence-binding-failure.json
=> GATE_PASS (exit 0)   # working-tree-only binding accepted — the original gap
```

R1 closes the gap with an opt-in, fail-closed Git-object pre-check in the shared validator: any
evidence that carries BOTH `commit_sha` and `repository_relative_path` is verified against real Git
objects; tampering a `sha256`/`commit_sha`/`blob_sha`, or an unresolvable `commit:path`, fails
closed (`EVIDENCE_BINDING_INVALID`, exit 4).

## R0–R4

| step | commit | what |
| --- | --- | --- |
| merge (propagation) | `ae062961d340a16eac55a005cca74f6ae864fe4f` | `--no-ff` merge of direct predecessor repair head `repair/q42-r1-counterfactual-ledger-binding` (`2f7777b2…`) into the original frozen head `3756cd64…` |
| R0 | `684bbde2ff6e99dc5e9e4f8df2ac015694a6e184` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc distinguishing action-risk-class / reversibility / authority / escalation; stated explicit non-claims (no legal/medical/financial/safety-critical external action) |
| R1 | `8b7daa1c27b33496c33359b1f2813e75da0185a7` | Bound every evidence object to real Git objects (`commit_sha`,`repository_relative_path`,`blob_sha`,`sha256`); relaxed `evidence` schema (`additionalProperties:true`); retargeted predecessor repair head `98998bb1…`→`2f7777b2…` |
| R2 | `bfba5c2a830c0f28f9a0300b71d2f6c5e2026ba1` | 24 regenerated fixtures; re-bound pilot; added `test_git_object_binding_is_enforced` + `test_q42_predecessor_regression`; full suite 6 tests pass |
| R3 | `7e170d0fb5d8ca21e513be6760e3fbd11582fd19` | Manifest/seal/propagation synchronized to this repair branch (PR #96); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `2f7777b26e1d52c5e6fff44fbf3d079cb38bdb98`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/counterfactual/pilot-q42-i1.json` | `0f7ed384778f5237a36836578b437ef72f274e2d` | `sha256:d265486dec7ca48886460cdc6d0542c9d29025e3c44b35530e0b0c5ef997fdf0` |
| evidence.2 | `data/intervention/pilot-controlled-intervention.json` | `222e4530d82f6334167f5fa5961a27aa5ac76480` | `sha256:12de83b566ca379fcf857e475e8c6f8e8c3ece39039fb219f85205a5223e504d` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's fail-closed pre-check;
any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4). All three `blob_sha` values resolve to real
Git objects at `2f7777b2…` and the `sha256` of the real Git bytes matches the claimed values exactly
(verified).

## Test / residue summary

- Graded-intervention / escalation gate: **6/6** pytest pass (pilot exit 0; 24-fixture fail-closed
  matrix each returns its declared exit code: 0,2,3,4,5–14,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable `commit:path` → exit
  4 (proved by `test_git_object_binding_is_enforced`).
- `Q42-I1` repair predecessor regression: **PASS** (pilot binds `2f7777b2…`; wrong parent → exit 3)
  — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical
  `closure_hash=28fa03aea06fd294a7018d49ac07c864e2f53306362b0376de6550e4d6be24b3` recomputed by
  `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (39 checked, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (93 frontend nodes).
- Production-execution-authority: not claimed. Claim ceiling = `candidate_only_repository_governance`;
  no external-action, L7, or truth-layer upgrade (gate would return `EXTERNAL_ACTION_FORBIDDEN`, exit
  21). High-risk external actions are request-only escalations, never executed.
- Inherited baseline debt (the Q41→…→D2 chain, and q33 governance validation) not disguised as new
  green; repair scope limited to evidence→Git-object binding integrity. Q43 remains a Draft candidate
  (unreviewed/unready/unmerged/not Current).

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer upgrade, no
real-world universal causal claim. Builder-only: not self-reviewed, not Ready/merged, Main
untouched, original PR #79 untouched.

## Publish

- Annotated repair tag `archive/q43-repair-r1-frozen-head` → this commit.
- Independent Draft PR #96 (base = `repair/q42-r1-counterfactual-ledger-binding`).
- 1111 receipt `agent-results/remaining-repair-train/Q43-I1-receipt.{json,md}` + total repair index.
