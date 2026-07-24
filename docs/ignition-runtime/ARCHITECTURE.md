# 点火生产运行时架构 / Ignition Production Runtime — Architecture

Draft production layer on branch `production/ignition-run-promote-evolve-r1`.
This is a build artifact, not merged/current capability, and does not alter the
frozen formal protocol or the iteration method `1.3.0`.

## 1. Module map

```
tools/ignition_runtime/
  errors.py            # IgnitionError + SimulatedCrash, PointerError, ManifestError,
                       # EpistemicError, IdentityError, ModeBoundaryError,
                       # AuthorizationError, PathEscapeError
  hashutil.py          # sha256_bytes/text/file, deterministic_id, is_safe_token,
                       # assert_under_root, safe_open_nofollow
  schemas_loader.py    # Draft202012Validator wrapper
  generation.py        # Generation model + CANON + closed-manifest triple-equality
  store.py             # StoreLayout: strict CURRENT pointer, once-only bootstrap
  transaction.py       # publish_generation: the single atomic write path
  epistemic.py         # source binding, semantic_id, ceilings, lifecycle, contract
  providers/
    base.py            # MaterialProvider ABC, MaterialRecord
    fixture_provider.py# deterministic M1-M4 (7/8/5) + M5 SECONDARY
    filesystem_provider.py # reads real .md inputs, path-escape guarded
  run.py               # RUN mode (no reference to promote/evolve)
  promote.py           # PROMOTE mode (no reference to evolve)
  evolve.py            # EVOLVE mode (separate gated mode)
  recovery.py          # cleanup_orphans, recover (walks back to last valid gen)
  cli.py               # argparse; hard mode boundaries; lazy imports per mode
```

Schemas: `schemas/ignition_runtime/*.json` (Draft 2020-12).

## 2. Identity & immutability

- `gen_id = "gen_" + sha256(canonical_json(core_payload))[:32]`.
- For `run`, the parent (immediate prior generation) is part of `core_payload`, so
  re-running from a new state always yields a distinct generation.
- For `promote_request` / `promote_approval` / `evolve`, the mutable pointer is
  **excluded** from `gen_id`; identity is derived from stable logical inputs
  (source run / `authorized_by` / signal id). A repeated, identical request
  therefore collapses to the same generation (idempotent no-op via
  `publish_generation`'s existing-dir check).
- `op_id` is `sha256(seed(parent, op_type, material_ids, provider_identity, authorized_by))`.

## 3. Closed manifest (CANON)

`CANON[op_type]` fixes the required file set:

| op_type | required files |
|---------|----------------|
| bootstrap | store_identity, manifest, receipt, audit_index |
| run | store_identity, manifest, materials, results, candidates, unknowns, signals, receipt, audit_index |
| promote_request / promote_approval | run set **+ promotion** |
| evolve | run set (no promotion) |

`validate_closed_manifest` proves `complete_file_list == digest_keys == actual_files`,
recomputes each digest, verifies the manifest self-digest, enforces
`committed`/`immutable`, checks receipt identity (`self_final_sha_claimed=false`,
`live_refetch_required=true`), and resolves the parent link against
`generations_root` (also correct while staging under `.staging/<gen_id>`).

## 4. Atomic publish (old-or-new-only)

`transaction.publish_generation` is the single writer:
staging → digest → manifest → `fsync` → `os.replace` → pointer swap.
`crash_after ∈ {none, write_files, manifest, staged, renamed, swap}` raises
`SimulatedCrash` at the named durable stage; the test suite proves the visible
`CURRENT` is always either the old complete generation or the new complete one.

## 5. Strict pointer

`store.read_current` rejects symlinks (`O_NOFOLLOW`), multiline tokens, traversal
and dangling references via `PointerError`. `bootstrap` runs exactly once; a
damaged pointer on an established store fails closed and never silently
re-initializes an empty ledger.

## 6. Epistemic contract

`epistemic.validate_epistemic_contract` enforces: non-empty `UNKNOWN`; bounded
claim ceilings; no duplicate ACTIVE `semantic_id`; ACTIVE candidates bind to a
known material `source_sha256` (REPLACED/ARCHIVED are historical tombstones and
are intentionally exempt); provider identity coherence. `semantic_id_of`
deterministically hashes `source_sha256 | normalized_claim`, so provider reorder
does not change ids. Source changes tombstone the stale `semantic_id`
(`REPLACED`); a revert reactivates it (`ACTIVE`) exactly once.

## 7. Mode boundaries (static + runtime)

- `run.py` contains neither `promote` nor `evolve` (static guard in the test).
- `promote.py` contains no `evolve` reference; it never emits an `evolve` generation.
- `cli.run` raises `ModeBoundaryError` if given `--authorize` (RUN must not carry
  promotion/evolution authorization). PROMOTE/EVOLVE import their modules lazily
  inside their own dispatch branches, so the RUN code path never loads them.

## 8. Providers

- `FixtureProvider`: deterministic, curated `M1-M4` → 7 ACTIVE candidates / 8
  UNKNOWNs / 5 signals; `M5` → `SECONDARY_ACADEMIC_INTERPRETATION`,
  `NORMALIZED_TRANSCRIPT_COPY` verdict, `temporal_calibration` `R_TQ_01..06`,
  SOTA/originality claim downgraded to UNKNOWN.
- `FileSystemProvider`: reads real `.md` inputs (index excluded), tier
  `SECONDARY_ACADEMIC_INTERPRETATION`; all reads confined to the inputs root
  (path-escape guard). It never changes the production architecture.

## 9. Recovery

`recovery.recover` strictly resolves `CURRENT`; if the current generation is
corrupt, it walks the parent chain to the last closed-manifest-valid generation
and makes it current. `cleanup_orphans` reclaims unreachable staging dirs and
generation dirs, tolerating a corrupt link without pruning reachable committed
generations.
