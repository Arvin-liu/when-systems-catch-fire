# IGNITION-20261001-229-R2-A1 Closeout

EXPERIMENT_ID=IGNITION-20261001-229-R2-A1
ANALYSIS_CLASS=SECONDARY_SALVAGE_ANALYSIS_OF_PREEXISTING_R1_FROZEN_SUCCESSOR_DATASET
R1_PRIMARY_STATUS_REMAINS=STOPPED_PROTOCOL_DEVIATION_NO_SCIENTIFIC_RESULT
R2_TERMINAL_STATUS_REMAINS=TASK229_R2_SANITIZER_CONTRACT_NOT_ESTABLISHED
NEW_SUCCESSOR_SESSIONS=0

A1 synthetic contract gate: PASS. The new independently authored builder and checker passed the frozen synthetic suite before semantic R1 access.

A1 packet sanitization: PASS, 54/54 packets built and independently checked; zero deny-token matches. The R1 raw outputs were not added to the A1 commit.

Fresh blind evaluators: PASS, two distinct ephemeral threads, 54/54 exact response/case rows each, both outputs schema-valid, and no tool-call item events. Requested model/effort: gpt-6-astra / medium. The CLI did not expose observed backend/effort values.

A1 recomputation terminal: TASK229_R2_A1_RECOMPUTE_MISMATCH. The byte-identical original recompute.py (SHA-256 `2a81a493b2d40cde023b4017a72c3aa7dfe45dee96fc06e223639fb082902b54`) was invoked twice against the same frozen input. Both invocations exited 1 with the same `FileNotFoundError` for the historical Task228 policy path resolved beneath the wrong execution root. Neither run produced a result file, so no endpoint markers or A1 analytical result are available. No retry, script edit, threshold change, or replacement run was made.

Original endpoint layers, each without an emitted marker because recomputation produced no output:
- `interface_execution`
- `reference_target_compatibility`
- `incremental_policy_effect`

ENDPOINT_MARKERS=NOT_PRODUCED
NEXT_DIRECTION=UNASSIGNED_RECOMPUTE_TERMINAL
TASK230_AUTO_LAUNCH=false

The result ceiling remains a bounded secondary analysis of the pre-existing R1 dataset; no primary scientific result is claimed. PR #242 remains Open + Draft + Unmerged.
