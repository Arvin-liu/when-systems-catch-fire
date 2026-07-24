# 点火生产运行时攻击矩阵 / Ignition RPE Attack Matrix

Draft production layer (`production/ignition-run-promote-evolve-r1`). Each row
maps a scenario test (`tests/ignition_runtime/test_scenarios.py`) to an attack
and the defensive invariant that closes it. All 45 scenarios pass (51 pytest
cases including parametrization).

## A. Pointer / store integrity (fail closed)

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S01 | `test_s01_bootstrap_empty_store` | empty store must bootstrap once only | `bootstrap()` once; second call → `PointerError` |
| S02 | `test_s02_deleted_current_fails_closed` | delete CURRENT after RUN | `resolve_current_gen` → `PointerError` |
| S03 | `test_s03_bad_current_fails_closed` | empty / multiline / traversal / symlink CURRENT | `read_current` rejects; `O_NOFOLLOW`; `is_safe_token` |
| S04 | `test_s04_dangling_pointer_fails_closed` | CURRENT points to nonexistent gen | dangling reference → `PointerError` |
| S38 | `test_s38_path_escape_guard` | provider root escapes boundary; token/path traversal | `PathEscapeError`; `assert_under_root`; `CURRENT` stays under store root |

## B. Closed-manifest closure (triple equality)

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S05 | `test_s05_missing_required_file` | drop an authoritative file | `load_generation` → `ManifestError` |
| S06 | `test_s06_drop_file_and_digest_still_rejected` | drop file **and** its digest entry | `declared != CANON[op_type]` → `ManifestError` |
| S07 | `test_s07_undeclared_file` | add an extra authoritative file | `actual != declared` → `ManifestError` |
| S08 | `test_s08_digest_mismatch` | mutate a file but keep its declared digest | recomputed digest mismatch → `ManifestError` |
| S09 | `test_s09_parent_mismatch` | rewrite parent pointer | parent resolution against `generations_root` → `ManifestError` |
| S10 | `test_s10_immutable_after_commit` | mutate committed candidate after commit | reload digest mismatch → `ManifestError` |
| S32 | `test_s32_audit_evidence_tamper` | forge `audit_index` gen_id | audit entry digest mismatch → `ManifestError` |

## C. Crash / atomicity (old-or-new-only)

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S11 | `test_s11_crash_before_files` | crash before any file written | old visible; `recover==old` |
| S12 | `test_s12_crash_after_manifest_pending` | crash after staging files, before manifest | old visible |
| S13 | `test_s13_crash_after_manifest_committed` | crash after manifest committed, before rename | staging orphan; old visible |
| S14 | `test_s14_crash_before_pointer_swap` | crash after rename, before swap | old visible |
| S15 | `test_s15_sigkill_after_swap` | crash after swap | new fully present |
| S27 | `test_s27_run_recovery` | crash mid-RUN, recover | `recover==old` |
| S29 | `test_s29_recovery_crash_orphan` | crash leaves staging orphan | orphan reclaimed; old visible |
| S34 | `test_s34_approval_crash_stages` | approval crash at every durable stage | old-or-new-only; request stays current until swap |

## D. Epistemic contract

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S17 | `test_s17_binding_tamper` | tamper candidate→source binding | digest + `EpistemicError` |
| S18 | `test_s18_missing_unknown_fails_closed` | empty / empty-question UNKNOWN | `EpistemicError` |
| S19 | `test_s19_arbitrary_claim_ceiling` | arbitrary claim ceiling (e.g. ROOT_CURE_ABSOLUTE) | `EpistemicError` |
| S20 | `test_s20_reorder_semantic_stable` | provider reorder | `semantic_id` deterministic |
| S21 | `test_s21_source_change_tombstones` | source change + stale entity | old `semantic_id` REPLACED; no active ghost |
| S22 | `test_s22_archived_reactivation` | revert source | reactivates ACTIVE exactly once |
| S23 | `test_s23_identical_run_stability` | identical RUN | stable ACTIVE sids, no duplicate |
| S40 | `test_s40_m5_secondary_temporal` | beyond-ceiling SOTA claim | downgraded to UNKNOWN; SECONDARY tier |

## E. Idempotency / no-op

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S16 | `test_s16_ordinary_run_visibility` | ordinary RUN visibility | parent recorded; old retained |
| S24 | `test_s24_concurrent_runs_distinct` | N identical start states | distinct generations; deterministic gen id |
| S33 | `test_s33_duplicate_promotion_request_noop` | duplicate promote_request | same `gen_id` → no-op (single gen) |
| S35 | `test_s35_duplicate_approval_same_id` | duplicate approval | same `gen_id` → no-op |

## F. Mode boundaries (RUN ≠ PROMOTE ≠ EVOLVE)

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S36 | `test_s36_run_no_promote` | RUN calls PROMOTE | static (no `promote`/`evolve` in `run.py`) + `ModeBoundaryError` at CLI |
| S37 | `test_s37_no_evolve_from_run_promote` | RUN/PROMOTE call EVOLVE | static (no `evolve` in `run.py`/`promote.py`); PROMOTE never emits `evolve` gen |

## G. Receipt / identity / non-self-reference

| ID | Scenario | Attack | Defense |
|----|----------|--------|---------|
| S30 | `test_s30_receipt_matches_generation` | receipt mismatch | `before_gen/after_gen/op_outcome/counts` match |
| S31 | `test_s31_audit_rebuild` | audit chain break | parent chain walk; tail entry == self |
| S45 | `test_s45_non_self_referential_identity` | embed live HEAD as final head | `self_final_sha_claimed=false`; `live_refetch_required=true`; HEAD absent from committed files |

## H. Functional regression

| ID | Scenario | Check |
|----|----------|-------|
| S25 | `test_s25_ingest_run_from_empty` | ingest + run from empty store |
| S26 | `test_s26_run_resume` | resume after crash re-runs deterministically |
| S28 | `test_s28_recovery_missing_file` | missing sidecar → corrupt gen; recover returns last valid gen (not None) |
| S39 | `test_s39_m1_m4_regression` | M1-M4 → 7 ACTIVE / 8 UNKNOWN / 5 signal; 0 formal promotions; 0 auto-evolve |
| S41 | `test_s41_branch_and_base_unchanged` | on `production/...` branch; base PR #118 HEAD untouched; not on `main` |
| S42 | `test_s42_runtime_imports_and_runs` | all modules import; run works |
| S43 | `test_s43_diff_scope` | draft diff only touches production-layer paths |
| S44 | `test_s44_remote_evidence_readable` | (skipped when control inputs absent) FileSystemProvider reads 5 materials; original upload SHA present in index |
