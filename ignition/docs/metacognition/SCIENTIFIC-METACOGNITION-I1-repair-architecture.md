# SCIENTIFIC-METACOGNITION-I1-REPAIR-R1 — Repair Architecture & Boundary

- **Task:** SCIENTIFIC-METACOGNITION-I1-REPAIR-R1 (item 2 of 9 in the remaining repair train)
- **Capability:** `epistemic_state_control_plane`
- **Original head:** `2b18e1f2d11511dc758734338e7c715566d01394` (PR #74)
- **Repair branch:** `repair/scientific-metacognition-r1-epistemic-state-binding`
- **Direct predecessor repair branch:** `repair/decision-integrity-r1-principle-process-binding` @ `25bd2ca3e14a2693e3c9fac49a2547e1aa7ca9a8`
- **Annotated tag (planned):** `archive/scientific-metacognition-repair-r1-frozen-head`

## Original problem (R0 reproduction)
`tools/metacognition/validate_epistemic_state_control_plane_gate.py` delegates to the shared
`structured_capability_gate`. The shared gate recomputes `artifact_digest` from the **working-tree**
file bytes and only regex-format-checks `exact_head`/`commit_sha`. It does **not** verify that the
evidence is actually bound to the claimed commit via `blob_sha` + content `sha256` read from the Git
object of that commit.

Reproduction (`data/metacognition/repro/original-evidence-binding-failure.json`):
- Each evidence record's `artifact_digest` is recomputed from the current working tree (so the
  digest check passes), but `exact_head` is set to a different, valid-format commit
  (`2b18e1f2d11511dc758734338e7c715566d01394`) that does NOT contain those blobs.
- Real CLI result: `{"exit_code": 0, "exit_name": "GATE_PASS"}` — the gate wrongly passes.
- This proves evidence is asserted via self-reported `artifact_digest` + `evidence_refs` strings,
  not anchored to a specific historical Git object.

## Repair boundary (R1 plan)
1. Extend `schemas/metacognition/epistemic_state_control_plane-contract.schema.json` `$defs/evidence`
   with optional `repository_relative_path`, `commit_sha` (40-hex), `blob_sha` (40-hex),
   `sha256` (`^sha256:[0-9a-f]{64}$`), `record_type`, `declared_role` (explicit allows; keep
   `additionalProperties: false`).
2. Add a fail-closed `reference_integrity_check` to the validator: for each evidence entry carrying
   all six reference fields, verify `blob_sha == git rev-parse {commit_sha}:{repository_relative_path}`
   and `sha256 == sha256(git show {commit_sha}:{repository_relative_path} bytes)`. Mismatch → exit 4
   (EVIDENCE_BINDING_INVALID). No strip before hashing.
3. Rebind the pilot `data/metacognition/pilot-scientific-metacognition-i1.json` evidence registry with
   real `repository_relative_path`/`commit_sha`/`blob_sha`/`sha256` for the actual objects, so the
   correctly-bound pilot passes and the tampered repro fails.

## Task-specific semantic checks (spec §6)
Independent verification required: epistemic state, unknown types & priority, evidence-acquisition
authority, cost/risk/time budget, deterministic replay, state-transition basis, replan conditions,
non-identifiable retention. Model self-rating is NOT evidence; unknown must not be disguised as
resolved; dominant discourse must not masquerade as fact.

## Scope guards
- Builder-only: no merge, no Main modification, no external actions.
- Only this task's repair branch is written; predecessor frozen heads untouched.
- Evidence binding must use real Git objects; no placeholders, nulls, all-zero, or self-reported booleans.
