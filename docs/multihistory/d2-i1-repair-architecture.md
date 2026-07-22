# D2-I1 Repair-R1 — Architecture & Boundary

> Builder-only. Repository-governance candidate only; claim ceiling enforced. Part of the serial `repair-r1` train (item 5/9).

## Scope

Repair `D2-I1` (`multi_history_world_projection`) for the same evidence→Git-object
binding-integrity gap fixed in the predecessor chain
(`DECISION-INTEGRITY` → `SCIENTIFIC-METACOGNITION` → `Q41` → `F15-D1`). The
capability itself (multiple evidence-constrained history/world candidates
preserving shared evidence, branch assumptions, indistinguishable sets and
falsifiers without forcing a unique story or unjustified probability) is
untouched semantically; only the evidence-grounding integrity is hardened.

## Root cause (reproduced in R0)

`data/multihistory/repro/original-evidence-binding-failure.json` runs the current
`tools/multihistory/validate_multi_history_world_projection_gate.py` and returns
`GATE_PASS` (exit 0). The bundle carries a correct **working-tree** `artifact_digest`
(recomputed from `path.read_text()`) but **no** `commit_sha` / `repository_relative_path`
/ `blob_sha` — i.e. the evidence is not anchored to an immutable Git object. The
gate never verifies that `exact_head`/`commit_sha` resolves to a real Git object,
nor that the artifact bytes at that commit match the claimed `blob_sha`/`sha256`.

```
python tools/multihistory/validate_multi_history_world_projection_gate.py \
  --bundle data/multihistory/repro/original-evidence-binding-failure.json
=> GATE_PASS (exit 0)   # working-tree-only binding accepted — the original gap
```

## Repair plan (R1–R4)

- **R1** — Relax `evidence` `$def` `additionalProperties:false → true` (fields
  allowed-but-undeclared, mirroring Q41/F15-D1). Retarget `parent_head`
  `8db9e5ab…` → `f0f7d7ff…` (direct predecessor repair exact head = F15-D1 R4).
  Rebind every evidence object in `data/multihistory/pilot-d2-i1.json` to real
  Git objects at `f0f7d7ff` (`commit_sha`+`repository_relative_path`+`blob_sha`+`sha256`).
- **R2** — Regenerate the 24 fixtures to `f0f7d7ff` via `build_d2-i1_fixtures.py`;
  add `test_git_object_binding_is_enforced` (tamper sha256 → exit 4) and
  `test_f15_d1_predecessor_regression` (F15-D1 pilot through F15-D1 validator → exit 0).
- **R3** — Recompute propagation closure (persisted, authoritative for non-121Q32I);
  sync manifest `data/operations/iterations/D2-I1.json` + seal
  `reports/operations/D2-I1-completion-seal.json` (base = `repair/f15-d1-r1-latent-system-identifiability`,
  base_head `f0f7d7ff`, PR #94); run `validate_iteration_sync`,
  `compute_change_propagation --check`, `validate_human_front_door`.
- **R4** — Freeze doc; annotated repair tag `archive/d2-repair-r1-frozen-head`;
  Draft PR #94; 1111 receipt + index.

## Predecessor

- Direct predecessor: `F15-D1-I1` → repair branch `repair/f15-d1-r1-latent-system-identifiability`
  (exact head `f0f7d7ff9dda620d59ad1dd1b504bcd503fe5c09`).
- Repair tag for this task: `archive/d2-repair-r1-frozen-head`.
- Trusted main `81edff4039619b8343a82cb1b84785c8a9f6a990` (never modified).

## Boundary

No semantic change to multi-history projection; no external action, L7, or
truth-layer upgrade. Builder-only: not self-reviewed, not Ready/merged, Main
untouched, original PR #77 untouched.
