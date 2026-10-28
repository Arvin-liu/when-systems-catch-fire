# Task157 Junction Invariant vs Local Predicate Competition — 2026-09-06

## Outcome

The frozen verdict is JUNCTION_INVARIANT_SUPPORTED_AS_RESEARCH_CANDIDATE. The experiment used 96 paired fixtures and 192 blind instances across eight families: 48 calibration pairs, 24 in-family holdout pairs, and 24 transfer holdout pairs. Pair members stayed together. The result is research evidence only.

Holdout MJ incremental defects beyond M0: 46; ML: 31. MJ-only holdout defects over ML: 15. MJ holdout control false positives: 0; ML holdout control false positives: 0.

## Frozen provenance and boundary

- Command source: Arvin-liu/1111 agent-commands/IGNITION-20260906-157.md
- Command commit: 6307f30abb92ab02b082476c4b627ccb0bdc6914; blob: dc51ff0524d6d5c43ba149cb7cb5722f48aebcaf; content SHA-256: 621a4aa243a3268d65c88c1960d4690a538bd228964f2fb79df4bef3d206b2a5
- Formal baseline: Arvin-liu/when-systems-catch-fire at ad0e8f3e6c80eee5f27d05bd4b29653b2d936aae, Task156 Draft PR #206 head
- Freeze digest: a877f928440b83c58f3638cd937cba57c8b1e8956902d573fb7dbd36baf5925a
- Blind score-run SHA-256: 4022350ec54078e7d8bb151313f2dc1ab99bb41bb2a942ae2f00c3aaf003a040; unblinded results SHA-256: f8d32fb6e5c054cf3a36dc1ef2fe2fbfef7015e824fc012323e8da6a26a83b3a
- No provider action, external truth assertion, Owner acceptance, production gate, runtime change, authority change, lifecycle change, or canonical layer was performed.

The stale 1111 instructions/CURRENT.md and 1111 relay/current pointers were recorded as STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL and left unchanged. They did not override the explicit Task157 command.

## Family coverage

| Family | Question | Holdout defects | MJ flags | Transfer relation |
|---|---|---:|---:|---|
| F1 | claim_to_action_mismatch | 24 | 18 | claim -> action -> execution packet |
| F2 | approval_to_action_mismatch | 24 | 13 | approval -> action -> lease |
| F3 | lifecycle_epoch | 24 | 18 | source -> projection -> release -> admission |
| F4 | base_delta_scope_contamination | 24 | 16 | Base -> Delta -> admission |
| F5 | source_identity_projection_surface_drift | 24 | 17 | source -> identity -> projection -> public surface |
| F6 | release_admission_provider_reference | 16 | 12 | release -> admission -> provider -> Current boundary |
| F7 | consequence_reconciliation_ownership | 24 | 17 | effect -> obligation -> observer/owner -> stop |
| F8 | novel_multi_hop_composition | 24 | 12 | source -> identity -> projection -> release -> admission -> action |

## Method

M0 used only object-local status records. ML used the frozen direct predicate registry, with no shared tuple helper. MJ used one typed research candidate over existing subject_id, version, scope, and lifecycle_epoch fields plus existing object references. MH was diagnostic only. Strict equality was not treated as sufficient: valid v1-to-v2 migration and allowed surface delay were explicit controls. The scorer input excluded the answer key and historical outcomes; two clean-clone runs were required to be byte-identical.

Strong controls included valid upgrades and migrations, same digest with distinct object context, allowed surface delay, fail-closed abstention, no safe alternative, irreversible effect with a correct existing charter marker, valid signer without a concrete defect, irrelevant evidence, label-only variation, Base/Delta isolation, and unknown distinct from fail.

## Metamorphic and maintenance evidence

- Metamorphic rows: 377; violations: 0
- Junction ablation rows: 8; removed dimensions and relations are recorded without promoting any dimension.
- Maintenance perturbations: 8; ML semantic update sites are distributed while MJ adapter changes are centralized, with central blast radius retained as a residual.

## Interpretation

If the frozen gates support MJ, that supports only a reusable research candidate for review. It does not establish a new truth state, authority, capability, lifecycle state, canonical contract, validator, or runtime gate. Task156 vocabulary is downgraded from any strong foundation claim to bounded comparative research vocabulary.
