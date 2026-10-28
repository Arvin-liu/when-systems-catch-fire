# F15-D1-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `F15-D1-I1-REPAIR-R1` |
| capability | `latent_system_identifiability` |
| original frozen head | `8db9e5abeaa32ffa73eb778bfbd5574a2aefe301` (original PR #76) |
| direct predecessor | `Q41-I1` → repair branch `repair/q41-r1-anomaly-evidence-binding` (head `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`) |
| repair branch | `repair/f15-d1-r1-latent-system-identifiability` |
| repair tag | `archive/f15-d1-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The latent-system-identifiability gate previously bound evidence only to the
**mutable working tree** (`artifact_digest` recomputed from `path.read_text()`)
and merely regex-checked `exact_head` format. It never verified that
`exact_head`/`commit_sha` resolves to a real Git object, nor that the artifact
bytes at that commit match the claimed `blob_sha`/`sha256`. This allowed an
evidence record to claim a commit while the bytes were unverifiable. Real CLI
reproduced it (post-retarget the repro's `exact_head` was aligned to the
repair predecessor head `da9c4e2a…` so the gap — not a parent-binding check —
is what surfaces):

```
python tools/latent/validate_latent_system_identifiability_gate.py \
  --bundle data/latent/repro/original-evidence-binding-failure.json
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
| merge (propagation) | `a6258a1f6ed45b613f4f71dedb39d38530a100c6` | `--no-ff` merge of direct predecessor repair head `repair/q41-r1-anomaly-evidence-binding` (`da9c4e2a…`) into the original frozen head `8db9e5ab…` |
| R0 | `0370ead61bedd6391d04768dd2ab8f6d7fafc05` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc (repro `exact_head` realigned to `da9c4e2a…` in R4 so the gap demonstration stays coherent post-retarget) |
| R1 | `e21de5e7705cfd53729d43f2584852b548465044` | Bound every evidence object to real Git objects (`repository_relative_path`,`commit_sha`,`blob_sha`,`sha256`); relaxed `evidence` schema (`additionalProperties:true`); retargeted predecessor repair head `d09bd6fe…`→`da9c4e2a…` |
| R2 | `54962bf7aa51b0a0be7cdd3e8f03557050390afa` | 24 verified fixtures (all exit codes, incl. new Git-object fail-closed modes) + `test_git_object_binding_is_enforced` + `test_q41_predecessor_regression` |
| R3 | `698ad67fa05985100290ccf17a0a1d856c1d0894` | Manifest/seal/propagation synchronized to this repair branch (PR #93); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/anomaly/pilot-q41-i1.json` | `d33a874054916918f12236026f1aa453c99c0da4` | `sha256:e8cb6af4451a19a0f61d90b10e94c978cde4e030bde39466c9894bb1bf492bc7` |
| evidence.2 | `data/metacognition/pilot-scientific-metacognition-i1.json` | `8f04b972ad6be64ad8a71660b54c2e2669565c56` | `sha256:a6ec0da30eaa114e052670878c2dd2f006cfa53e9edb223ccacd7f97ba99cda4` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4).
All three `blob_sha` values resolve to real Git objects at `da9c4e2a…` and the
`sha256` of the real Git bytes matches the claimed values exactly (verified).

## Test / residue summary

- Latent-system-identifiability gate: **6/6** pytest pass (pilot exit 0; 24-fixture fail-closed matrix each returns its declared exit code: 0,2,3,4,5–14,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable `commit:path`, unknown ref → exit 4 (proved by `test_git_object_binding_is_enforced`).
- `Q41` repair predecessor regression: **PASS** (Q41 pilot through Q41 validator → exit 0) — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical `closure_hash=84d658f88fb4f66b87a96ca46e67a27b4f13caea93e9c68f44a34fe8fdbd00e2` recomputed by `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (`implementation_consistency` PASS, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (repository-local human front-door consistency).
- Production-execution-authority: not claimed. Claim ceiling = `candidate_only_repository_governance`; no external-action, L7, or truth-layer upgrade (gate would return `EXTERNAL_ACTION_FORBIDDEN`, exit 21).
- Inherited baseline debt (Q41 → SCIENTIFIC-METACOGNITION → DECISION-INTEGRITY chain) not disguised as new green; repair scope limited to evidence→Git-object binding integrity. F15-D1 remains a Draft candidate (unreviewed/unready/unmerged/not Current).

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #76 untouched.

## Publish

- Annotated repair tag `archive/f15-d1-repair-r1-frozen-head` → this commit.
- Independent Draft PR #93 (base = `repair/q41-r1-anomaly-evidence-binding`).
- 1111 receipt `agent-results/remaining-repair-train/F15-D1-I1-receipt.{json,md}` + total repair index.
