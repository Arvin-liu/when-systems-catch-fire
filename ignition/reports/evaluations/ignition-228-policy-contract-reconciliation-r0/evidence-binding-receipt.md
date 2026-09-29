# Task228 Task227 evidence-binding receipt

- Owner Packet path: `/tmp/ignition-227-component-isolation-r0/FINAL-OWNER-PACKET/`
- Packet manifest: `SHA256SUMS`; SHA256=`076e4febc3b2f2b801fa3ae9fe20ac52d86aa9e0b64e38227e9f2ae4e4793005`
- Inventory: 100 manifest-listed files; every entry verified; no unlisted or missing files (excluding the manifest file itself).
- Task227 PR: #237; OPEN + DRAFT + UNMERGED; head `7d979b1aa523030b16f773a973477cbfca1e4513`.
- Current exact-head CI: 4/4 success: foundation-validation run 36420663470; repository-path-accounting-preflight run 36420663792; architecture-pages run 36420663646; q33-governance-validation run 36420663752.
- Task227 freeze manifest: `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/freeze/freeze-manifest.json`; SHA256=`91a33c38f209b88644ef473c21a133463bf7839d1bd5afc9c1507b88d128b7ec`.
- Frozen files verified: 52/52; M0/E1 source inputs verified: 6/6.
- The reference-policy validity-lock sidecar verifies the lock JSON.
- Locked human review: 3/6 usable (REF-01, REF-04, REF-05); both raw reviewer sheets and the non-reconciled lock agree.
- Official validator audit: 0/6 pass; all six audit rows say TASK227_POLICY_INVALID and review_scores_modified=false.

## Immutable reference policies

| File | SHA256 | Family | Official exit | Frozen audit first failure |
|---|---|---|---:|---|
| `REF-01.json` | `7d8931b28e01d128573634731068cbf793a295a3800af8416b9fb8e6ef45cb6f` | FAMILY01 | 1 | preserved-rule evidence_refs must reference M0 |
| `REF-02.json` | `223aff4d4cf6dc67804416bd2b33fa297f5688ebda5c6cd44e49de7387c857bb` | FAMILY01 | 1 | evidence IDs must be unique |
| `REF-03.json` | `9e22f44ece3f436f247f89e427a82ea1c7247901e318dc9597c661b5c9a21039` | FAMILY02 | 1 | preserved-rule evidence_refs must reference M0 |
| `REF-04.json` | `043f91bc940f13f8a876ae83877d31f0428bcecbb6f32112ba4b9663d1eb4594` | FAMILY02 | 1 | preserved-rule evidence_refs must reference M0 |
| `REF-05.json` | `613eff7b1da721bf84c96a2b29f2ae5c5ad233dc79248b5a4dad2c9be850f630` | FAMILY03 | 1 | preserved-rule evidence_refs must reference M0 |
| `REF-06.json` | `207841634dc2824cb3a4f4b8c72d58e3d05d82bd917241aa4eff262644fa0022` | FAMILY03 | 1 | unknown provenance link fallback:FALLBACK |

## Locked reviewer and validator records

| File | SHA256 |
|---|---|
| `policy-reviewer-A.json` | `63cd88172c269f7876032edf00db271bc3b54e4274c7a7f61ab86ed19131694e` |
| `policy-reviewer-B.json` | `3e75086c45d7f18891564e62e0969ce0518a2bb67983e66b33e221a96d4f11bd` |
| `reference-policy-validity-lock.json` | `554e74ac9d48828fc997f542dc695d90a8ac02132c491c290c93b404181704a5` |
| `reference-policy-validity-lock.sha256` | `04d1edec2f66b3f6240681fbad790a9f3bc81d51ae106109bffd1b591fd45b7f` |
| `post-review-official-validator-audit.csv` | `8b8dd92cec0282228a0669a8acff2251a25fe00d1d2b21887b1bc081c1d19611` |

## Exact Task227 contract source paths and hashes

| Source | Path | SHA256 |
|---|---|---|
| Task227 protocol | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/design/protocol.md` | `c0e0a4306ba6120d611493f8c53e5523465ed36582a2bf8a7ce2eeb5eace3ba4` |
| policy schema | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/reference/policy-schema.json` | `65995a0ea424ed7103db862c36d678a59efa95546f2d55fdb6f0c13997776dc6` |
| official validator | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/tools/validate_policy.py` | `97825e5d8640fe931578cfb4448e453674de3a68cb9001fce2d4ce5ef89623bc` |
| reviewer criteria | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/reference/reviewer-criteria.md` | `70add38bbaf6c8ee76259a5429ceeb3cb517d3dfcf3dfa385892825d5f72056e` |
| validity criteria | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/reference/validity-criteria.md` | `df4a9f4f1dff2749dd71ac42afbbd35b0facb6dc838bb2823cc9f64381c81b5d` |
| builder prompt | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/reference/builder-prompt.md` | `53c1416c265b88756c0bf78d43d2226d4ed29ee557e3e1ff1fa5071476187655` |
| revision prompt | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/revision/prompt.md` | `39bfd92f36fca6373e02eecc64d41d09bfd2ce5eec4c097e00997c09d09f32d9` |
| revision evaluator criteria | `ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/revision/evaluator/criteria.md` | `79936855885f300d185e0306ce18e0bc21f35f67a36240c8b87f5c8e80e1c61f` |

No Task227 policy, reviewer sheet, lock, aggregate, result, target, or validator source was modified. The Task228 diagnostic read only the six raw reference policies, the frozen schema/validator, and frozen family M0/E1 inputs; it did not read A/B/C target files.
