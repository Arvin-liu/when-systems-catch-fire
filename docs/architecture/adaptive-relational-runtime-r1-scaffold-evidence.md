# ARR R1 Scaffold — Commit 5 Evidence & Known Limitations

Status: candidate derived representation.

This document records the synchronization work of the FINAL (5th) commit of the
Adaptive Relational Runtime (ARR) R1 Scaffold and the architecture's evidence and
counters. It is a candidate derived representation; it does not establish real-world
truth, causality, or an execution engine.

## Boundary Rules

- ARR R1 Scaffold is NOT a new truth layer, NOT an L7, and NOT a unified theory.
- `tools/adaptive_relational_runtime/` is an adapter-only package; it is NOT a second
  executor and does not perform process spawn, network I/O, or path write outside the
  ignition_runtime predecessor modules it reuses.
- Commit 5 adds NO new runtime behavior; it synchronizes maps, registries, topology and
  CI so the earlier ARR surfaces are accepted by the repo-native governance validators.
- `runtime.py` is NOT modified in commit 5.

## Publish identity (non-self-referential)

- `self_final_sha_claimed = false`
- `live_refetch_required = true`
- This document does NOT assert a final SHA and does NOT mark the scaffold ready.
- External acceptance (PRs #109–#119, Main, Ready, merge, EVOLVE, WAIC) is NOT claimed.

## Commit-2 non-blocking polish items (documented, NOT applied)

Per the exactly-5-commit rule, the following four polish items from commit 2 are recorded
as KNOWN LIMITATIONS rather than applied. They are cosmetic/contract-hygiene and do not
affect the passing 78-test suite or the 40-item attack matrix.

- **(a) `$id` form** — several ARR schemas use the short `ignition-runtime/...` `$id` form
  while the architecture convention for derived representations is the
  `https://example.invalid/ignition/...` form. Not normalized to avoid risking schema
  references already exercised by the 78 tests.
- **(b) `signal_scope` required** — a small number of signal/observation schemas could mark
  `signal_scope` as required. Left optional to preserve the committed fixture set.
- **(c) G2 `machine_rule` text** — G2 growth-gate schema could carry a stricter
  machine-readable `machine_rule` string. Left as prose to avoid re-validation churn.
- **(d) `source.tier` ↔ `evidence.tier` bridge** — an explicit bridge field between
  `source.tier` and `evidence.tier` was proposed but omitted to keep the object model
  stable for commit 5.

## Commit-4 non-blocking items (documented, runtime.py NOT fixed)

Agent J's commit-4 re-audit (verdict ACCEPT_WITH_FIXES, fresh successor agent
`8bc3d9a7`, mutation-proven on a `/tmp` copy) found two non-blocking items. Per the
exactly-5-commit rule and to avoid risking the passing 78 tests / 40 attack matrix, these
are DOCUMENTED as KNOWN LIMITATIONS in this commit-5 evidence; `runtime.py` is NOT modified.

- **NB-1** (`tools/adaptive_relational_runtime/runtime.py`, call site ~L376–380,
  `_apply_anti_overstep(bindings, relation, decision)` ~L479): the `bindings` parameter
  (registry-loaded `anti_overstep_bindings` B1–B6) is unused inside the function body;
  B1–B6 overclaim enforcement currently runs via the hardcoded gate path
  (R12/R11 + `claim_ceiling` PRIMARY_VERIFIED + forbidden-word scan). Security outcome is
  correct (ATT-11/12/13/14/15/16-20/27/28 all REFUSED), but B1–B6 are not yet
  behaviorally registry-driven. Flagged as a post-Draft follow-up.
- **NB-2** (`runtime.py`, via `_enforce_lifecycle`, called from `run()`): `eng.run()` mutates
  the caller's input `source`/`observation` dicts in place (sets lifecycle state). Tests
  use fresh dicts so all 78 pass; re-running the same input dict would re-enter
  PROVISIONAL→PROVISIONAL. Documented defensively; behavior unchanged in commit 5.

## Counters (exact)

- **5** commits in the ARR R1 Scaffold sequence.
- **14** schemas under `schemas/architecture/adaptive-relational-runtime/`.
- **10** registries under `data/architecture/adaptive-relational-runtime/registries/`.
- **9** object primitives (action, assertion, event, feedback, mechanism, object,
  observation, relation, source, state, plus runtime-envelope / execution-receipt-adapter
  satellites counted within the schema set).
- **12** fixtures (3 text / 3 Git / 2 structured / 2 runtime-receipt / 2 event-sequence).
- **40** attack-matrix items (8 REJECT codes, B1–B6 overclaim guards, 3 engine guards,
  13 projection rules).
- **10** lifecycle states / **26** legal edges / **11** `reject_reason_code`s.
- **8** failure classes.
- **6** growth gates (G1–G6 + G5g).
- **12** sub-agents A–L:
  A predecessor-auditor, B cartographer, C object-model, D projection,
  E mechanism/runtime, F evidence/lifecycle, G growth/governance,
  H sole-builder, I red-team, J replay-auditor, K integration/propagation-audit (this
  commit), L release.

## Independent audit trail

- **I** (commit 2): ACCEPT_AS_IS.
- **J** (commit 3): ACCEPT_WITH_FIXES → commit 4 re-audit: ACCEPT_WITH_FIXES.
- **K** (commit 5): this synchronization/evidence step.
- **L** (release): pending independent release audit.

## Repository-native acceptance (commit 5 surface)

Commit 5 registers the `arr` (visible, `models` group, derived representation) and
`arr_runtime` (hidden, represented-by `arr`, NON-executor adapter) components, bumps
`project-components` 1.1.13→1.1.14, adds topology relations (topology 1.1.0→1.1.1), adds
`arr` to the interactive system map (layout 1.1.0→1.1.1; map 99→100 nodes / 42→45 edges),
regenerates `component-execution-profiles.json` (arr / arr_runtime profiles are `manual`,
NON-executor), adds the 42nd iteration manifest, and extends `foundation-validation.yml`
with ARR path triggers and the anti-second-executor static scan step. The repo-native
validators `validate_human_front_door`, `validate_iteration_sync`,
`generate_interactive_system_map --check`, and `compute_change_propagation` are left green
or era-pinned; the ARR adapter static gate reports zero violations.
