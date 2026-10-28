# Task report IGNITION-20260906-157

Completion state at local unblind: PENDING_DRAFT_AND_REMOTE_CI; frozen verdict: JUNCTION_INVARIANT_SUPPORTED_AS_RESEARCH_CANDIDATE.

This report answers the mandatory questions while preserving OBSERVATION, EXPERIMENTAL_MODEL, SYNTHETIC_FIXTURE, INFERENCE, VERDICT, and OPEN boundaries.

## Mandatory questions

### 1. Holdout defect and control outcomes

MJ TP=46, FN=0, abstain=0, control FP=0, TN=40; ML TP=31, FN=15, control FP=0.

### 2. Transfer generalization

MJ transfer incremental defects=22 across 8 families; no post-freeze ML predicate was added.

### 3. MJ-only defects

15 holdout instances were MJ-only; subtypes are ['approval_action_object', 'base_delta_object', 'base_delta_scope', 'claim_action_object', 'consequence_owner_object', 'lifecycle_epoch', 'novel_multi_hop', 'projection_surface_object', 'provider_admission_object', 'release_admission_object', 'rollback_consequence_object', 'source_identity_object'].

### 4. ML-only defects

0 holdout defects were ML-only against MJ; zero is recorded rather than manufactured.

### 5. Post-freeze predicate additions

None. The registry and freeze ledger record zero post-freeze local predicate additions and zero new junction dimensions.

### 6. Hidden extra facts

None. Scoring used blind packets and frozen existing fields/references; no external truth, provider output, or answer label was read.

### 7. Duplicated sites and adapters

ML has 16 direct predicate sites; MJ has one candidate with 6 relation groups plus adapters.

### 8. Maintenance perturbations

ML semantic changes were distributed across local sites; MJ changes were centralized at adapters, so drift and blast radius remain separate costs.

### 9. Strict versus typed equality

Strict equality would reject explicit v1-to-v2 migration and allowed surface delay controls; typed compatibility preserves those controls without adding authority or truth.

### 10. Tuple dimensions

The frozen candidate tested subject_id, version, scope, and lifecycle_epoch; ablation records missed holdout rows for each removal without canonicalizing any dimension.

### 11. Claim/action versus approval/action

They were separate relation groups and reason codes; a valid claim reference does not authorize an action, and a valid approval reference does not prove claim ceiling.

### 12. Historical links

CC-012, CC-020, and CC-026 are lineage context only; fresh fixtures were not historical replays and no historical record supplied an answer label.

### 13. Diagnostic labels

Missing, mismatched, unknown, ambiguous signer, provider capability, lifecycle epoch, scope contamination, and consequence ownership remain separate bounded labels.

### 14. Binding versus local

The result is comparative research evidence about a shared binding candidate versus direct local predicates, not a new canonical contract.

### 15. Downgrade of Task156 vocabulary

Any strong foundation or universal claim is downgraded to a bounded research lens and candidate assessment.

### 16. Why no canonicalization

The experiment cannot grant Owner authority, external truth, production readiness, or lifecycle permission; a separately authorized design task would be required.

### 17. Metamorphic evidence

377 rows were checked and 0 violations were observed.

### 18. Remaining maintenance risk

A shared invariant reduces duplicated logic but increases centralized blast radius; the ledger preserves both sides.

### 19. Repository and CI status

Formal and 1111 Draft PR evidence is recorded separately after publication; a Draft, CI, or projection is not equated with acceptance.

### 20. Final epistemic boundary

The verdict is frozen research evidence only: no production, canonical, authority, capability, lifecycle, external-truth, merge, promotion, or Owner-acceptance claim.

## Machine evidence

- freeze digest: a877f928440b83c58f3638cd937cba57c8b1e8956902d573fb7dbd36baf5925a
- score-run-1 SHA-256: 4022350ec54078e7d8bb151313f2dc1ab99bb41bb2a942ae2f00c3aaf003a040
- results SHA-256: f8d32fb6e5c054cf3a36dc1ef2fe2fbfef7015e824fc012323e8da6a26a83b3a
- metamorphic violations: 0
- formal baseline: ad0e8f3e6c80eee5f27d05bd4b29653b2d936aae
- command source SHA-256: 621a4aa243a3268d65c88c1960d4690a538bd228964f2fb79df4bef3d206b2a5

## Residuals

- STALE_CONTROL_POINTER / PREFLIGHT_RESIDUAL: 1111 instructions/CURRENT.md and 1111 relay/current were observed and left unchanged.
- A Draft PR is not Owner acceptance; CI is not external truth; repository equality is not external truth.
- No full-regression claim is made unless the exact command-required run is separately evidenced.
