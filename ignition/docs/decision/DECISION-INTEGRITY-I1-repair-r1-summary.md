# DECISION-INTEGRITY-I1 Repair-R1 — Freeze Summary (R4)

> Builder-only. Repository-governance candidate only; claim ceiling enforced.

## Task identity

| field | value |
| --- | --- |
| task | `DECISION-INTEGRITY-I1-REPAIR-R1` |
| capability | `decision_integrity` |
| original frozen head | `b3f27e4c3d614b95af4b112e3564fcf0e3d9f68e` (original PR #73) |
| direct predecessor | `SYMBOLIC-SPHERE-I1` → repair branch `repair/symbolic-sphere-r1-reference-integrity` |
| repair branch | `repair/decision-integrity-r1-principle-process-binding` |
| repair tag | `archive/decision-integrity-repair-r1-frozen-head` |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Root cause

The pilot bundle declared `artifact_digest` values for two evidence artifacts that
did not match the real file bytes. Real CLI reproduced the original failure:

```
python tools/decision/validate_decision_integrity_gate.py --bundle data/decision/pilot-decision-integrity-i1.json
=> {"exit_code":4,"exit_name":"EVIDENCE_BINDING_INVALID",
    "errors":["evidence.1: digest mismatch","evidence.2: digest mismatch"]}
```

Minimal reproduction preserved at `data/decision/repro/original-evidence-binding-failure.json`.

## R0–R4

| step | commit | what |
| --- | --- | --- |
| R0 | `694e3a4e` | Reproduced original failure via real CLI; wrote repair architecture/boundary doc |
| R1 | `4706eb96` | Bound every evidence object to real Git objects (`repository_relative_path`,`commit_sha`,`blob_sha`,`sha256`,`record_type`,`declared_role`); relaxed schema; added fail-closed Git-object pre-check to the validator |
| R2 | `4749be90` | Fail-closed regression runner (decision capability + SYMBOLIC-SPHERE predecessor) |
| R3 | `26b89c31` | Propagation-closure verification (`closure_complete=true`, `residue=0`, canonical hash recomputed); seal bound to R1 repair branch |
| R3-fix | `d32852c8` | Corrected closure-completeness key in verification |
| R4 | this commit | Freeze + publish (tag, Draft PR, 1111 receipt) |

## Evidence grounding (real Git objects, commit `315c7a44560949ca3ca09784d2e3bb12cab623d8`)

| evidence_id | repository_relative_path | blob_sha | sha256 |
| --- | --- | --- | --- |
| evidence.1 | `data/failure/pilot-q39-failure-lineage.json` | `7cd19ee0dd6c0da1c47da895e9021b2e09e12ca4` | `sha256:ca11da2279caac2b99e783b1cdebeb3ca362536986b0f1c8ee78ba2c9f2bd805` |
| evidence.2 | `data/symbolic/pilot-symbolic-sphere-i1.json` | `9499156b69c4b5363e2fd7a44c20709f21caef88` | `sha256:9b30b04109215787bc38ca332dc4c9b112be6edb3d0ecbedf75d82d021405d29` |
| evidence.3 | `FOUNDATION.md` | `c084b5300c1f6a4eeac3fd08cd764c1d12f0ec2f` | `sha256:5fd6618adcdb8aad0643cea3e94bde049c634b85d26131e521b02f54df07b1aa` |

`blob_sha`/`sha256` are recomputed from real Git objects by the validator's
fail-closed pre-check; any mismatch fails `EVIDENCE_BINDING_INVALID`.

## Test / residue summary

- Decision capability gate: **4/4** pass (pilot exit 0; 24-fixture fail-closed matrix each returns its distinct exit code).
- SYMBOLIC-SPHERE predecessor regression: **6/6** pass (no regression).
- R3 propagation closure: `closure_complete=true`, `residue=[]`, canonical `closure_hash=f23b35907a9b13e68b6ee383e315e379fc6c95351ef18bf217362bcd6568ce1c` recomputed and matched.
- Inherited baseline debt (SYMBOLIC-SPHERE) not disguised as new green; repair scope limited to evidence-binding integrity.

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PR #73 untouched.

## Publish

- Annotated repair tag `archive/decision-integrity-repair-r1-frozen-head` → this commit.
- Independent Draft PR (base = `repair/symbolic-sphere-r1-reference-integrity`).
- 1111 receipt `agent-results/remaining-repair-train/DECISION-INTEGRITY-I1-receipt.{json,md}` + total repair index.
