# Round 0 Checkpoint — Close PR #194 Remote Repository-Wide Validation Drift

**Round:** 0 / 10 (unnumbered Task 115 continuation; not Task 116)
**Control identity:** `PARALLEL-TASK115-AGENT-AGNOSTIC-RESEARCH-RUNTIME-LICENSED-EXTERNAL-INTAKE-PR194-CLOSURE-R1-20260804`
**Frozen parent candidate:** PR #194 head `9895c0c319ab8ae09044c757d0821f5dc6532ab9`
**Child branch:** `runtime/task115-agent-agnostic-research-runtime-intake-r1-20260804`
**CI-equivalent interpreter:** Python 3.12.13 (`/usr/bin/python3` on `ubuntu-latest` ≡ local `/Users/zhiyuan/homebrew/bin/python3.12`)

## What Round 0 did (TASK.md §3)

1. **Classified all 104 PR #194 paths via the canonical rule engine** — `tools/foundation/validate_repository_path_classification.py`. No hand-editing of the failing count. The 104 paths classify cleanly into `RECEIPT_HISTORY_OPERATIONS` (15), `EDITORIAL_ARTICLE` (4), `SCHEMA` (14), `TEST_FIXTURE` (61), `TOOL_OR_WORKFLOW` (10). The previous takeover added content but never regenerated the manifest.
2. **Used CI-equivalent Python 3.12.13** for every generation step (not the local 3.13).
3. **Ran the canonical generation sequence to an idempotent fixed point** — `--generate` then `--check` twice; the manifest hash is stable across passes.
4. **Regenerated all affected derived products in dependency order**, because PR #194's 104 new tracked files shifted every scanner's tracked-file count (the `3646/3750` remote-failure signature):
   - `build_function_asset_census.py` → `data/foundation/function-assets/{discovery,census,dependencies,audit-queue,census-summary}.jsonl`
   - `adjudicate_function_assets.py` → deep-adjudication set (`identity-cards`, `adjudication-ledger`, `dependency-closure`, `public-claim-lineage`, `closure-summary`, `discovery-coverage`, `asset-inventory`, `proof-empirical-obligations`, `unresolved-quarantine`)
   - `adjudicate_nonfunction_claims.py` → `data/foundation/nonfunction-claims/*` (now `tracked_files_accounted=3750`)
   - `migrate_legacy.py` → `data/foundation/migration-summary.json`
5. **Repaired Round 7 machine-state drift** — `CANDIDATE-STATE.json` had `"round": 7, "commit": "PENDING"`. The takeover ledger (`ROUND-LEDGER.jsonl` line 13) and `ROUND-7-CHECKPOINT.md` both record Round 7's deliverable commit as `1416fcc782eb276b08d27a28d1d31fd172a7a609`, with `9895c0c3` being the subsequent "record Draft PR #194" commit. Set the field to `1416fcc7…` so state/ledger/checkpoint/PR facts agree. (PR facts in the same file — head/base/is_draft/`R2_EMPIRICAL_CALIBRATION_PENDING` — were already correct.)
6. **Ran the complete local Foundation preflight + validation** (Layer A + the pure-Python Layer B chain). The Lean proof step (`lake env lean Foundation.lean`) and the full `unittest` matrix are delegated to the remote exact-head CI, which is the authority; PR #194 did not touch any `.lean` sources, so the proof chain is unchanged.

## Local validation results (idempotent fixed points)

| Check | Result |
|-------|--------|
| `validate_repository_path_classification.py --check` | 9/9 PASS (`REPOSITORY_PATH_CLASSIFICATION_VALID`) |
| `build_function_asset_census.py --check` | `FUNCTION_ASSET_CENSUS_VALID` |
| `adjudicate_function_assets.py --check` | `FUNCTION_ASSET_DEEP_ADJUDICATION_VALID` |
| `adjudicate_nonfunction_claims.py --check` | `NONFUNCTION_CLAIM_GENERATION_DETERMINISTIC` |
| `validate_nonfunction_claim_closure.py --check` | 54/54 PASS, incl. `discovery:every-repository-path-accounted listed=3750 tracked=3750` |
| `validate_foundation.py` | 63/63 PASS |
| `validate_claim_governance.py` | 39/39 PASS |

## Hard boundaries honoured

- Normal commit only; no amend / rebase / squash / force push.
- Did **not** modify PR #194's head branch (`workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`).
- Did **not** merge, mark Ready, tag, terminalize Task 115, create Task 116, modify `main`, `relay/current`, or rewrite Task 114 history.

## Cascaded governance drift (added after remote CI feedback)

Round 0 foundation regen rewrote `data/foundation/nonfunction-claims/{claim-registry,dependency-graph,evidence-lineage}.jsonl`, which both `run_self_correction.py` and `build_knowledge_experience.py` consume. This is the repo's documented cascade pattern (task 107/108), **not** a Task 115 bug; my Round 0 commit touched no governance files directly. The remote `foundation-validation` step runs these `--check`s in one bash step with `set -e`, so the first drift aborts the step before later checks run — each layer was revealed only after the prior was fixed.

- **Self-correction (run `30903275683`):** `SELF_CORRECTION_OUTPUT_DRIFT` on 8 files (`data/governance/self-correction/*` + `RESULTS/*`). Fixed at commit `683a295e`: regenerated to fixed point (`SELF_CORRECTION_OK deltas=88 rules=10, blocking_rules=0`). Confirmed green on Linux CI (run `30907048029` printed `SELF_CORRECTION_OK`).
- **Knowledge-experience (run `30907048029`):** `KNOWLEDGE_EXPERIENCE_OUTPUT_DRIFT` on `data/governance/knowledge-experience/*` + `KNOWLEDGE/indexes/*` + `KNOWLEDGE/{README,MAP,SEARCH,COVERAGE}.md`. Root cause: `build_knowledge_experience.py` relinks links by rglob-ing the repo for target part-files; in write mode `output_map` runs before part-files exist on disk, so links resolve differently than in `--check` mode. Fixed by a **second write pass** (pass 2 relinks with part-files present) → fixed point (`KNOWLEDGE_EXPERIENCE_OK cards=355 changes=275 layered=292 search=26416`); `validate_knowledge_experience.py` clean (`KNOWLEDGE_EXPERIENCE_AUDIT_OK`). `build_human_results.py --check` (human-results) already passed and is unchanged.

## Pending

- Remote exact-head CI re-verification (push + re-run `foundation-validation`). Round 0 is complete only when both `repository-path-accounting-preflight` and `foundation-validation` are green on the child-branch head.
- Rounds 1–9 remain, now under the **callable-capability-federation** architecture per `ARCHITECTURE-AMENDMENT-EXTERNAL-CAPABILITY-FEDERATION.md` (control tip `292d15ef`): executor-neutral capability-adapter boundary, invocation-first / thin-adapter / no source vendoring, approval/watchdog state machine, license intake, OpenAI4S invocation-first mapping, narrow experiment, contradiction-gate fix, executor-substitution pilot, review packet + stacked Draft PR.
