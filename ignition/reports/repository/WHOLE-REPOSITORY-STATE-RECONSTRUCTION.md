# Whole-Repository State Reconstruction — Line D

Campaign: `POINTFIRE-QWEN38MAX-WHOLE-REPOSITORY-STATE-RECONSTRUCTION-CANDIDATE-CONVERGENCE-GLOBAL-INVARIANT-CLOSURE-R1-20260803`
Branch: `qwen38max/whole-repo-state-convergence-r1-20260803` (from exact formal main `cac043d4`)
Machine artifacts: `data/operations/repository-state-ledger.json`, `data/operations/candidate-lineage-registry.json`, `data/operations/global-invariant-results.json`

## Method

Acceptance is never inferred from timestamp, branch existence, PR openness or file name. State derives from three authoritative evidence classes only:

1. the merged iteration ledger (`data/operations/merged-iteration-ledger.jsonl`) — tasks 104/105 `TERMINAL_SUCCESS`, 106 `PR_OPEN`;
2. iteration terminal tags `ignition/iterations/<n>/terminal-r1` — present for 106–114;
3. `FINAL_STATE` records under `data/operations/iterations/` — explicit `TERMINAL_SUCCESS` for 108, 111–114; dialect variants for 109/110 (terminalization fields + tag present, no top-level `terminal_state`; recorded as such, not reinterpreted).

The current-truth projection (`current_accepted_iteration: 114`) is treated as a generated projection whose input is the terminal evidence above; INV-02/INV-03 verify agreement rather than trusting it.

## Reconstructed state (at main `cac043d4`)

- Accepted current: iteration **114** (language–thought logic plane pilot + current-work repair), tag `ignition/iterations/114/terminal-r1`.
- Accepted historical / merged: iterations 104–113, contiguous chain, no gaps (INV-03).
- Open candidate surface: **81 open PRs, all Draft** — 13 base-`main` draft candidates, 68 stacked repair/candidate PRs, grouped into **16 lineage families** by head/base identity. Largest chains: the R3 semantic-evaluator stack (#109→#122 lineage), the repair-r2 stack (#99→#108), the agent i1 stack (#65→#81), the ARR chain (#120→#132), and old records drafts (#3, #5, #16–#21, #31, #32).
- Research candidates: `research/overnight-public-evidence-20260803-r1` (R1, failure evidence) and `research/eight-track-deep-validation-20260803-r2` (R2, candidate research only) — category `RESEARCH_CANDIDATE_NOT_FORMAL_KNOWLEDGE`; neither is represented in accepted state (INV-05).
- Scale: 215 remote branches, 94 tags at snapshot time.

## Deterministic machinery

- `tools/operations/build_repository_state_ledger.py` — rebuilds ledger + lineage from committed inputs; INV-11 proves byte-identical regeneration.
- `tools/operations/validate_global_invariants.py` — 11 invariants, 5 negative fixtures; verdict at this head: `GLOBAL_INVARIANTS_CLOSED` (see `GLOBAL-INVARIANT-CLOSURE.md`).
- Schemas under `data/operations/schemas/` for all three machine artifacts.

## What is explicitly NOT concluded

- No open PR, candidate branch or research line is accepted, current or merge-ready by virtue of appearing here.
- Task 115 remains non-terminal (Draft-PR phase); PR #189 and R2 remain candidates under stacked repair.
- Old record drafts (#3–#32 era) are surfaced as `UNKNOWN_REQUIRES_OWNER_ADJUDICATION` where rules cannot decide supersession; nothing is closed or edited.
