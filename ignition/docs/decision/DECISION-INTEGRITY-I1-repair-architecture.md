# DECISION-INTEGRITY-I1 Repair-R1 — Architecture & Boundary

> Builder-only repair train item. Repository-governance candidate only.

## Task identity

| field | value |
| --- | --- |
| task | `DECISION-INTEGRITY-I1-REPAIR-R1` |
| capability | `decision_integrity` |
| original frozen head | `b3f27e4c3d614b95af4b112e3564fcf0e3d9f68e` (original PR #73) |
| direct predecessor | `SYMBOLIC-SPHERE-I1` (spec exact head `4ec769768d31c1fd0d7a6c066d235b4064606652`; validator `parent_head` `213dced90f1e9b1f1992a148ee10fc0844917490`) |
| repair branch | `repair/decision-integrity-r1-principle-process-binding` |
| repair tag | `archive/decision-integrity-repair-r1-frozen-head` |
| original PR | #73 (kept OPEN/DRAFT/UNMERGED/NOT CURRENT); this item publishes an independent Draft PR |
| trusted main | `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified) |

## Original defect (reproduced in R0)

The pilot bundle `data/decision/pilot-decision-integrity-i1.json` declared
`artifact_digest` values for two evidence artifacts that did **not** match the
actual file bytes:

- `evidence.1` → `data/failure/pilot-q39-failure-lineage.json`
- `evidence.2` → `data/symbolic/pilot-symbolic-sphere-i1.json`

Real CLI reproduction:

```
python tools/decision/validate_decision_integrity_gate.py \
  --bundle data/decision/pilot-decision-integrity-i1.json
=> {"exit_code":4,"exit_name":"EVIDENCE_BINDING_INVALID",
    "errors":["evidence.1: digest mismatch","evidence.2: digest mismatch"]}
```

Minimal reproduction saved at
`data/decision/repro/original-evidence-binding-failure.json` (the pre-fix pilot)
and produces the identical failure through the real CLI — no constant assertions.

## Repair strategy (R1–R4)

- **R1 — Reference-integrity.** Every evidence object binds to a resolvable
  repository reference record carrying `repository_relative_path`, `commit_sha`,
  `blob_sha`, `sha256`, `record_type`, `declared_role` — all recomputed from real
  Git objects (`git rev-parse`, `git hash-object`, `sha256sum`). The declared
  `artifact_digest` is rebound to the real committed blob bytes. The schema is
  relaxed to *allow* (optional) reference-integrity fields while keeping the
  fail-closed digest check. The decision validator gains a Git-object pre-check
  that fails closed if `blob_sha` / `sha256` / `commit_sha` do not resolve.
- **R2 — Fixtures + positive pilot + predecessor regression.** Keep the
  24-fixture fail-closed matrix (each stable failure family returns a distinct
  non-zero exit). The positive pilot depends only on real resolvable objects.
  Run the decision capability tests and the SYMBOLIC-SPHERE predecessor
  regression.
- **R3 — Propagation closure.** Component registry/profile, propagation
  request/closure/delta/residue/report, iteration manifest, completion seal —
  `persisted == recomputed`, `closure_complete=true`, `residue=0`, no unrelated
  predecessor artifacts modified.
- **R4 — Freeze + publish.** Full regression, inherited-baseline-debt comparison
  (inherited debt is not disguised as new green, scope is not expanded), final
  docs/receipt, annotated repair tag, independent Draft PR (base = predecessor
  repair branch), 1111 receipt + index.

## Fail-closed design

The shared gate `tools/governance/structured_capability_gate.py` is fail-closed:
any digest mismatch, missing artifact, malformed head, incomplete rule coverage,
unsatisfied required rule, claim-ceiling overreach, or external action → non-zero
exit. No self-reported boolean gate substitutes the nine task-specific semantics;
each DECISION-INTEGRITY semantic (ex-ante principle, standard priority,
assumptions, risk, alternatives, stop conditions, process/outcome dual-axis,
result bias, post-hoc rationalization, legitimate revision vs interest capture,
true need vs bargain/scarcity/conformity/FOMO, intake vs integration) is verified
by its own rule + evidence binding.

## Claim ceiling

All conclusions are repository-governance candidates only; no L7, no truth-layer
upgrade, no real-world universal causal claim. Builder-only: not self-reviewed,
not Ready/merged, Main untouched, original PRs untouched.
