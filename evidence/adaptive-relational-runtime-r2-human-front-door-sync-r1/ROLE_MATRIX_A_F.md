# Role Matrix — Sessions A–F (≥6 distinct sessions)

This repair was executed across distinct roles/sessions to keep diagnosis, contract,
audit, fix, verification, and publication separated.

| Session | Role | Responsibility | Key artifacts |
|---------|------|----------------|--------------|
| A | Runtime Architect | Branch/commit structure; exactly one child branch from `5771d6c`; exactly two ordinary commits (noreply); one Draft PR #124 (base `ci-r1`). | branch `repair/...human-front-door-sync-r1` |
| B | Canonical Map / Registry Identity Auditor | Enumerate the 100 nodes; prove the 100th is legitimate (not duplicate/orphan/`l7`); set-equality proof across registry/layout/generator. | `CANONICAL_NODE_IDENTITY_AUDIT.md` |
| C | CI Failure Reproducer | Reproduce `100 != 99` exactly: detached-HEAD local run on `5771d6c` + complete remote log (`REMOTE_CI_JOB_LOG_30143814302.txt`, line 719 = 100 PASS, lines 896–906 = `100 != 99`). | `CI_FAILURE_REPRODUCTION.md` |
| D | Source & Evidence Classifier | Classify the defect: stale hand-maintained count literal (`99`), not a data bug; note validator's `required_nodes` already = 100 and matches spec. | `CI_FAILURE_REPRODUCTION.md` |
| E | Gate Designer | Design drift-resistant canonical node-set gate: derive `expected_ids` from registry `visible` + layout `node_order` (independent of validator's `required_nodes`); assert exact identity; retain no-`l7`; fail on missing/extra/orphan/duplicate/non-clickable/`l7`. | `NARROW_REPAIR_CONTRACT.md` (contract) → commit 2 test |
| F | Verification & Publication | Run ARR pytest + `test_human_front_door` + `validate_human_front_door.py` + generator `--check`; watch `foundation-validation` to `success`; publish Draft PR #124, 1111 evidence branch, annotated frozen tag. | `FIX_VERIFICATION.md` (commit 2) |

## Guardrail ledger (all 0)
`WAIC_FULL_CORPUS_RUNS=0`, `R3_STARTED=0`, `REAL_WORLD_ACTIONS=0`, `FORMAL_ASSETS_PROMOTED=0`,
`AUTO_EVOLVE_STARTED=0`, `FORMAL_READY_PRS=0`, `FORMAL_MERGES=0`, `MAIN_CHANGES=0`,
`FORCE_PUSHES=0`, `HISTORY_REWRITES=0`, `EXTERNAL_ACCEPTANCE_CLAIMED=0`.
