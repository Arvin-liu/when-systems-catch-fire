# Future execution instructions for runtime R1

This package is preregistration only. Neither its marker nor the parent R0 next-direction authorizes execution. A separate explicit Owner instruction is required before a canary or R4 unit.

## Before a future canary

1. Reconfirm this exact R1 PR head, Draft/unmerged state, frozen parent `b7267180cb2afe735cdcb0e75583d2e356cadf98`, and unchanged PR #244/#246 state.
2. Obtain explicit Owner authorization for the synthetic canary. Review the access history in `leakage-boundary.md`; new R1 access events still need Owner/GPT disposition before any positive R4 result.
3. Verify all 12 frozen R0 artifact hashes against its committed `SHA256SUMS.txt`; verify the selected R4 runtime source hashes from `executor-source-manifest.json`.
4. Set `TASK229_R4_EXECUTION_AUTHORIZATION=OWNER_AUTHORIZED_R4_EXECUTION` only for the authorized process. Supply `OPENAI_API_KEY` through a secret environment mechanism. Never print or store the key.
5. Run one canary in a fresh external supervisor process, for example:

   ```sh
   python3 runtime_supervisor.py --receipt /secure-run/canary-supervisor.json -- \
     python3 runtime_executor.py --execute-live --canary --capture-dir /secure-run/canary
   ```

6. Accept it only under `runtime-canary-contract.json`. A failed, timed-out, mismatched, or unverifiable canary consumes the canary attempt and blocks all 18 units. Do not tune or retry; create a new preregistration revision.

## Before each of 18 units

Only after the canary gate passes and a separate Owner instruction authorizes the frozen R4 run:

1. Verify frozen R0 package hashes and run-order manifest. Select the next exact line from `execution-inputs.jsonl` and place only that single JSON line in a temporary `unit.json`; verify its frozen `input_hashes` before use.
2. Launch one worker through `runtime_supervisor.py` with one capture directory, the exact R3 prompt and response schema, and that one unit record. The environment authorization is required by the CLI. Use one process and one provider request. Follow the manifest order; do not retry, replace, reorder, or continue after a protocol deviation.
3. Preserve transport and payload capture files, hashes, supervisor record, model/effort acceptance evidence, runtime version, and unit input hashes. Do not expose validator-only expected fields to the worker.
4. A separate, specifically authorized deterministic R4 validation step may later consume the captured payload under the existing frozen R3 response/route schemas and the R0 mechanical outcome contract. This R1 runtime worker does not run that validator or an evaluator.

## Stop boundary

This runtime preregistration task ends before the canary. A passing local test, PR, or exact-head CI does not authorize a provider call, R4 unit, evaluator, Task230, Ready, or merge.
