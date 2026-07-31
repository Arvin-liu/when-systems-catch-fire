# Task 107 — Foundation Drift Repair: Incident Report

**Task:** `IGNITION-FOUNDATION-DRIFT-REPAIR-UNIVERSAL-DISCOVERY-PREFLIGHT-AND-PROPAGATION-CI-PROOF-R1-20260731`
**Executor:** WorkBuddy
**Formal repo:** `Arvin-liu/when-systems-catch-fire`
**Branch:** `agent/foundation-drift-repair-universal-preflight-propagation-ci-proof-r1-20260731`
**Predecessor:** Task 106 (`IGNITION_CONTINUOUS_ITERATION_PROPAGATION_CLOSED_CURRENT_TRUTH_RECONCILED_AND_MERGED`, PR #162, merge `af988422`)

## 1. What actually broke

Task 106 merged (PR #162) but its remote `foundation-validation` workflow failed *before* reaching the
new propagation-reconciliation step. The failure was **not** introduced by task 106 — it was latent drift
already sitting in `main`. Task 106's receipt listed four failure modes:

- `generator:deterministic DEEP_ADJUDICATION_OUT_OF_DATE`
- `generator:deterministic NONFUNCTION_CLAIM_OUTPUT_DRIFT`
- `nonfunction-claim-closure:integrated`
- `discovery:every-repository-path-accounted` (registry `listed=3094`, repo `tracked=3150`)

The root cause is **not** any single claim. It is an **infrastructure** defect: the repository's *Git path set
itself* is an input to the discovery/closure machinery, but nothing guaranteed that every Git-tracked path was
accounted for, and the workflow that should have caught this only fired on a narrow set of paths.

## 2. Why a "Foundation-untouching" PR can still break Foundation next run

The discovery registry (`data/foundation/nonfunction-claims/source-discovery.jsonl`) is supposed to enumerate
every repository path so the `discovery:every-repository-path-accounted` gate can compare it against
`git ls-files`. In reality the committed registry had drifted: PRs #160 and #161 added files to the tree
without re-triggering the heavy `foundation-validation` workflow (see §4), so the registry went stale. The
next time *any* PR triggered the workflow, the gate compared a stale `listed` set against the now-larger
`tracked` set and failed — even though the PR changed nothing about Foundation logic.

**Key lesson:** the Git path set is a *first-class input* to Foundation discovery. A repo is not "Foundation-stable"
just because the last Foundation edit was correct; it is stable only when the discovery/closure inputs (the
entire tree) are continuously reconciled.

## 3. Why a narrow workflow `paths:` filter creates latent drift

`foundation-validation.yml` filtered its triggers with a hand-maintained `paths:` list. When a PR touched
paths outside that list (e.g. `docs/...`, `analysis/...`, new top-level directories), the heavy validation
simply did not run. The drift accumulated silently until a later PR (task 106's #162) finally triggered it and
exposed the accumulated staleness. This is the classic *narrow-trigger* trap: the filter that is meant to save
CI time becomes the mechanism by which correctness regressions hide.

## 4. Why broadly widening an ignore glob would hide the problem

One tempting "fix" is to make the discovery gate ignore the new paths (a broad glob exclusion). That is exactly
what contract §3.1 forbids: it would silence the symptom while leaving the real invariant — *every* tracked
path must be classified and reconciled — unenforced. A path that is silently excluded can later become an
unaccounted authoritative input without anyone noticing.

## 5. The two-layer CI design (completeness without cost)

- **Layer A — universal repository-path-accounting preflight** (`tools/foundation/validate_repository_path_classification.py`,
  workflow `repository-path-accounting-preflight.yml`): a fast, stdlib-only rule engine that classifies **every**
  Git-tracked path into exactly one governed category. No `paths:` filter — it triggers on *every* PR and
  *every* push to `main`. It fails closed on any unclassified / duplicate / conflicting / stale path, and enforces
  the anti-backflow boundary (only the two CJK master tables may feed authoritative claim discovery).
- **Layer B — scoped heavy Foundation validation** (`foundation-validation.yml`): now triggered with **no**
  `paths:` filter, so it always runs when anything relevant changes. It runs the generators + closure checks and
  then the task-106 propagation-reconciliation step.

This separates the cheap, always-on path-accounting guarantee (Layer A) from the expensive deterministic
regeneration (Layer B), so cost does not tempt anyone to narrow the trigger again.

## 6. The 56 unaccounted paths, itemised

Reproduced at the latent `main` (`af988422`): `tracked=3150`, discovery registry `listed=3094`, **exactly 56
unaccounted paths** (`tracked − listed`, because at that commit `listed ⊆ tracked`). Each was classified by the
same engine Layer A uses (no broad silent glob):

| Category | Count |
|---|---|
| EDITORIAL_ARTICLE | 24 |
| CANDIDATE_NONAUTHORITATIVE_RECORD | 14 |
| TOOL_OR_WORKFLOW | 10 |
| RECEIPT_HISTORY_OPERATIONS | 7 |
| TEST_FIXTURE | 1 |

None were mislabeled as authoritative claim inputs. The full register is
`data/foundation/task-107-path-classification-register.jsonl`.

> **Reproduction pitfall (documented for next time):** `git ls-tree --name-only` quotes non-ASCII (CJK) paths by
> default (`core.quotePath`), emitting octal-escaped strings and producing a false 1489 "divergence". The correct
> reproduction uses `git ls-tree -z` (raw, NUL-delimited) and NFC-normalises both sides. With that fix the count
> is exactly 56, matching the contract.

## 7. Generator fixed point (§3.3)

The heavy Foundation outputs were stale. Regeneration required the **correct order**:

```
adjudicate_core.py
migrate_legacy.py
build_function_asset_census.py
adjudicate_function_assets.py
adjudicate_nonfunction_claims.py
migrate_legacy.py   # RE-RUN LAST: project-state/registry-manifest/migration-summary
                     # must reflect the finalised registries, or they read stale counts
```

Re-running `migrate_legacy` last closes the order hazard: its snapshot enumerates the finalised registries, so
it no longer goes `OUT_OF_DATE` after the claim/asset registries land. The documented order manifest is
`data/foundation/task-107-generation-order-manifest.json`.

After regeneration, all gates are green locally (see §9 / verification ladder): 5 generators `--check` pass,
`validate_function_asset_closure.py` 46/46, `validate_nonfunction_claim_closure.py` 54/54
(`discovery:every-repository-path-accounted listed=3161 tracked=3161`), and the foundation test suite 16/16.

## 8. Semantic safety of the regeneration (§5)

The regeneration is **drift-closure only** (`data/foundation/task-107-semantic-diff.json`):
- 41 new nonfunction claims + 41 new function assets discovered (from repo state the stale outputs had not
  scanned), all low-maturity (`M0`/`M1`, `E0`) / quarantine / definitional — **none** promoted to
  `ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT` or `ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT`.
- **Zero** existing claims/assets changed disposition, maturity, or claim ceiling.
- No withdrawn-conclusion rebound.
- No new scientific conclusions, no maturity upgrades, no claim-ceiling promotions.

## 9. What this round proved — and what it did not

**Proved:** the latent Foundation drift is repaired; every Git path is now governed by a fast, always-on
preflight; the heavy validation triggers unconditionally; the generators reach a deterministic fixed point; and
the task-106 propagation-reconciliation gate is wired into Layer B and passes locally.

**Not proved here (requires remote CI):** that the *remote* GitHub Actions run reaches and passes the task-106
propagation step end-to-end. That is the §6 proof and is established by opening PR #163 and letting the remote
workflow execute (see the verification ladder and the relay receipt).

## 10. Negative fixtures added (contract §4)

`tests/foundation/fixtures/repository-path-classification/` (duplicate + authoritative-mislabel manifests) plus
`tests/foundation/test_repository_path_classification.py`, `test_trigger_coverage.py`,
`test_generator_reconciliation_staleness.py` enforce: new-unclassified path, duplicate category, deleted-path
stale, editorial-mislabeled-authoritative, authoritative-change-trigger, stale generator output, two-pass
fixed point, and task-106 propagation staleness.
