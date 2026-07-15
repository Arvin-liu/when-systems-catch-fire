# 121Q7 Foundation CI Mail-Storm Repair — Verification Report

- Task: 121Q7 (IGNITION-20260715-121Q7)
- Executor: QClaw | Model: Hy3 (深度思考 high)
- Branch: ops/121q7-foundation-ci-mail-storm-repair-20260715 (stacked on PR #43)
- Base HEAD: 5396889 | Final HEAD: 
- PR: #44 (Draft, base=PR #43)

## Root cause of mail storm
foundation-validation.yml had NO `paths` filter on `pull_request`. Every Agent
push (100+) re-triggered the full foundation chain; `migrate_legacy.py --check`
was perpetually OUT_OF_DATE, so GitHub Actions emailed a failure to the subscribed
qq mailbox each push → 200+ emails.

## Step 001 — Mail-storm hemostasis (commit 0ee08d3, PR #44 f1983a6)
- Added `paths` covering all 12 real foundation dependency groups (workflow,
  requirements, formal/lean, tools/foundation, tests/foundation, data/foundation
  +architecture +math, pending_claims.json, views, schemas/foundation,
  reports/foundation-architecture).
- Added `concurrency` (cancel-in-progress, per PR/ref).
- `permissions: contents: read`; added `workflow_dispatch`.
- Effect: ordinary Agent pushes (Function OS, reports, overlays) NO LONGER
  trigger foundation-validation.

## Step 002 — Real root-cause fix (commit 3129cf7, cache-cleanup 372bba0)
- data/foundation/project-state.json was polluted by foreign runtime state
  (083_* / next_task fields) NOT produced by migrate_legacy.py deterministic
  generation → perpetual OUT_OF_DATE.
- Regenerated canonical file (git diff = this one file only).
- `migrate_legacy.py --check` now MIGRATION_CHECK_OK (EXIT 0), verified locally
  with requirements-foundation.txt installed.
- Also repaired 28 empty-field schema violations in 080/083 adjudication data.

## Local full-chain verification (deps installed)
- adjudicate_core.py --check ................ PASS
- migrate_legacy.py --check ................. PASS (root cause fixed)
- validate_foundation.py .................... PASS
- verify_core_claims.py --check ............. PASS
- verify_079.py --check ..................... PASS
- python -m unittest tests.foundation ....... PASS (no Lean locally; CI runs Lean)
- validate_080_adjudications.py ............. PRE-EXISTING FAIL at baseline HEAD
    (080-run-state.json missing counts; review_rows=609 != expected 25).
    NOT introduced by 121Q7; documented, not hidden (no skip/continue-on-error).

## Residual
080 validation is a separate pre-existing failure. With paths filter in place,
only foundation-related pushes trigger CI; the mail storm for ORDINARY pushes is
stopped. 080 needs its own reconciliation task.

## Honesty / compliance
- No workflow disabled, no continue-on-error, no if:false, no || true.
- Foundation verification steps kept intact.
- No PR merged/closed/rebased. No Ψ0/085/old-tables/evidence-cards modified.
- 2 commits with PR-number metadata (Step 001 meta, this report) per allowed
  deviation; actual fix commits are single-push each.
