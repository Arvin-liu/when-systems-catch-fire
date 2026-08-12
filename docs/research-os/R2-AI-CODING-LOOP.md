# R2 Bounded Loop — AI-Coding-Productivity Question (Task 115 Line A)

Status: **CANDIDATE (Draft phase)** — `R2_EMPIRICAL_CALIBRATION_PENDING`

This is one real bounded Research OS loop on the R1 round-006 question, run
stepwise `observe → diagnose → choose → dispatch → inspect → update` with every
CLI step in a separate OS process. It demonstrates the control loop and the
blocker rule: a verified access blocker leaves the obligation open-class and
never raises the claim ceiling.

## Question

生成式 AI 是否在真实软件工程中提高开发者生产率，还是只在简单受控任务或自报感受中显示加速？

Episode `r2-loop-ai-coding-001`, strategy pack `ENGINEERING_BENCHMARK`,
budgets `{human_attention_hours: 2, tool_calls: 20}`.

## Step record

1. **init + freeze** (process 1): `research-os init --freeze`; state `INTAKE → QUESTION_FROZEN`.
2. **observe** (process 2): executor return importing R1 round-006 telemetry from the locked tip (`COMMITTED_FULL_TEXT`): elapsed 0.0364 h for 7 sources, identical `accessed_at`, no recomputation, verdict `CONTESTED`; no raw benchmark data committed.
3. **claim + obligation registration** (process 2b): one claim at ceiling `SPECULATIVE`; the pack's 8 required obligations registered — `PRIMARY_SOURCE` at `PARTIAL` (URLs identified, access unverified), all others `OPEN`. No waiver requested. Known limitation: the CLI has no claim/obligation subcommand yet; the kernel API was used directly and this step is recorded in provenance.
4. **diagnose** (process 3): 9 findings — `PRIMARY_SOURCE_MISSING`, `FULL_TEXT_MISSING`, `NUMERIC_CLAIM_NOT_RECOMPUTED`, `RAW_DATA_OR_CODE_MISSING`, `SOURCE_DEPENDENCE_HIGH`, `OUTCOME_DEFINITION_CONFLICT`, `POPULATION_SCOPE_MISMATCH`, `NEGATIVE_EVIDENCE_NOT_SEARCHED`, `HUMAN_JUDGMENT_REQUIRED`.
5. **choose** (process 4): deterministic scheduler selects `ESCALATE_TO_GPT_OWNER` (forced by `HUMAN_JUDGMENT_REQUIRED`); ranked bounded alternatives: `SEARCH_PRIMARY_SOURCE`, `BRANCH_QUESTION`, `FREEZE_OR_NARROW_QUESTION`, `REPRODUCE_ANALYSIS`, `COMPARE_POPULATIONS_OR_JURISDICTIONS`. The ranked #1 bounded investigation is dispatched before escalation is handed off, with the escalation decision recorded.
6. **dispatch** (process 5): `dispatch-spec` for `SEARCH_PRIMARY_SOURCE` written to `dispatch-spec-search-primary-source.json` (bounded objective, required inputs, expected return schema, prohibited claims, budget/stop condition).
7. **executor return / inspect** (process 6): the executor (this campaign, clean offline clone, no external fetch) returns an honest `SOURCE_ACCESS_BLOCKER` — METR 2025 primary materials and the GitHub experiment data cannot be verified offline; `validate_return` accepts the return (no self-approval keys present) and re-diagnoses (9 findings persist).
8. **update** (process 7): `PRIMARY_SOURCE` obligation → `BLOCKED_WITH_EVIDENCE` with the blocker evidence attached. Ceiling untouched.
9. **inspect gates** (process 8): `review` → `all_gates_pass: false` (source_provenance, method_calculation, source_dependence, owner_gpt_acceptance fail); recommendation `ESCALATE` — `integrity/claim failure: PRIMARY_SOURCE_MISSING`.
10. **pause** (process 9): state → `PAUSED_RESUMABLE` (paused_from `QUESTION_FROZEN`).
11. **resume** (process 10, a NEW process): state → `QUESTION_FROZEN`, exactly the paused-from state. Cross-process persistence proven by the event log (16 events, payload hashes recorded).

Machine artifacts: `episode.json`, `LOOP-LOG.md`, `dispatch-spec-search-primary-source.json` in this directory.

## Loop verdict

The OS did not complete the episode. It escalated to GPT/owner and left the
episode resumable with a blocked primary-source obligation. The claim ceiling
remains `SPECULATIVE`. This is the intended behavior: source/method access
blockers stay open obligations; they never become silent completion, and a
waived or blocked obligation can never raise the claim ceiling.

## Defects found and repaired in the recovered OS during this loop

Two real defects in the restored Checkpoint C code were exposed by running the
loop and repaired minimally (documented in commit messages):

1. `adapters.consume_iteration_delta` used `setdefault`, silently dropping the
   delta because the kernel initializes `information_delta` to `None`.
2. `cli resume` compared the paused-from state against its own successor list,
   so resume could never return to `paused_from`; it now checks the successors
   of `PAUSED_RESUMABLE`.

## What would unblock this episode

Verified access to the METR 2025 time-study primary materials (or an
equivalent raw per-task timing dataset), independent recomputation of the
headline productivity figures, and adversarial review of the measurement
construct — after which the obligation graph, not elapsed time or report
length, decides whether a bounded result exists.
