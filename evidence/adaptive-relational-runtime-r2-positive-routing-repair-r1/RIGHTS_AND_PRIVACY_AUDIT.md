# Rights & Privacy Audit — R2 Positive Routing Repair R1

- No full private content enters the public formal repository. Each Source is a
  typed reference: `locator` (external_ref) + 64-hex `content_hash` only.
- `rights_boundary.classification = private_corpus`, `republication = hash_only`
  for all 48 objects — the strongest privacy-preserving representation.
- `raw_excerpt.kind = hash_only` (digest only, no verbatim text).
- `privacy_boundary_ok = True` for all 48 receipts; `REPRESENTATION_RESIDUE.
  full_private_content_leaked = 0`.
- `real_world_actions = 0` across the whole run; no network call, no second
  executor, no PROMOTE/EVOLVE path (static gate: ZERO VIOLATIONS).
- Manifest `rights_tier` / `permitted_formal_representation` constraints are
  enforced by `manifest_validator` (a third_party/personal object may not carry a
  content-copying representation).
