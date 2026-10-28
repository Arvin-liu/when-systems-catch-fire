# IGNITION-140 Step 05 — Reconciliation State Model

Status: `PASS`

The new `live-reconciliation-state-r1` contract separates an open evidence
obligation from a terminal unrecoverable observation. It has explicit states
for effect-unknown timeouts, observation-incomplete attempts, a conclusive
no-live-dispatch boundary, and an independently reconciled record.

The contract intentionally carries two different facts:

- `process_observation` can be `NO_LIVE_PROCESS_OBSERVED` when the public
  dispatch boundary is conclusive;
- `external_effect_knowledge` remains `UNKNOWN` unless a later independent
  validator establishes a stronger fact. This step never uses a terminal
  state to claim success, failure, or no external effect.

`validated_completion_eligible` is hard-coded false in reconciliation states.
Reconciliation closes the obligation to keep searching for evidence; it does
not create a completion result. The historical attempt ledger is not edited.

Evidence: five state-machine tests passed with zero failures, errors, or
skips, including negative gates for known-effect and validated-completion
upgrades and a recoverable-evidence gate that remains open.

Claim ceiling: repository-local reconciliation state machine only. No external
success, failure, no-effect, production readiness, Owner acceptance, or
epistemic upgrade is inferred.
