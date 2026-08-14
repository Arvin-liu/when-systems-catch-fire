# 121Q6 — Function OS v0.2.1 Hardening & Reproducibility

**Status: ✅ COMPLETE — PARTIAL_ACCEPTED_AS_HARDENED_CANDIDATE**
**Executor:** QClaw | **Model:** Hy3 (pool-hy3-preview), adaptive deep-thinking HIGH | **No Auto / no model-switch / no fallback / no subagent**

## Scope
25-step hardening protocol on top of 121Q5 (canonical node realignment). Hardens Function OS `v0.2.1-candidate` for reproducible tests, deterministic execution, and real control-plane operation. Excludes weight-space / probabilistic semantics (per protocol).

## Defects Found & Fixed (real)
| Node | Defect | Fix |
|------|--------|-----|
| N1 | Parser accepted `spec_version: "0.0.0"` (SEMVER regex allowed all-zero) | Added explicit rejection in `_validate` |
| N6 | `trace_hash` included non-deterministic `trace_id` (global exec counter) + `timing_ms` → different hash per call order | Now content fingerprint: `artifact_id/spec_id/status/inputs/outputs/errors` only |

## Hygiene Fixed
- Removed `__main__` smoke blocks containing `sys.path.insert` from `n2/n3/n4/n6`; removed n9 smoke block (n1/n5/n7/n8 already clean).
- Deleted 3 tracked `__pycache__/*.pyc`; `.gitignore` now covers `__pycache__/*.py[cod]`, `.pytest_cache`, `.coverage`.
- All tests use standard package import — **zero `sys.path` injection** in any test.

## Test Suite (155 tests)
- Per-node robust suites: n1(24) n2(9) n3(8) n4(7) n5(8) n6(11) n7(8) n8(8) n9(16)
- Integration: full-chain N1→N9 (5) + N8 real control-plane routing over populated N9 registry (4)
- **Reproducibility verified**: 151 tests pass under **unittest AND pytest**, from **TWO independent CWDs** (repo root + `/tmp`) — proves path independence, no `/tmp` hardcoded paths.

## Model Identity
Prior 121Q5 status `MIXED_OR_UNVERIFIED` → now **`VERIFIED_HY3`**. Full task executed by a single Hy3 runtime; no model switching, no fallback, no sub-agents.

## Verdict
`PARTIAL_ACCEPTED_AS_HARDENED_CANDIDATE` — v0.2.1 reproducible, path-independent, model-verified. Canonical node realignment (121Q5) confirmed intact. Ready for GPT final acceptance.

## Control Files
- `121q6-run-state.json` (terminal), `121q6-step-ledger.jsonl` (19 entries, Steps 000–019), `121q6-commit-guard.jsonl` (per-step parent/child verification), `121q6-reproducibility-report.md`, `121q6-final-status.json`, `121q5-reconciliation.json`, `121q5-status-correction-overlay.json`.
