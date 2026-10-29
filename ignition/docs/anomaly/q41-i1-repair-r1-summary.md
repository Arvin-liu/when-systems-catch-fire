# Q41-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `Q41-I1-REPAIR-R1` |
| capability | `world_feedback_anomaly` |
| original frozen head | `d09bd6fe964d8879e1b5027aa28cb2e010363c05` (original PR #75) |
| direct predecessor | `SCIENTIFIC-METACOGNITION-I1` → repair branch `repair/scientific-metacognition-r1-epistemic-state-binding` (head `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3`) |
| repair branch | `repair/q41-r1-anomaly-evidence-binding` |
| repair tag | `archive/q41-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The world-feedback anomaly gate previously bound evidence only to the
**mutable working tree** (`artifact_digest` recomputed from `path.read_text()`)
and merely regex-checked `exact_head` format. It never verified that
`exact_head`/`commit_sha` resolves to a real Git object, nor that the artifact
bytes at that commit match the claimed `blob_sha`/`sha256`. This allowed an
evidence record to claim a commit while the bytes were unverifiable. Real CLI
reproduced it (post-retarget the repro's `exact_head` was aligned to the
repair predecessor head `183f4343…` so the gap — not a parent-binding check —
is what surfaces):

```
python tools/anomaly/validate_world_feedback_anomaly_gate.py \
  --bundle data/anomaly/repro/original-evidence-binding-failure.json
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
| merge (propagation) | `31ccf1a2e74a9326c8cbd0925ea0508db6f5dc48` | `--no-ff` merge of direct predecessor repair head `repair/scientific-metacognition-r1-epistemic-state-binding` (`183f4343…`) into the original frozen head `d09bd6fe…` |
| R0 | `6475314337fbeb3ab581fd1ca2315302d723bc1d` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc (repro `exact_head` realigned to `183f4343…` in R4 so the gap demonstration stays coherent post-retarget) |
| R1 | `a493ff7fec341162f92b930ef09265c12680046c` | Bound every evidence object to real Git objects (`repository_relative_path`,`commit_sha`,`blob_sha`,`sha256`,`record_type`,`declared_role`); relaxed `evidence` schema (`additionalProperties:true`); retargeted predecessor repair head `2b18e1f2…`→`183f4343…` |
| R2 | `7ff1517f6b3f9a1a1fc51b7fa14015dc44232e77` | 24 verified fixtures (all exit codes, incl. new Git-object fail-closed modes) + `test_git_object_binding_is_enforced` + `test_scientific_metacognition_predecessor_regression` |
| R3 | `8c56c89db6b0c21d8b1ab2abd57350244e04b447` | Manifest/seal/propagation synchronized to this repair branch (PR #92); closure recomputed by formal tool, `closure_complete=true`, `residue=0` |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/metacognition/pilot-scientific-metacognition-i1.json` | `8f04b972ad6be64ad8a71660b54c2e2669565c56` | `sha256:a6ec0da30eaa114e052670878c2dd2f006cfa53e9edb223ccacd7f97ba99cda4` |
| evidence.2 | `data/failure/pilot-q39-failure-lineage.json` | `7cd19ee0dd6c0da1c47da895e9021b2e09e12ca4` | `sha256:ca11da2279caac2b99e783b1cdebeb3ca362536986b0f1c8ee78ba2c9f2bd805` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID` (exit 4).
All three `blob_sha` values resolve to real Git objects at `183f4343…` and the
`sha256` of the real Git bytes matches the claimed values exactly (verified).

## Test / residue summary

- World-feedback anomaly gate: **6/6** pytest pass (pilot exit 0; 24-fixture fail-closed matrix each returns its declared exit code: 0,2,3,4,5–14,20,21).
- Git-object fail-closed: tamper `sha256`/`commit_sha`/`blob_sha`, unresolvable `commit:path`, unknown ref → exit 4 (proved by `test_git_object_binding_is_enforced`).
- `SCIENTIFIC-METACOGNITION` repair predecessor regression: **PASS** (SM pilot through SM validator → exit 0) — proves the shared opt-in check is non-regressive.
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical `closure_hash=8fd273b455c9d72358845cd8317b5e7affcfb0e70e878b66d1b2b91c1ef66685` recomputed by `compute_change_propagation` and matched.
- `validate_iteration_sync`: PASS (`implementation_consistency` PASS, `repository_synchronization_closure` PASS).
- `validate_human_front_door`: PASS (repository-local human front-door consistency).
- Production-execution-authority: not claimed. Claim ceiling = `candidate_only_repository_governance`; no external-action, L7, or truth-layer upgrade (gate would return `EXTERNAL_ACTION_FORBIDDEN`, exit 21).
- Inherited baseline debt (SCIENTIFIC-METACOGNITION → DECISION-INTEGRITY chain) not disguised as new green; repair scope limited to evidence→Git-object binding integrity. Q41 remains a Draft candidate (unreviewed/unready/unmerged/not Current).

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #75 untouched.

## Publish

- Annotated repair tag `archive/q41-repair-r1-frozen-head` → this commit.
- Independent Draft PR #92 (base = `repair/scientific-metacognition-r1-epistemic-state-binding`).
- 1111 receipt `agent-results/remaining-repair-train/Q41-I1-receipt.{json,md}` + total repair index.
