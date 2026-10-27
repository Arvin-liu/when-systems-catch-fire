# Round 3 Checkpoint — Inner Research Loop, Tool Adapters, CLI/API Surface

**Round:** 3 / 7
**Parent (frozen Qwen Round 0):** `f4fe6faded65c16c98230ad34ca17e4374d59613`
**Round 3 deliverable commit:** `e0176d670fafd04e95029ad050f11cd878a73be5`
**Branch:** `workbuddy/task115-deep-research-queue-round1-7-takeover-r1-20260804`

## What Round 3 produced

The single research inner loop that the Round 2 queue drives, plus the
offline-safe tool adapters and the CLI/API invocation surface. The loop is
**crash-resumable** (checkpoint per episode) and **never self-approves** its
stop/report — finalization is driven only by the sufficiency evaluator, and
`CANDIDATE_COMPLETE` (the terminal it can reach) is intentionally **non-terminal**
by kernel design, requiring owner/gate review before any publish.

### `tools/deep_research/adapters.py` (NEW)
Offline-safe adapters that emit executor observations under the kernel contract
(no `self_approved` / `mark_episode_complete` / `claim_ceiling`):

- **Prompt-injection quarantine** — `detect_prompt_injection` flags directive
  injections; on detection a source is opened at `ABSTRACT_ONLY` with
  `provenance[-1].injection_detected = true` and
  `inspected_scope = "abstract_only_quarantined"` (full text is never trusted).
- **Exact source identity + inspected scope** — every open records
  `source_id`, `access_level` (NONE / ABSTRACT_ONLY / FULL_TEXT), and the exact
  `inspected_scope` provenance. `open` returns `DISCOVERED` only on a prior
  `search` (fail-closed).
- **Bounded hashed calculation** — `CalcAdapter` evaluates a strict AST subset
  (sum / min / max / abs / round over named numeric inputs), hashes inputs and
  output, and turns any disallowed call or error into an **observation** (no
  escape, no exception leak).
- `WebAdapter` / `PdfAdapter` / `AttachmentAdapter` / `CalcAdapter` +
  `build_default_adapters()`.

### `tools/deep_research/episode_loop.py` (NEW)
- **Claim / obligation operations missing from PR #190** — `add_claim`,
  `add_obligation`, `set_obligation_status` (kernel-vocabulary enforced;
  `claim_ceiling` is OWNER_ADJUDICATED and never raised by the loop).
- **`EpisodeController`** — `freeze_scope` → `plan_obligations` →
  `do_search` / `do_open` / `do_calc` → `challenge` → `revise` → `evaluate`
  → `finalize` → `checkpoint`. `run_plan` is a bounded driver that respects the
  kernel state machine (EVIDENCE_GATHERING → ANALYSIS → CHALLENGE → ANALYSIS →
  REVISION → terminal); on a CONTINUE decision with remaining actions it returns
  to gathering, and with **no remaining actions it stops honestly in BLOCKED**
  rather than spinning. A freshly frozen (`QUESTION_FROZEN`) episode enters
  gathering with no explicit obligations (queue-driven path).
- **`pause_episode` / `resume_episode` / `replay_events`** — crash-resumable.
- `_placeholder_sufficiency` — obligation-coverage placeholder; **Round 4
  replaces it** with the real hard-gate + sufficiency-vector stopping algorithm.
- `_safe_pack` / `DEFAULT_STRATEGY_PACK` — tolerate a non-kernel strategy-pack
  string instead of crashing the kernel's `assert_strategy_pack`.

### `tools/deep_research/cli.py` (NEW)
Pure ops (`inspect_episode`, `pause`, `resume`, `replay`, `claim_add`,
`obligation_add`, `obligation_set`, `queue_step`, `run_until_stop`) behind an
`argparse` surface (inspect / pause / resume / replay / claim-add /
obligation-add / obligation-set / episode / queue-step / run-until-stop).
Per the mandate, the executor never approves its own stop — `queue_step` only
ingests a result; campaign continuation is decided by `should_stop`.

### Tests (`tests/test_deep_research_round3.py`) — 18 tests, all PASS
- Adapter: injection detection, offline NONE, clean full-text, injection
  quarantined to ABSTRACT_ONLY, bounded calc hashing, disallowed call →
  observation error, no prohibited keys.
- Loop: freeze→plan transitions, sufficient run finalizes to CANDIDATE_COMPLETE
  (non-terminal by design), insufficient run stops honestly in BLOCKED, executor
  cannot self-approve, checkpoint written, pause/resume/replay.
- Claim/obligation ops via CLI.
- Queue step completes an item and records `checkpoint_commit`; CLI inspect +
  obligation-add.

## Test results
- `tests/test_deep_research_round1.py`: **19/19 PASS**
- `tests/test_deep_research_round2.py`: **24/24 PASS**
- `tests/test_deep_research_round3.py`: **18/18 PASS** (61/61 across R1–R3, no regression)
- `tools/deep_research/queue_runtime.py` smoke: OK
- `tests/test_research_os.py`: ALL CORE TESTS PASSED
- `tests/test_research_os_checkpoint_c.py`: ALL CHECKPOINT C TESTS PASSED
- `tests/test_research_os_resumability.py`: ALL RESUMABILITY/REPLAY TESTS PASSED

## Next
Round 4 — hard gates + sufficiency vector + stopping algorithm (replaces
`_placeholder_sufficiency`), then ≥24 offline anti-overfit / error-stop fixtures
(Round 5), the bounded live pilot (Round 6, only if stable + tools permit), and
docs + validation + Codex handoff + GPT review packet + stacked Draft PR
(Round 7).
