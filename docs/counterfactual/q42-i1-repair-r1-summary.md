# Q42-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `Q42-I1-REPAIR-R1` |
| capability | `counterfactual_unrealized_path` |
| original frozen head | `98998bb1e3db67230954c1436d8effbcb87027af` (original PR #78) |
| direct predecessor | `D2-I1` → repair branch `repair/d2-r1-multi-history-world-projection` (head `1904628103d8c23133107d501a22e3f17d08221d`) |
| repair branch | `repair/q42-r1-counterfactual-ledger-binding` |
| repair tag | `archive/q42-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The counterfactual / unrealized-path gate previously bound evidence only to the
**mutable working tree** (`artifact_digest` recomputed from `path.read_text()`)
and merely regex-checked `exact_head` format. It never verified that
`exact_head`/`commit_sha` resolves to a real Git object, nor that the artifact
bytes at that commit match the claimed `blob_sha`/`sha256`. This allowed an
evidence record to claim a commit while the bytes were unverifiable. Real CLI
reproduced it (the repro's `parent_binding.exact_head` was aligned to the repair
predecessor head `19046281…` so the gap — not a parent-binding check — is what
surfaces):

```
python tools/counterfactual/validate_counterfactual_unrealized_path_gate.py \
  --bundle data/counterfactual/repro/original-evidence-binding-failure.json
=> GATE_PASS (exit 0)   # working-tree-only binding accepted — the original gap
```

R1 closes the gap with an opt-in, fail-closed Git-object pre-check in the shared
validator: any evidence that carries BOTH `commit_sha` and
`repository_relative_path` is verified against real Git objects; tampering a
`sha256`/`commit_sha`/`blob_sha`, or an unresolvable `commit:path`, fails
closed (`EVIDENCE_BINDING_INVALID`, exit 4).

## R0–R4

| step | commit | what |
| --- | --- | --- |
| merge (propagation) | `0f49eb5b4d602e8045e1cba1a6895dade2316482` | `--no-ff` merge of direct predecessor repair head `repair/d2-r1-multi-history-world-projection` (`19046281…`) into the original frozen head `98998bb1…` |
| R0 | `ab1c603f8fecea671ed4a5894bcffe839d57c27e` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc distinguishing counterfactual / alternative decomposition / unrealized path / speculative narrative; stated explicit non-claims |
| R1 | `5f20f5c93634b1f9c77617aa2bdf965c7505350a` | Bound every evidence object to real Git objects (`commit_sha`,`repository_relative_path`,`blob_sha`,`sha256`); relaxed `evidence` schema (`additionalProperties:true`); retargeted predecessor repair head `f638442a…`→`19046281…` |
| R2 | `ef674121c6ae14a1782d9bd8656d8a03605addf7` | 24 regenerated fixtures; re-bound pilot; added `test_git_object_binding_is_enforced` + `test_d2_predecessor_regression`; full suite 6 tests pass |
| R3 | `e61af92f69da7e01629d993e6e3d1d9a0b7dac9a` | Manifest/seal/propagation synchronized to this repair branch (PR #95); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `1904628103d8c23133107d501a22e3f17d08221d`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/multihistory/pilot-d2-i1.json` | `58700ec5e0b091b4312b2cba3d3384d3805c908e` | `sha256:2acfb4c795ebc3e728c7ac543635564099ffaa39710850f3e980fa21b7582fe4` |
| evidence.2 | `data/latent/pilot-f15-d1-i1.json` | `fb60cc2b57489e8333f7dd60b87b37dedb4a801d` | `sha256:ea201b3f07d64afc1fa812dde8121910eb961be8f1338771a80293bacb5995e5` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4).
All three `blob_sha` values resolve to real Git objects at `19046281…` and the
`sha256` of the real Git bytes matches the claimed values exactly (verified).

## Test / residue summary

- Counterfactual / unrealized-path gate: **6/6** pytest pass (pilot exit 0; 24-fixture fail-closed matrix each returns its declared exit code: 0,2,3,4,5–14,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable `commit:path` → exit 4 (proved by `test_git_object_binding_is_enforced`).
- `D2-I1` repair predecessor regression: **PASS** (pilot binds `19046281…`; wrong parent → exit 3) — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical `closure_hash=4658910053ba3bee41ea413491a1d4daeeebc126d9738d8a0a46298d8c8ed0f3` recomputed by `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (38 checked, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (90 frontend nodes).
- Production-execution-authority: not claimed. Claim ceiling = `candidate_only_repository_governance`; no external-action, L7, or truth-layer upgrade (gate would return `EXTERNAL_ACTION_FORBIDDEN`, exit 21).
- Inherited baseline debt (the Q41→…→D2 chain) not disguised as new green; repair scope limited to evidence→Git-object binding integrity. Q42 remains a Draft candidate (unreviewed/unready/unmerged/not Current).

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #78 untouched.

## Publish

- Annotated repair tag `archive/q42-repair-r1-frozen-head` → this commit.
- Independent Draft PR #95 (base = `repair/d2-r1-multi-history-world-projection`).
- 1111 receipt `agent-results/remaining-repair-train/Q42-I1-receipt.{json,md}` + total repair index.
