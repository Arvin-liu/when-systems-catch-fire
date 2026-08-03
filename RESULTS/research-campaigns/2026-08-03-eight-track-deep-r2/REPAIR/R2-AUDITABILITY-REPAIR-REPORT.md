# Eight-Track R2 Auditability, Metadata and Reproduction Repair — Line C

Campaign: `POINTFIRE-QWEN38MAX-WHOLE-REPOSITORY-STATE-RECONSTRUCTION-CANDIDATE-CONVERGENCE-GLOBAL-INVARIANT-CLOSURE-R1-20260803`
Branch: `qwen38max/eight-track-r2-auditability-repair-r1-20260803` (child of exact R2 tip `ae777859`)
Scope boundary: all changes stay inside the R2 campaign root plus narrowly necessary validator/test paths. This repair does **not** promote R2 into formal knowledge; R2 remains candidate research.

## C1. Historical metadata reconstruction (from Git history, never invented)

**Track 005 freeze misbinding — repaired.** `TRACK_STATE.json` and `TRACK-INDEX.jsonl` recorded `16be95dd` as Track 005's freeze. Git history proves `16be95dd` is "r2 006 final" (Track 006's final checkpoint) and Track 005's true freeze is `4ee1ef058d0d63ec0bb9b45d83aebc1f63fde4b0` ("r2 005 freeze", touching PREREGISTRATION/R1-AUDIT/TRACK_STATE). `R1-TO-R2-VERDICT-MATRIX.md` row 005 already recorded the correct identity. Versioned correction applied with `metadata_repair` blocks recording old/new values and evidence.

**All eight tracks' checkpoint lists verified against Git history.** Every checkpoint commit exists, is ordered on the campaign branch, and touches its own track directory (validator GITBIND 174/174). Track 008's six-commit list (including a freeze-metadata commit) is the real history.

**Missing timestamps marked, never invented.** 56 source records across tracks 001/002/003/005/006/007/008 lacked `first_opened_at`/`completed_review_at`. All now carry the explicit marker `NOT_RECORDED_DURING_EXECUTION` plus a `timestamp_repair` block stating the audit consequence (reading-integrity and access-duration checks cannot verify these records; claim ceilings relying on them stay bounded). Track 004 records already carried real timestamps and were preserved.

**Schema gaps restored with cited derivations.** Track 004 `TRACK_STATE` lacked `frozen_commit` (restored: `a863584b` = checkpoint_commits[0] = "r2 004 freeze" from Git) and `claim_ceiling`; Track 006 lacked `claim_ceiling`. Both ceilings were restored verbatim from `R1-TO-R2-VERDICT-MATRIX.md` rows (no new claim introduced). Tracks 006/008 source-audit records had no access field at all; they now carry `access_level: NOT_RECORDED_DURING_EXECUTION`.

**Dialect heterogeneity documented, not silently rewritten.** Two source-audit dialects exist (A: `access_level` governed values; B: `access` prose descriptions). The validator accepts both as documented variants; unification remains an owner decision because it would rewrite 5 of 8 tracks' records.

## C2. Offline deterministic validator

`tools/research_campaigns/validate_eight_track_r2.py` (stdlib-only, deterministic, non-mutating):

- STRUCTURE required files per stage, with documented challenge-stage artifact tolerance (CHALLENGE-* file or TRACK_STATE challenge_findings/required_hard_gate);
- SCHEMA TRACK_STATE / SOURCE-AUDIT / CLAIM-MATRIX / STATUS / TRACK-INDEX parse and carry required keys;
- TIME_STATE time fields are ISO-8601-ish or the explicit NOT_RECORDED marker — blank is a failure;
- GITBIND checkpoint commits exist, are ordered, and bind to their track directory; frozen_commit == checkpoint_commits[0] and is an ancestor of the campaign tip (this check class catches the real Track-005 defect);
- CLAIMREF every source id referenced by claim matrices exists in the track's source audit (id-token extraction handles "S9 web lines 31-57" locator annotations; internal artifact references are skipped);
- ACCESS access fields present and explicit per record;
- CEILING final tracks must carry an explicit bounded ceiling;
- INDEX index covers exactly the eight track directories once each.

Result on the repaired campaign: `EIGHT_TRACK_R2_VALID`, 657 checks, 0 failures (git-bound checks against tip `ae777859`).

Negative fixtures (`tests/fixtures/eight_track_r2_validator/`, self-test mode):
1. `track005-misbinding` — frozen_commit ≠ checkpoint_commits[0] → GITBIND;
2. `fabricated-timestamps` — blank/non-ISO time fields → TIME_STATE;
3. `duplicate-source-chain` — claim cites source ids absent from the audit → CLAIMREF;
4. `open-obligation-final` — final track without explicit ceiling → CEILING;
5. `missing-calculation-outputs` — final-stage artifacts missing → STRUCTURE.

## C3. Independent replay (clean environment, offline)

Environment recorded per replay: clean clone, exact commands, input/output hashes in `REPAIR/replay-0*-result.json`.

| replay | method | result |
|---|---|---|
| Track 004 core electricity reconciliation | independent stdlib reimplementation recomputing Ember world-row deltas and IEA chart totals from the committed input CSVs only (no network) | **MATCH** — 12/12 comparisons, including clean +878.491 TWh vs demand +833.233 TWh, margin +45.258 TWh; first two mismatches were replayer scope errors (aggregate-row double counting, transposed chart), corrected and documented |
| Track 006 METR main estimate | clean-environment rerun of the committed script with pinned deps (Python 3.12, numpy 2.4.6, pandas 3.0.5, scipy 1.15.2, statsmodels 0.14.4 per requirements.lock.txt) on the committed input CSV | **MATCH** — 6/6 regenerated outputs byte-equal; headline estimate 0.1884 (CI95 0.0126–0.3948, n=246) reproduced; `official_regression.txt` is a committed artifact not regenerated by the script (recorded) |
| Track 003 heat (complex candidate) | clean rerun of the committed simulation-interval reanalysis on the committed MCC-HEWS public-output zip | **MATCH** — output identical. Selected over Track 001 because 003 commits a deterministic offline package with an explicit boundary (14-row public output means, not population-weighted EU totals) |
| Track 007 Swedish EV fire | independent denominator arithmetic recheck from committed audited numerator/denominator pairs | **ARITHMETIC_CONSISTENT** — Sweden 2024 recomputed 0.4541 ≈ published 0.45; Denmark recomputed rates differ from published by more than 5%, consistent with the committed exposure-timing warning |

**Track 007 source-identity disposition (per TASK: downgrade, never fill in):** the identity of the Swedish official source cannot be verified from the offline clean environment. The repair therefore does not assert verified provenance; the claim relying on that identity keeps its bounded status and is flagged `OFFICIAL_SOURCE_IDENTITY_NOT_VERIFIED_OFFLINE` in `REPAIR/replay-007-result.json` semantics: any downstream use that needs verified Swedish official identity must downgrade or re-verify with live access, never inherit an unverified identity.

## What this repair does not do

- no promotion of R2 reports into formal knowledge;
- no edit of original report prose or calculations except the versioned metadata corrections above;
- no closure of open obligations — the NOT_RECORDED markers and offline blockers remain open items for live-access follow-up;
- no change to R1 history, Task 114/115 artifacts, or any branch outside this child branch.
