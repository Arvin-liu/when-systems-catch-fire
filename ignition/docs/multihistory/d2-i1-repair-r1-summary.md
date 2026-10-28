# D2-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `D2-I1-REPAIR-R1` |
| capability | `multi_history_world_projection` |
| original frozen head | `8db9e5abeaa32ffa73eb778bfbd5574a2aefe301` (original PR #77) |
| direct predecessor | `F15-D1-I1` → repair branch `repair/f15-d1-r1-latent-system-identifiability` (head `f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09`) |
| repair branch | `repair/d2-r1-multi-history-world-projection` |
| repair tag | `archive/d2-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The multi-history world-projection gate previously bound evidence only to the
**mutable working tree** (`artifact_digest` recomputed from `path.read_text()`)
and merely regex-checked `exact_head` format. It never verified that
`exact_head`/`commit_sha` resolves to a real Git object, nor that the artifact
bytes at that commit match the claimed `blob_sha`/`sha256`. This allowed an
evidence record to claim a commit while the bytes were unverifiable. Real CLI
reproduced it (post-retarget the repro's `exact_head` was aligned to the
repair predecessor head `f0f7d7ff…` so the gap — not a parent-binding check —
is what surfaces):

```
python tools/multihistory/validate_multi_history_world_projection_gate.py \
  --bundle data/multihistory/repro/original-evidence-binding-failure.json
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
| merge (propagation) | `f607e28fd1336e6cc1b6b6088217bb6c61d0a651` | `--no-ff` merge of direct predecessor repair head `repair/f15-d1-r1-latent-system-identifiability` (`f0f7d7ff…`) into the original frozen head `8db9e5ab…` |
| R0 | `bf3adda41bc8507593790d555676c54aa78fdcbf` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc (repro `exact_head` realigned to `f0f7d7ff…` in R4 so the gap demonstration stays coherent post-retarget) |
| R1 | `221159064ebf0d49111e8d271c6cf6fe8e277d9d` | Bound every evidence object to real Git objects (`repository_relative_path`,`commit_sha`,`blob_sha`,`sha256`); relaxed `evidence` schema (`additionalProperties:true`); retargeted predecessor repair head `8db9e5ab…`→`f0f7d7ff…` |
| R2 | `8aa561e51c6a2c0af585995388ee40589eb70508` | 24 verified fixtures (all exit codes, incl. new Git-object fail-closed modes) + `test_git_object_binding_is_enforced` + `test_f15_d1_predecessor_regression` |
| R3 | `3cbe8ebf41d97945305a049f7ff2216c55dd63b8` | Manifest/seal/propagation synchronized to this repair branch (PR #94); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/latent/pilot-f15-d1-i1.json` | `fb60cc2b57489e8333f7dd60b87b37dedb4a801d` | `sha256:ea201b3f07d64afc1fa812dde8121910eb961be8f1338771a80293bacb5995e5` |
| evidence.2 | `data/anomaly/pilot-q41-i1.json` | `d33a874054916918f12236026f1aa453c99c0da4` | `sha256:e8cb6af4451a19a0f61d90b10e94c978cde4e030bde39466c9894bb1bf492bc7` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4).
All three `blob_sha` values resolve to real Git objects at `f0f7d7ff…` and the
`sha256` of the real Git bytes matches the claimed values exactly (verified).

## Test / residue summary

- Multi-history world-projection gate: **6/6** pytest pass (pilot exit 0; 24-fixture fail-closed matrix each returns its declared exit code: 0,2,3,4,5–14,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable `commit:path`, unknown ref → exit 4 (proved by `test_git_object_binding_is_enforced`).
- `F15-D1` repair predecessor regression: **PASS** (F15-D1 pilot through F15-D1 validator → exit 0) — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical `closure_hash=060fd2a6642edd03152808a42b9f05f23114577ae7d924fbea43389681d631d1` recomputed by `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (`implementation_consistency` PASS, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (repository-local human front-door consistency).
- Production-execution-authority: not claimed. Claim ceiling = `candidate_only_repository_governance`; no external-action, L7, or truth-layer upgrade (gate would return `EXTERNAL_ACTION_FORBIDDEN`, exit 21).
- Inherited baseline debt (Q41 → SCIENTIFIC-METACOGNITION → DECISION-INTEGRITY → F15-D1 chain) not disguised as new green; repair scope limited to evidence→Git-object binding integrity. D2 remains a Draft candidate (unreviewed/unready/unmerged/not Current).

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #77 untouched.

## Publish

- Annotated repair tag `archive/d2-repair-r1-frozen-head` → this commit.
- Independent Draft PR #94 (base = `repair/f15-d1-r1-latent-system-identifiability`).
- 1111 receipt `agent-results/remaining-repair-train/D2-I1-receipt.{json,md}` + total repair index.
