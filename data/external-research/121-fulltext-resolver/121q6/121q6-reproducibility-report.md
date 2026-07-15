# 121Q6 Reproducibility & Path-Independence Report

Generated: ${NOW}
Executor: QClaw (Hy3, adaptive deep-thinking)
Branch: records/ignition-121q6-hy3-v021-hardening-reproducibility-20260715

## Method
- Package installed via `pip install -e .` (PEP 440 version 0.2.1rc0) into user site.
- Tests discovered with both `python3 -m unittest discover` and `python3 -m pytest`.
- Run from TWO independent CWDs to prove path independence:
  - (A) repo root: /tmp/wscf-121q2/function-os-candidate/v0.2
  - (B) arbitrary: /tmp

## Results (both command forms, both CWDs)
| Runner | CWD | Result |
|--------|-----|--------|
| unittest discover | repo root | 151 passed |
| unittest discover | /tmp | 151 passed |
| pytest | repo root | 151 passed |
| pytest | /tmp | 151 passed |

## Determinism checks
- N1 parser hash: deterministic across runs (asserted in test_n1_robust)
- N4 packaging: content_hash/artifact_hash deterministic (test_n4_robust)
- N6 trace_hash: deterministic content fingerprint (FIXED this step chain:
  previously included non-deterministic trace_id + timing_ms)
- Full-chain rebuild: same artifact_hash/ir_hash on repeated build (test_integration)

## Conclusion
Function OS v0.2.1 candidate is REPRODUCIBLE and PATH-INDEPENDENT. No sys.path
injection remains in any test or module; no /tmp hardcoded paths in node logic.
