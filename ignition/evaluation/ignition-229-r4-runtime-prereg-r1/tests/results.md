# R1 local deterministic validation results

Date: 2026-10-04.

- `python3 -m unittest tests.test_runtime_prereg -v`: **PASS**, 14 tests.
- `python3 -m py_compile runtime_executor.py runtime_supervisor.py`: **PASS**.
- Frozen R0 package SHA-256 verification at parent `b7267180cb2afe735cdcb0e75583d2e356cadf98`: **PASS**, 12/12 artifacts.
- `python3 tools/foundation/validate_repository_path_classification.py --check`: **PASS**, 10/10 checks; the generated manifest classifies this R1 subtree as `EVALUATION_EVIDENCE`.
- Provider calls: **0**. Canary calls: **0**. R4 live units: **0**. Evaluator runs: **0**. Task230: **not started**.

Fixtures cover canonical no-tool request fields, one-request-per-process enforcement, inert live authorization gate, deterministic frozen input framing, frozen input hash failure, exact transport and payload hash order, incomplete/invalid/duplicate/ambiguous/refusal/tool-call response rejection, non-200 and compressed response rejection, payload sizes below/at/above 16,384 bytes including multibyte UTF-8, and timeout termination of a child process group without retry.

These checks exercise local synthetic fixtures only. They do not establish provider/account acceptance, execute any Task229 input, invoke the R4 validator/evaluator, or authorize a canary.
