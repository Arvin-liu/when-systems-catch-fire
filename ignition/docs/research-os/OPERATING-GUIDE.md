# Research OS — Operating Guide (Checkpoint C)

A practical guide for humans and agents operating the Pointfire Research
Executive OS (Task 115 Draft candidate). It is the control system that keeps
asking: *what is epistemically missing, what is the next highest-value action,
and should we continue, branch, stop or escalate?*

This guide assumes you have read `RESEARCH-OS-ARCHITECTURE.md` and
`REVIEW-GATES.md`. It focuses on **how to drive the loop**, not on internals.

## 1. What the OS is and is not

The OS is **not** L7, not a truth authority, not an autonomous permission to
publish, and not a replacement for Function OS / Q12 / Q13 / Foundation / Charter
Gate / language–thought logic. It is the continuous controller spanning L0–L6.

Its deterministic core runs **without an LLM**. An LLM may supply optional
candidate action proposals, but it is never the sole scheduler or validator.

## 2. The control loop

```
OBSERVE -> DIAGNOSE -> CHOOSE -> DISPATCH -> INSPECT -> UPDATE -> STOP/ESCALATE
```

- **OBSERVE** — read live episode state and L0–L6.
- **DIAGNOSE** — deterministic gap engine over structured state (`diagnose`).
- **CHOOSE** — inspectable scheduler over the 24-action vocabulary (`plan`).
- **DISPATCH** — Executor Adapter Contract → Function OS / agent (`dispatch-spec`).
- **INSPECT** — executor return; **no self-approval** (`record-result`).
- **UPDATE** — append-only event log + obligation graph.
- **STOP / ESCALATE** — review gates, budget, human judgment (`review`, `stop`, `pause`).

A report file, word count, elapsed time or round count **never** alone causes a
completion transition. Completion requires satisfied obligations and passed
review gates.

## 3. CLI workflow

```
# 1. Create + (optionally) freeze the question
research-os init --episode ep.json --id ep1 --question "..." \
    --type recon --pack QUANTITATIVE_DATA_RECONCILIATION --freeze

# 2. Diagnose the current state
research-os diagnose --episode ep.json

# 3. Choose the next action (inspectable rationale)
research-os plan --episode ep.json

# 4. Build the bounded spec an executor consumes
research-os dispatch-spec --episode ep.json --action RECOMPUTE_RESULT --out spec.json

# 5. Executor returns; validate + record (no self-approval allowed)
research-os record-result --episode ep.json --action RECOMPUTE_RESULT --result-file ret.json

# 6. Review gates + stop/escalation recommendation
research-os review --episode ep.json

# Pause / resume / stop / reopen
research-os pause   --episode ep.json
research-os resume  --episode ep.json
research-os stop    --episode ep.json --reason "primary data inaccessible"
research-os reopen  --episode ep.json
```

State transitions are validated against `data/research-os/episode-states.json`.
`CANDIDATE_COMPLETE` is **not** a success terminal; it is a candidate awaiting
owner / GPT acceptance.

## 4. Choosing a strategy pack

Pick the pack that matches the research shape (see `templates/research-os/README.md`
for the eight codes). The pack sets `max_claim_ceiling` and the discipline-specific
escalation/stop conditions. The pack is validated at `init` time against
`data/research-os/strategy-packs/`; an unknown pack is rejected.

## 5. Interpreting the gates

Run `review`. The seven gates (`REVIEW-GATES.md` §1) report `passed` per gate and
an `all_gates_pass` flag. Remember:

- `all_gates_pass == true` only when the episode is at `CANDIDATE_COMPLETE` or
  `ESCALATED_TO_GPT_OWNER` **and** all substantive gates pass.
- Passing is **necessary but not sufficient**. Owner / GPT acceptance (gate 7)
  remains required, and the publication layer's claim-ceiling constraint still
  applies.

## 6. When to escalate

Escalate (recommendation `ESCALATE`) when any of these hold:

- Integrity / claim-ceiling finding: `CLAIM_EXCEEDS_EVIDENCE`,
  `PREMATURE_COMPLETION`, `UNAUTHORIZED_EARLY_CLOSEOUT`,
  `READING_TIME_SCOPE_INCONSISTENT`, `TIMESTAMP_BATCH_NOT_PROOF_OF_READING`,
  `PRIMARY_SOURCE_MISSING`.
- High-stakes episode not yet `ESCALATED_TO_GPT_OWNER`.
- `ATTRACTOR_LOOP_RISK` detected.

Use `research-os stop` for a reliable null / insufficient-evidence conclusion, and
`research-os pause` at a budget boundary to write a resumable checkpoint.

## 7. Obligation and claim ceilings

Each material claim carries obligations from the 12 classes. A
`WAIVED_WITH_REASON` obligation can **never** raise a claim ceiling. Assertive
ceilings (`QUALIFIED`, `BOUNDED_STRONG`) require satisfied obligations; the gate
`claim_ceiling` flags `CLAIM_EXCEEDS_EVIDENCE` otherwise.

## 8. Phase boundary (read before acting on this OS)

This is a **Draft-PR candidate**. It carries the marker
`R2_EMPIRICAL_CALIBRATION_PENDING`. The phase:

- does **not** merge into `main`;
- does **not** mark the PR ready;
- does **not** terminalize the work or create `FINAL_STATE`;
- does **not** create Task 116.

R1 is failure evidence; R2 is a human-authored comparison target, not empirical
proof. A later same-number continuation absorbs R2 results and performs final
adjudication.
