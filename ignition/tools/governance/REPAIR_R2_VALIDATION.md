# SYMBOLIC-SPHERE repair-r2 — R2 builder validation (internal)

Validated by the BUILDER against the shared engine after R1. This is an internal
`BUILDER_VALIDATION_PASS`; it is NOT `INDEPENT_ACCEPTED` (that requires the
morning independent re-review). No q33 inherited debt is relabelled as new green.

## Attack matrix (all exit non-zero after fix; were exit 0 before)

| # | bypass attempt | pre-fix | post-fix |
|---|---|---|---|
| 1 | absolute path `/etc/hosts` | 0 | non-zero |
| 2 | `..` traversal `../secrets` | 0 | non-zero |
| 3 | backslash path | 0 | non-zero |
| 4 | symlink escape | 0 | non-zero |
| 5 | fabricated exact_head `0`*40 | 0 | non-zero |
| 6 | missing `commit_sha` | 0 | non-zero |
| 7 | tampered `sha256` | 0 | non-zero |
| 8 | tampered `blob_sha` | 0 | non-zero |
| 9 | `facts=true`/`status=PASS`, non-resolving evidence | 0 | non-zero |
| 10 | parent head mismatch | 3 | 3 (unchanged, still rejected) |

## Positive path

- valid bundle built from a real Git object (recomputed `sha256`/`blob_sha` match)
  → exit 0 (GATE_PASS).

## Test entry

`python -m pytest tests/test_structured_capability_gate.py` → **10 passed**.
The engine is imported by every downstream B09 wrapper, so this fix propagates to
all nine consumers through the stacked `--no-ff` predecessor merges.
