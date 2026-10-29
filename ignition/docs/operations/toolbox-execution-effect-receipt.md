# Execution Effect Receipt Preflight R0

maintenance.preflight_execution_effect_receipt checks whether a caller-supplied execution record and later observation refer to the same declared tool, version, source digest, input/output digest, environment, and run. It keeps NOT_RUN, STARTED, COMPLETED, and UNKNOWN distinct and flags a nonzero completed run whose first-failure record was not declared preserved.

Run it with one bounded JSON object on stdin:

    python3 -B ignition/tools/toolbox_execution_effect_receipt.py --stdin < receipt.json

The input limit is 131072 bytes. The schema permits up to 32 observations and 32 repository paths. When paths are supplied, the command independently rereads regular files under ignition/ using no-follow opens, returns SHA-256 digests without file contents, and compares the observed state with the caller-declared baseline. It reads at most 1 MiB per file and 4 MiB total. Paths outside ignition/, symlinks, non-files, and oversized files fail closed.

## What the result means

- NO_RUN_RECORDED means the input declares no run. It is not a successful run.
- OUTCOME_UNKNOWN means a run was declared but no effect state was bound to it.
- OUTCOME_RECORDED_CALLER_DECLARATION means at least one known effect state agrees with the declared identities, hashes, environment, run ID and chronology. If another matching observation remains UNKNOWN, the output preserves that with OUTCOME_WITH_UNRESOLVED_OBSERVATION and the UNKNOWN state.
- Binding mismatches, contradictory observations, or missing failure preservation remain findings.
- OBSERVER_IS_EXECUTOR_SELF_REPORT identifies a matching actor reference. A different actor reference is only a caller-declared distinction; it does not establish observer independence.
- A nonzero run's failure-preservation field records only that the caller declared the first failure preserved.
- Every output keeps source_authentication=NOT_PERFORMED, outcome_truth=NOT_ESTABLISHED, and execution_authorized=false.
- A local path result records current bytes or absence relative to the supplied baseline. It does not establish that the declared run caused a difference or that the file set was complete.

## Limits and fallback

This preflight does not read receipt evidence references or validate supplied digests against their source bytes. The bounded local path recheck is a direct observation of the current checkout, but it does not authenticate the run or baseline, observe external systems, establish causality, or prove a scientific result. Treat the output as a consistency aid. When independent proof is required, inspect the underlying run and effect through a separately authorized evidence source and preserve the original failure record. For portable artifact/version relations use collaboration.validate_portable_research_episode; for GitHub Actions plans and artifacts use maintenance.attribute_actions_validation_evidence; for failure diagnosis and retry-plan gates use maintenance.preflight_failure_anchored_recovery.
