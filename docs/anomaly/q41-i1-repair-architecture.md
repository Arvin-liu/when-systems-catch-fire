# Q41-I1-REPAIR-R1 — Repair Architecture & Boundary

- **Task:** Q41-I1-REPAIR-R1 (item 3 of 9 in the remaining repair train)
- **Capability:** `world_feedback_anomaly`
- **Original head:** `d09bd6fe964d8879e1b5027aa28cb2e010363c05` (PR #75)
- **Repair branch:** `repair/q41-r1-anomaly-evidence-binding`
- **Direct predecessor repair branch:** `repair/scientific-metacognition-r1-epistemic-state-binding` @ `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3`
- **Annotated tag (planned):** `archive/q41-repair-r1-frozen-head`

## Original problem (R0 reproduction)
`tools/anomaly/validate_world_feedback_anomaly_gate.py` delegates to the shared
`structured_capability_gate`. The shared gate recomputes `artifact_digest` from the **working-tree**
file bytes and only regex-format-checks `exact_head`/`commit_sha`. It does **not** verify that the
evidence is actually bound to the claimed commit via `blob_sha` + content `sha256` read from the Git
object of that commit.

Reproduction (`data/anomaly/repro/original-evidence-binding-failure.json`):
- Each evidence record's `artifact_digest` is recomputed from the current working tree (so the
  digest check passes), and `exact_head` is set to a valid-format commit
  (`2b18e1f2d11511dc758734338e7c715566d01394`). The gate never verifies the file bytes at that
  commit match the claimed digest.
- Real CLI result: `{"exit_code": 0, "exit_name": "GATE_PASS"}` — the gate wrongly passes.
- This proves evidence is asserted via self-reported `artifact_digest` + `evidence_refs` strings,
  not anchored to a specific historical Git object.

## Repair boundary (R1 plan)
1. Extend `schemas/anomaly/world_feedback_anomaly-contract.schema.json` `$defs/evidence` with optional
   `repository_relative_path`, `commit_sha` (40-hex), `blob_sha` (40-hex), `sha256`
   (`^sha256:[0-9a-f]{64}$`), `record_type`, `declared_role` (relax `additionalProperties: false`
   → `true`).
2. The shared validator already performs the fail-closed `reference_integrity_check` (R1 of the shared
   module, inherited from the predecessor). For each evidence entry carrying `commit_sha` +
   `repository_relative_path`, verify `blob_sha == git rev-parse {commit_sha}:{repository_relative_path}`
   and `sha256 == sha256(git show {commit_sha}:{repository_relative_path} bytes)`. Mismatch → exit 4
   (EVIDENCE_BINDING_INVALID). No strip before hashing.
3. Rebind the pilot `data/anomaly/pilot-q41-i1.json` evidence registry with real
   `repository_relative_path`/`commit_sha`/`blob_sha`/`sha256` for the actual objects at the SM repair
   head `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3`, and update `parent_binding.exact_head` + the
   validator `CONFIG.parent_head` to `183f4343a036d0dbb20ae7df9dd96be97bcd3fc3`.

## Task-specific semantic checks (spec)
Independent verification required: recurring expected/observed divergence, repeat window, deviation
metric, threshold source, decision basis. A single residual is NOT a hidden system; no threshold-free
escalation; failure sampling must be balanced; recurring evidence is required before a rebuild decision;
repair budget is bounded; escalation authority is required; stop/rollback is present. Model self-rating
is NOT evidence; anomaly is NOT causal proof.

## Scope guards
- Builder-only: no merge, no Main modification, no external actions.
- Only this task's repair branch is written; predecessor frozen heads untouched.
- Evidence binding must use real Git objects; no placeholders, nulls, all-zero, or self-reported booleans.
