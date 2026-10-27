# Research OS — Review / Stop / Escalation Gates (Checkpoint C)

This document specifies the seven independent review gates and the deterministic
stop / escalation logic of the Pointfire Research Executive OS (Task 115 Draft
candidate). It is the human/agent-facing companion to `tools/research_os/gates.py`.

The gates consume a structured episode (`kernel.new_episode`) and a diagnosis
from the Checkpoint B deterministic engine (`diagnosis.diagnose`). They are
**necessary but not sufficient**: passing all gates does not by itself authorize
publication or completion. Owner / GPT acceptance (gate 7) remains required, and
the publication layer's claim-ceiling constraint still applies.

## 1. The seven gates

| # | Gate | Checks | Passes when |
|---|------|--------|-------------|
| 1 | `source_provenance` | every `evidence_obligations` entry | all obligations `SATISFIED` or `NOT_APPLICABLE` |
| 2 | `method_calculation` | diagnosis findings | no `NUMERIC_CLAIM_NOT_RECOMPUTED` finding |
| 3 | `source_dependence` | diagnosis findings | no `SOURCE_DEPENDENCE_HIGH` finding |
| 4 | `adversarial_claim` | diagnosis findings | no `ADVERSARIAL_REVIEW_MISSING` finding |
| 5 | `claim_ceiling` | diagnosis findings | no `CLAIM_EXCEEDS_EVIDENCE` finding |
| 6 | `high_stakes_escalation` | `high_stakes` flag + state | not high-stakes, **or** state `ESCALATED_TO_GPT_OWNER` |
| 7 | `owner_gpt_acceptance` | episode state | state in `CANDIDATE_COMPLETE` / `ESCALATED_TO_GPT_OWNER` |

Gate 1 reads the obligation graph directly. Gates 2–5 read the diagnosis `findings`
emitted by the deterministic engine (each finding carries a gap code from
`data/research-os/gap-codes.json`). Gates 6–7 read episode-level control fields.

`evaluate_gates(ep, diagnosis)` returns the per-gate results, an `all_gates_pass`
boolean, and the standing note that acceptance remains required. `all_gates_pass`
is true only when the episode has already reached `CANDIDATE_COMPLETE` or
`ESCALATED_TO_GPT_OWNER` with all substantive gates satisfied.

## 2. Stop states (required)

The OS must be able to stop at exactly one of these conditions. A stop is a
deliberate, evidence-conditioned transition — never a function of report length,
word count, elapsed time or round count alone (enforced by the state kernel).

1. **Sufficient bounded result** — `CANDIDATE_COMPLETE` after all substantive
   gates pass and external review recorded; ceiling within the pack's
   `max_claim_ceiling`.
2. **Reliable null / insufficient evidence** — `INSUFFICIENT_EVIDENCE_COMPLETE`
   via `stop` after a genuine, searched negative result or inaccessible primary
   data/code. This is an honest-null conclusion, not a positive finding.
3. **Verifiable source / data blocker** — when primary source, raw data or
   analysis code is demonstrably inaccessible after search; recorded as
   `INSUFFICIENT_EVIDENCE_COMPLETE` or `BLOCKED`.
4. **No information gain** — `NO_INFORMATION_GAIN` diagnosis → `PAUSE_AND_CHECKPOINT`
   (resumable) or `STOP_WITH_INSUFFICIENT_EVIDENCE`.
5. **Budget boundary with resumable checkpoint** — `PAUSED_RESUMABLE` via
   `pause`; the episode is fully resumable from its append-only event log.
6. **Mandatory human escalation** — `ESCALATE_TO_GPT_OWNER` for value, high-stakes
   or exceptional adjudication; the executor cannot self-approve.

## 3. Escalation conditions

Escalation is forced (recommendation `ESCALATE`) in these cases, independent of
other gates:

- Any integrity / claim-ceiling finding among:
  `CLAIM_EXCEEDS_EVIDENCE`, `PREMATURE_COMPLETION`, `UNAUTHORIZED_EARLY_CLOSEOUT`,
  `READING_TIME_SCOPE_INCONSISTENT`, `TIMESTAMP_BATCH_NOT_PROOF_OF_READING`,
  `PRIMARY_SOURCE_MISSING`.
- High-stakes episode not yet `ESCALATED_TO_GPT_OWNER` (gate 6 fails).
- `ATTRACTOR_LOOP_RISK` detected by the Q13 IterationDelta consumer.

The strategy packs (`data/research-os/strategy-packs/*.json`) additionally carry
per-pack `escalation_conditions` that bind trigger gaps to `GPT_OWNER`; these are
the discipline-specific instances of the general rule above.

## 4. Recommendation actions

`gates.recommend(ep, diagnosis, gates_result)` returns one of:

- `ESCALATE` — integrity/claim/high-stakes failure; route to GPT/owner.
- `PAUSE_CHECKPOINT` — `NO_INFORMATION_GAIN`; pause and write a resumable checkpoint.
- `STOP_INSUFFICIENT` — reliable null / inaccessible source after search.
- `READY_FOR_ACCEPTANCE` — all gates pass and episode at `CANDIDATE_COMPLETE` /
  `ESCALATED_TO_GPT_OWNER`; await owner/GPT acceptance.
- `DONE_INSUFFICIENT` — already at `INSUFFICIENT_EVIDENCE_COMPLETE`.
- `CONTINUE` — gates failing for non-escalation reasons; address open
  obligations / findings and keep working.

## 5. CLI

```
research-os review --episode <path>
```

Emits `{episode_id, gates{...}, all_gates_pass, note, recommendation}`.

## 6. Phase boundary (reminder)

This is a Draft-PR candidate. The gates and stop/escalation logic are not
empirically calibrated (R2 pending). This phase does **not** merge, mark ready,
terminalize, create `FINAL_STATE`, or create Task 116. The PR carries the marker
`R2_EMPIRICAL_CALIBRATION_PENDING`.
