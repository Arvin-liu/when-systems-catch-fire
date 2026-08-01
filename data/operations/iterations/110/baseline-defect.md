# Task 110 — §4 Frozen Baseline Defect

> Purpose: preserve, as auditable evidence, the stale-completion-state defect that
> task 109's planner exposed. This file does NOT modify any task-109 artifact.
> Task-109 outputs remain immutable historical evidence (see `supersession` links).

## Defect class

`STALE_COMPLETION_STATE_CAUSING_DUPLICATE_RECOMMENDATION`

The task-109 iteration planner (`tools/iteration_planner/planner.py`) ranks candidates
purely by a frozen priority model over the **candidate portfolio's `selection_decision`**
field, with **no lifecycle-state reconciliation**. When a candidate's underlying bounded
obligation has already been completed by an earlier task, the planner still ranks it as a
live next iteration. A deterministic recommendation of already-completed work is still an
incorrect recommendation.

## Concrete manifestation (verified from remote truth)

### C-01 — recommended by 109, already completed by 103

- Task-109 recommendation: `data/operations/iterations/109/next_iteration_recommendation.md`
  states `canonical_id: C-01`, `claim_id: SRC-REGISTRY-104-METADATA`, `aggregate_score: 73.2`,
  `source: data/external-research/104-source-registry.jsonl`. Planner baseline re-run confirms
  `recommended=C-01` (candidates=71, score 73.20).
- Candidate portfolio (authoritative schedulable-state source the planner reads):
  `evidence-program/registry/candidate-portfolio.jsonl` line 1 → `C-01` `selection_decision=PRIMARY`.
- Authoritative completion: Task 103 executed and adjudicated this exact obligation.
  - Run: `evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION/`
  - `run-manifest.json`: `run_id=IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION-RUN-1`,
    `preregistration_ref=PREREG-103-R1-CROSSREF`, `preregistration_commit=a4d13a69acea9bcc1480d7dd383929d46813c2f5`.
  - `result-adjudication.json`: `outcome=SUPPORTED_WITHIN_SCOPE`,
    `verification_match_rate=1.0`, `resolution_rate=1.0`, `title_match_rate=1.0`,
    `year_match_rate=1.0`, `retraction_signal_count=0`, `full_match_count=117`.
  - This is the Crossref verification of the same 117 source records claimed by C-01.

### C-04 — still "DEFERRED" in portfolio, already completed by 105

- Candidate portfolio line 4 → `C-04` `claim_id=FUNCTION-OS-V02-CORRECTNESS`,
  `selection_decision=DEFERRED`, `deferral_reason: "Needs a constructed reference oracle and
  more expertise; chosen as a later pilot, not this round."`
- Authoritative completion: Task 105 executed and adjudicated this bounded obligation.
  - Run: `function-os-candidate/v0.2/benchmark/`
  - `PREREGISTRATION.md`: control commit `d2167c3472e32c0c053c7413c03219cac0389dcc`,
    target implementation commit `16f640045b3dc9d411f015a51e45de07299d31fc`
    (origin/main, PR #160 merge = task-104 terminal), prereg commit `5d664686474ef4457e89127c53e2293a61028094`.
  - `RESULTS.json`: `overall_verdict=SUPPORTED_WITHIN_BOUNDED_DOMAIN`,
    `critical_violations=0`, `git_head=1314ba807415b3945bc6784689af5a5559e66fc9`,
    `target_commit=16f640045b3dc9d411f015a51e45de07299d31fc`,
    `prereg_commit=5d664686…`, `prereg_ancestor_of_head=true`.
  - `CLAIM_VERDICTS.json`: 6/7 claims `SUPPORTED_WITHIN_BOUNDED_DOMAIN`
    (1 `PENDING_REPLAY` for DETERMINISTIC_REPRODUCIBILITY), `overall_verdict=SUPPORTED_WITHIN_BOUNDED_DOMAIN`.

### C-03 — the genuinely unfinished pilot (authorized for 110)

- Candidate portfolio line 3 → `C-03` `claim_id=DOI-OPENALEX-CROSS-CHECK`,
  `selection_decision=RESERVE`, `ranking_score=0.74`. No completion record exists.
- Authorized as the substantive pilot of task 110 (contract §8).

## Why it is a correctness defect, not a cosmetic one

- `planner.py:read_candidate_portfolio()` sets `c["current_status"] = d.get("selection_decision", …)`
  and the ranking never consults lifecycle evidence (task FINAL_STATE, evidence-program
  run adjudications, function-os benchmark verdicts, terminal tags).
- Therefore a completed candidate (`C-01` → 103 `SUPPORTED_WITHIN_SCOPE`) is ranked #1 and
  recommended as the next iteration; a completed candidate (`C-04` → 105
  `SUPPORTED_WITHIN_BOUNDED_DOMAIN`) remains schedulable as `DEFERRED`.
- The fix (§5) must be **generic** (governed-identifier reconciliation) and must NOT
  hard-code an exclusion list, must NOT erase the 109 recommendation, and must preserve
  completed items in a historical register.

## Exact source digests (SHA-256) — recorded for audit

| Artifact | SHA-256 |
|----------|---------|
| `data/operations/iterations/109/next_iteration_recommendation.md` | `373cdc22897a83aad4a522b4dec3217352fcfd62dbae596f721b9f8482f303f2` |
| `data/operations/iterations/109/ranked_queue.json` | `86faf0ccf3e63cdcb516574307ff86009c2400a40a5c46d30e984c7afa810fb7` |
| `data/operations/iterations/109/candidate_inventory.json` | `66a6a05cdcfa23c87e31bd69a47560215a8a80b4574fe15a5843e01b61c5cc82` |
| `evidence-program/registry/candidate-portfolio.jsonl` | `5cf1bdc7a7b35a32ad9d32bf2176c886c561c205f20c8617b6402902716b5cbd` |
| `evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION/result-adjudication.json` | `083db73165182b4670b38a77e2b61528a25fe022d6c575bc7d9f00d6e98015ea` |
| `evidence-program/runs/IGNITION-EVIDENCE-PILOT-R1-CROSSREF-DOI-VERIFICATION/run-manifest.json` | `ad04c66b5cc1b99f93d633446e87c889431700f42aed0c3a41a36c27d5615cd0` |
| `function-os-candidate/v0.2/benchmark/CLAIM_VERDICTS.json` | `48901348c508d9bf20bab7159070d1f7acf9f43753e79f2cfb885a9a6ad0ca7c` |
| `function-os-candidate/v0.2/benchmark/PREREGISTRATION.md` | `ccde93ae66d569b4879a231eb2a5be5e5bd2a3a24eaba3a26c1aa07f519368d1` |
| `function-os-candidate/v0.2/benchmark/RESULTS.json` | `806845a33b4ea04b41bde68e6133399fc84405ea973ec07f070a163726cbd869` |

## Lifecycle-state anchoring commits (ancestors of `origin/main`)

- Task 103 preregistration anchor: `a4d13a69acea9bcc1480d7dd383929d46813c2f5`
- Task 105 preregistration anchor: `5d664686474ef4457e89127c53e2293a61028094`
- Task 105 target implementation: `16f640045b3dc9d411f015a51e45de07299d31fc` (PR #160 = task-104 terminal)
- Task-110 branch base (== predecessor terminalization merge): `0bbd31a82406e1922509aa052885d214b6efff85`

## Supersession / immutability note

- Task-109 `next_iteration_recommendation.md`, `ranked_queue.json`,
  `candidate_inventory.json` are **immutable historical evidence** of the defect.
- This file (`110/baseline-defect.md`) is a NEW task-110 projection. The corrected queue
  (§7) is published separately as `110/corrected_queue.json` + `110/queue_diff.md`.
- No task-109 file is modified, renamed, or deleted.
