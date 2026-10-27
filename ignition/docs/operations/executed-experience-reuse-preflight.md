# Executed Experience Reuse Preflight

`knowledge.preflight_executed_experience_reuse` checks caller-selected execution receipts before a prior result is shown as an optional reference for a later task. It is an experimental CLI candidate and remains excluded from routing by default. It is read-only, has no network or secret access, writes no files, and never executes, authorizes, ranks, or promotes a procedure.

## Supported request contracts

- R0 (`toolbox-executed-experience-preflight-r0`, response tool version `0.1.0`) preserves the original contract. It checks a bounded local receipt artifact, declared task family, environment, source scope, tool/source identity, outcome label, and expiry. It does not reopen the source, input, or output bytes named by that receipt.
- R1 (`toolbox-executed-experience-preflight-r1`, response tool version `0.2.0`) adds caller-selected local source, input, and output artifact paths and digests. The tool requires the source path and digest to agree with a repository-state observation in the receipt, then reads each artifact under `ignition/` and compares the actual bytes with the receipt's declared hashes. A preserved negative outcome also requires its failure bytes to match the receipt.

R1 checks no more than 32 experience entries, at most 1 MiB per artifact, and 8 MiB of total artifact reads per request. Expired or scope-mismatched entries are withheld before any receipt or bound-artifact reads. Duplicate paths within one experience, traversal, symlinks, non-regular files, malformed receipts, missing artifacts, digest mismatches, and exhausted budgets fail closed.

An exact-scope `EFFECT_PRESENT` receipt can be shown only as `OPTIONAL_REFERENCE_ONLY`; `EFFECT_ABSENT` is `COUNTEREXAMPLE_ONLY` only when failure preservation is declared and, in R1, the failure bytes match. Different scopes require review. R0 remains available for old callers; R1 does not change permissions or route defaults.

The evidence remains caller-declared. Matching local bytes do not authenticate who ran the tool, the environment, the source's authority, the actual effect, or the truth of a reported outcome. `EFFECT_PRESENT` is not a task-success claim. Both contracts return `execution_authorized=false` and `reuse_authorized=false`; the caller separately decides whether a reference is useful and must independently authorize any later execution.

Run from the repository root:

```bash
python3 -B ignition/tools/toolbox_executed_experience_preflight.py --stdin \
  < ignition/data/operations/toolbox-executed-experience-real-task-input-r0.json

python3 -B ignition/tools/toolbox_executed_experience_preflight.py --stdin \
  < ignition/data/operations/toolbox-executed-experience-real-task-input-r1.json
```

R0 schemas are `ignition/schemas/operations/toolbox-executed-experience-preflight-r0.schema.json` and `toolbox-executed-experience-result-r0.schema.json`. R1 schemas are the matching `*-r1.schema.json` files. The C1 evidence keeps protocol compatibility and byte-complete task ranges distinct; it does not establish portfolio-wide replacement value.
