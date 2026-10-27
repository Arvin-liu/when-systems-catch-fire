# Research OS Templates

Human/agent-facing templates for the Pointfire Research Executive OS (Task 115
Draft candidate). These are authored against the live structures produced by the
Checkpoint B/C engine; the authoritative contracts live in `tools/research_os/`
and `data/research-os/`.

## Files

| File | Purpose | Source of truth |
|------|---------|-----------------|
| `episode-template.json` | Hand-author / inspect an episode. Mirrors `kernel.new_episode` output. | `tools/research_os/kernel.py`, `data/research-os/episode-states.json`, obligation graph |
| `dispatch-spec-template.json` | Shows the spec the OS sends to executors. | `tools/research_os/executor_contract.build_dispatch_spec` |
| `receipt-audit-packet-template.json` | Audit receipt emitted by `review` (gates + obligation tally). | `tools/research_os/gates.evaluate_gates` / `recommend`, `cli.cmd_review` |

## How to use

1. **Create an episode** — prefer the CLI; it validates the strategy pack and
   seeds every field:

   ```
   research-os init --episode <path> --id <id> --question "<q>" \
       --type <type> --pack <one of 8 pack codes> [--freeze]
   ```

   Use `episode-template.json` only when you must author or inspect by hand.

2. **Dispatch an action** — `research-os plan` selects an action; `research-os
   dispatch-spec --action <code>` emits the bounded spec an executor consumes.
   `dispatch-spec-template.json` documents that spec's shape.

3. **Record a result** — the executor returns the `research-os/executor-return/0.1`
   contract (no self-approval). `research-os record-result` validates and appends.

4. **Review** — `research-os review --episode <path>` emits the gates result and a
   stop/escalation recommendation. `receipt-audit-packet-template.json` shows the
   audit-receipt shape.

## Strategy packs

The `strategy_pack` field must be one of the eight codes in
`data/research-os/strategy-packs/`:

- `QUANTITATIVE_DATA_RECONCILIATION`
- `RANDOMIZED_CLINICAL_EVIDENCE`
- `OBSERVATIONAL_CAUSALITY`
- `POLICY_EFFECT_EVALUATION`
- `ENGINEERING_BENCHMARK`
- `SYSTEMATIC_EVIDENCE_SYNTHESIS`
- `HISTORICAL_SOURCE_ADJUDICATION`
- `PUBLIC_CLAIM_FACT_CHECK`

Each pack declares required obligations, typical gaps, mandatory calculations,
common failure modes, a `max_claim_ceiling`, escalation conditions and stop
criteria.

## Phase boundary

Draft-PR candidate. `R2_EMPIRICAL_CALIBRATION_PENDING`. Does not merge, mark
ready, terminalize, create `FINAL_STATE`, or create Task 116.
