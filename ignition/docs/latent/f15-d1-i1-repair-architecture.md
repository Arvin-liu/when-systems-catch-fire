# F15-D1-I1-REPAIR-R1 — Repair Architecture & Boundary

- **Task:** F15-D1-I1-REPAIR-R1 (item 4 of 9 in the remaining repair train)
- **Capability:** `latent_system_identifiability`
- **Original head:** `d09bd6fe964d8879e1b5027aa28cb2e010363c05` (original PR #76)
- **Repair branch:** `repair/f15-d1-r1-latent-system-identifiability`
- **Direct predecessor repair branch:** `repair/q41-r1-anomaly-evidence-binding` @ `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`
- **Annotated tag (planned):** `archive/f15-d1-repair-r1-frozen-head`

## Original problem (R0 reproduction)
`tools/latent/validate_latent_system_identifiability_gate.py` delegates to the shared
`structured_capability_gate`. The shared gate recomputes `artifact_digest` from the **working-tree**
file bytes and only regex-format-checks `exact_head`/`commit_sha`. It does **not** verify that the
evidence is actually bound to the claimed commit via `blob_sha` + content `sha256` read from the Git
object of that commit.

Reproduction (`data/latent/repro/original-evidence-binding-failure.json`):
- Each evidence record's `artifact_digest` is recomputed from the current working tree (so the
  digest check passes), and `exact_head` is set to a valid-format commit
  (`d09bd6fe964d8879e1b5027aa28cb2e010363c05`). The gate never verifies the file bytes at that
  commit match the claimed digest.
- Real CLI result: `{"exit_code": 0, "exit_name": "GATE_PASS"}` — the gate wrongly passes.
- This proves evidence is asserted via self-reported `artifact_digest` + `evidence_refs` strings,
  not anchored to a specific historical Git object.

## Repair boundary (R1 plan)
1. Extend `schemas/latent/latent_system_identifiability-contract.schema.json` `$defs/evidence` with
   optional Git-object fields (`repository_relative_path`, `commit_sha` (40-hex), `blob_sha`
   (40-hex), `sha256` (`^sha256:[0-9a-f]{64}$`), `record_type`, `declared_role`) by relaxing
   `additionalProperties: false` → `true`.
2. The shared validator already performs the fail-closed `reference_integrity_check` (inherited from
   the predecessor). For each evidence entry carrying `commit_sha` + `repository_relative_path`,
   verify `blob_sha == git rev-parse {commit_sha}:{repository_relative_path}` and
   `sha256 == sha256(git show {commit_sha}:{repository_relative_path} bytes)`. Mismatch → exit 4
   (EVIDENCE_BINDING_INVALID). No strip before hashing.
3. Rebind the pilot `data/latent/pilot-f15-d1-i1.json` evidence registry with real
   `repository_relative_path`/`commit_sha`/`blob_sha`/`sha256` for the actual objects at the Q41
   repair head `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`, and update `parent_binding.exact_head` +
   the validator `CONFIG.parent_head` to `da9c4e2a6b8c0f757aa676814fda7c86d4ac2558`.

## Task-specific semantic checks (spec)
Independent verification required: latent-system candidate and equivalent decompositions can remain
candidate objects until distinguishing evidence passes an explicit identifiability gate. A residual is
NOT a latent entity; a shared pattern is NOT a common cause; non-identifiable decomposition remains
unresolved; distinguishing evidence is required before promotion; contradictions are preserved;
unsupported elements are not promoted; claim ceiling preserved. Model self-rating is NOT evidence; no
Q45+ numbering; no universal truth; no causal proof established; no ecosystem deployed.

## Scope guards
- Builder-only: no merge, no Main modification, no external actions.
- Only this task's repair branch is written; predecessor frozen heads untouched.
- Evidence binding must use real Git objects; no placeholders, nulls, all-zero, or self-reported booleans.
