# Round 0 Checkpoint Report — Remote Foundation CI closure

Parent: PR #190 head `16f3d83b`. Goal: trustworthy parent surface before adding the queue runtime.

## Remote CI truth at parent head (all logs read)

- `foundation-validation` run 30801202396: **FAIL** — stale generated outputs: `CENSUS_OUT_OF_DATE` (discovery/census/audit-queue/census-summary), `DEEP_ADJUDICATION_OUT_OF_DATE` (public-claim-lineage/closure-summary), `discovery:every-repository-path-accounted listed=3588 tracked=3643`, `NONFUNCTION_CLAIM_OUTPUT_DRIFT`; aggregate 60/63.
- `repository-path-accounting-preflight` run 30801201931: PASS.
- `iteration-lifecycle-validation` run 30801202590: PASS.
- `iteration-planner-ci` run 30801202335: PASS.

Local merge-ref simulation (main + PR #190 branch) passes path accounting 9/9, so the defect is branch-tree generated-output drift, not a merge-conflict artifact.

## Repair (canonical generators only, fixed point)

path manifest -> function census -> deep adjudication -> nonfunction adjudication -> migration -> governance chain, iterated until `validate_foundation.py` 63/63 and path `--check` PASS simultaneously. No generated file was hand-edited.

## Local verification at the round head

- Research OS tests (core / checkpoint C / resumability): all pass
- lifecycle + terminalization allowlist tests: pass
- migration --check, knowledge experience audit: pass
- `validate_foundation.py`: **63/63 ALL_FOUNDATION_VALID**

## Remote exact-head run

A `workflow_dispatch` run of foundation-validation will be triggered at the pushed head and recorded in ROUND-LEDGER.jsonl (field `remote_runs`). Any remaining merge-ref-specific failure would be recorded there with resumable repair instructions; none is expected because the branch tree is now self-consistent.

Research OS is not redesigned in this round; only generated surfaces were regenerated.

## Pass 2 — remote run feedback and ordering root cause

Remote exact-head run 30829240122 (workflow_dispatch, head 066f530d) FAILED at `validate_foundation.py` with `NONFUNCTION_CLAIM_OUTPUT_DRIFT` (61/63). The failure was reproduced locally, byte-for-byte in symptom. Root cause: pass 1 ran the knowledge-experience rebuild after the nonfunction adjudication; the knowledge rebuild changes tracked `KNOWLEDGE/*` contents that nonfunction discovery scans, so the earlier nonfunction outputs were stale relative to the tree. Platform sensitivity was ruled out (no z3/random/time/uuid in the generator; 19 explicit `sorted()` calls).

Pass 2 re-ran the canonical generator chain in dependency order (knowledge before nonfunction) to fixed point. Full CI-step-order replay now exits 0 for every foundation step, and all remaining workflow steps (iteration sync, phase D/E, system map, stage snapshots, front door, language-thought, knowledge determinism, unittests) exit 0. Research OS tests still pass. This head is pushed for a second exact-head remote verification.

Resumable instruction for any future drift of this class: run the chain in the order recorded in ROUND-LEDGER.jsonl `repair_pass_2.fix`, then replay the CI step order before pushing.

## Pass 3 — interpreter-version root cause (verified)

Remote run 30832717871 (head fa530044) failed with the same drift. Controlled experiment: a fresh venv at Python 3.12.13 (CI's exact version) regenerated `data/foundation/nonfunction-claims/`; 10 of 15 outputs differ from the Python 3.14.6 generation. Local green was a same-version artifact: generation and verification both ran on 3.14, while CI regenerates under 3.12 and compares against committed bytes.

Pass 3 rebuilt the whole canonical generator chain under Python 3.12.13 to fixed point. The complete CI step order (foundation, governance incl. determinism, operations, language-thought) now exits 0 under 3.12.13, and Research OS + lifecycle tests pass. Resume rule recorded in ROUND-LEDGER.jsonl: generate and verify Foundation outputs with the CI interpreter version; local-only green under another interpreter is not CI evidence.

## Pass 4 — committed-state check-only gate (final)

Remote run 30839816598 (head 3ba8d549) still failed with DEEP_ADJUDICATION_OUT_OF_DATE plus NONFUNCTION_CLAIM_OUTPUT_DRIFT (census had converged). Controlled experiments against the exact committed state established: validate_foundation under 3.12.13 reproduces the CI failure without modifying the tree; standalone --check reproduces the two drifts on committed bytes; regenerating the two drifted generators changed 13 files and then aged migration outputs (chain dependency). After migrate + governance + nonfunction regeneration, validate_foundation reached 63/63 in one iteration.

Final gate (the one that now defines round completion): 26 CI-ordered steps under Python 3.12.13 in CHECK-ONLY mode against the tree being committed — TOTAL_FAILS=0. Research OS tests 3/3; lifecycle tests PASS. Rule recorded: after any generator run, the final gate must be checks-only, CI-ordered, under the CI interpreter, against the exact tree to be committed; mixed generate+check sequences are not stability evidence.

## Pass 5 — final root cause: content-after-generation (proven by CI diff)

A temporary push-triggered debug workflow (removed in the same round) regenerated the Foundation outputs inside CI and uploaded the exact diff. The only new discovery records correspond to text added to this checkpoint report after the last local generation (the pass-4 heading) and to the debug workflow file itself. Interpreter/platform non-determinism is excluded once content order is controlled.

Round discipline encoded in ROUND-LEDGER.jsonl: for every commit — docs/ledger first, canonical generator chain second (CI interpreter, dependency order), check-only CI-ordered gate third against the exact tree, commit fourth.

## Pass 6 — propagation reconciliation closure

Remote run 30872474844 (head ffaa13cc): the Foundation generator drift checks passed for the first time; the remaining failure moved to the Task 106/107 propagation reconciliation step. Root cause: the reconciliation artifacts were stale because the canonical propagation reconciliation generator was not part of the round-0 chain. Repair: run `tools/propagation/validate_reconciliation.py --generate`, then the full remaining workflow gate (all unittest groups incl. the Task 106/107 suites) under python 3.12.13, docs-first discipline unchanged.
