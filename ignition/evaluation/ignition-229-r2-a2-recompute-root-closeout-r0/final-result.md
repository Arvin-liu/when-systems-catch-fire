# IGNITION-20261002-229-R2-A2 — Recompute Root & Repository Closeout

## Secondary analysis

`EXPERIMENT_ID=IGNITION-20261002-229-R2-A2`
`ANALYSIS_CLASS=SECONDARY_SALVAGE_ANALYSIS_OF_PREEXISTING_R1_FROZEN_SUCCESSOR_DATASET`
`RECOMPUTE_STATUS=PASS`
`RECOMPUTE_OUTPUT_SHA256=8724263aca1feb29ad9f57752bdc523e12ce6be5fb5186b24431100398b3af55`
`FINAL_CI_STATUS=PENDING`

Original R1 source-prereg `recompute.py` was invoked twice with the frozen A1 input; both invocations passed and their output bytes were identical. The endpoint fields below are copied from that output without reinterpretation.

```json
{
  "interface_execution": {
    "denominator": 6,
    "lineage_success": {
      "L01": true,
      "L02": true,
      "L03": true,
      "L04": false,
      "L05": false,
      "L06": false
    },
    "success_count": 3
  },
  "reference_target_compatibility": {
    "denominator_per_target": 6,
    "success_counts_by_evaluator": {
      "a1-fresh-evaluator-a": {
        "A": 2,
        "B": 6,
        "C": 4
      },
      "a1-fresh-evaluator-b": {
        "A": 2,
        "B": 6,
        "C": 4
      }
    }
  },
  "incremental_policy_effect": {
    "control_denominator": 6,
    "control_observed_by_lineage": {
      "L01": true,
      "L02": true,
      "L03": true,
      "L04": true,
      "L05": true,
      "L06": true
    },
    "evaluator_counts": {
      "a1-fresh-evaluator-a": {
        "chain_successes_among_observed_controls": 0,
        "m0_only_A_successes": 0,
        "observed_controls": 6
      },
      "a1-fresh-evaluator-b": {
        "chain_successes_among_observed_controls": 0,
        "m0_only_A_successes": 0,
        "observed_controls": 6
      }
    },
    "m0_only_controls_observed": 6,
    "support_threshold_met": false,
    "when_all_controls_observed_threshold_not_met": "no conclusion marker; do not infer causality"
  },
  "result_markers": {
    "incremental_policy_effect": null,
    "interface_execution": "INTERFACE_EXECUTION_PARTIAL",
    "reference_target_compatibility": "REFERENCE_TARGET_COMPATIBILITY_NOT_ESTABLISHED"
  },
  "next_direction": "TRANSFER_INTERFACE_REPAIR"
}
```

`R1_PRIMARY_STATUS_REMAINS=STOPPED_PROTOCOL_DEVIATION_NO_SCIENTIFIC_RESULT`
`R2_TERMINAL_STATUS_REMAINS=TASK229_R2_SANITIZER_CONTRACT_NOT_ESTABLISHED`
`R2_A1_TERMINAL_STATUS_REMAINS=TASK229_R2_A1_RECOMPUTE_MISMATCH`
`NEW_SUCCESSOR_SESSIONS=0`
`NEW_EVALUATOR_SESSIONS=0`
`TASK230_AUTO_LAUNCH=false`

## Closeout status

Deterministic Fire Seeds and repository projections: PASS. Final exact-head CI 4/4 and the A2 terminal success status remain pending.
