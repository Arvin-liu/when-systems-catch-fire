# Deep Research Capability — Stop Algorithm (Transparent, Non-Scalar)

The stopping algorithm (Round 4) deliberately avoids authorizing completion
with a single scalar score. It enforces **hard gates** and computes a
**multidimensional sufficiency vector**; only when every gate passes AND every
vector dimension is met may an episode be marked a sufficient candidate.

## 1. Hard gates (`SufficiencyEvaluator.hard_gates`)

Any failing gate blocks `STOP_SUFFICIENT_CANDIDATE`. Each gate is inspectable.

| # | Gate | Blocks when |
|---|------|-------------|
| 1 | `scope_frozen` | no frozen `brief` (scope not frozen) |
| 2 | `unsupported_material_claim` | a material claim with zero gathered observations |
| 3 | `open_burden_bearing_severe_obligation` | an OPEN `HIGH`/`CRITICAL` obligation |
| 4 | `unresolved_source_identity` | a source with `NONE` access or no `inspected_scope` |
| 5 | `citation_attribution_mismatch` | an `ABSTRACT_ONLY` source behind a material claim |
| 6 | `false_independence_same_family` | material claim backed by ≤1 source family |
| 7 | `high_stakes_evidence_route_failure` | failed required calc/tool behind a material claim |
| 8 | `unresolved_prompt_injection` | provenance contamination / injection detected |
| 9 | `blocked_evidence_route` | a load-bearing source with `NONE` access |
| 10 | `missing_required_calc_without_ceiling_reduction` | quantitative claim lacking recomputation and ceiling reduction |

## 2. Sufficiency vector (`sufficiency_vector`)

Eight independent dimensions, each `{value, threshold, met}`; all must be `met`.

| Dimension | Meaning |
|-----------|---------|
| `obligation_coverage` | fraction of evidence obligations `SATISFIED` |
| `claim_support_faithfulness` | material claims with ≥1 gathered observation |
| `independent_family_coverage` | ≥2 independent source families when material claims exist |
| `contrary_null_coverage` | contrary/null evidence explicitly sought |
| `method_data_recomputation_coverage` | required recomputations succeeded (no errors) |
| `claim_ceiling_stability` | no claim at `NOT_ASSERTED` ceiling |
| `unresolved_gap_severity` | no open `HIGH`/`CRITICAL` obligation (severity gap = 0) |
| `marginal_information_gain` | at least one observation (non-zero information gain) |

Thresholds are **registry-driven** by strategy pack (`_SUFFICIENT_THRESHOLDS`),
default `SYSTEMATIC_EVIDENCE_SYNTHESIS`; a custom threshold dict can be passed
to the evaluator.

## 3. Decision mapping (`evaluate`)

```
if any hard gate failed:
    if {unresolved_prompt_injection, high_stakes_evidence_route_failure}:
        -> ESCALATE_GPT_OWNER
    elif "blocked_evidence_route" in failed:
        -> BLOCKED_WITH_EVIDENCE
    else:
        -> CONTINUE_RESEARCH
elif all vector dimensions met:
    -> STOP_SUFFICIENT_CANDIDATE
elif marginal_information_gain == 0:
    -> STOP_INSUFFICIENT_EVIDENCE
else:
    -> CONTINUE_RESEARCH
```

No scalar score alone authorizes completion; the loop only finalizes to a
terminal state when the evaluator returns a stop decision.

## 4. Queue campaign stop conditions (`queue_runtime.should_stop`)

Only these **seven** conditions stop the campaign (Round 2). A long report,
many URLs, or an executor `success` are explicitly **excluded** — they can
never stop the queue.

1. `OWNER_STOP`
2. `DEADLINE` (past)
3. `MAX_EPISODES` (completions ≥ cap)
4. `BUDGET` (cost ≥ cap)
5. `QUEUE_EMPTY` (only if `queue_empty_stops`)
6. `SAFETY_BLOCKER` (a `BLOCKED` item, only if `safety_blocker_stops`)
7. `LOW_INFORMATION` (consecutive low-info ≥ threshold)

Episode-result ingestion (`ingest_result`) is idempotent and never triggers a
stop; continuation is decided solely by `should_stop` against campaign state.
