# Executed Experience Reuse Preflight

`knowledge.preflight_executed_experience_reuse` checks caller-selected execution-receipt artifacts before a prior result is shown as an optional reference for a later task. It compares caller-declared task family, environment, source scope, tool/version/source identity, outcome label, and expiry. For a non-expired entry it reads one bounded JSON artifact under `ignition/` and checks the supplied SHA-256 before inspecting the embedded `receipt_input` and `receipt_output`.

The tool is an isolated `EXPERIMENTAL_AVAILABLE` CLI candidate and is excluded from routing by default. It is read-only, has no network or secret access, writes no files, and never executes, authorizes, ranks, or promotes a procedure. An exact-scope `EFFECT_PRESENT` receipt can be shown only as `OPTIONAL_REFERENCE_ONLY`; `EFFECT_ABSENT` is preserved as `COUNTEREXAMPLE_ONLY` when the receipt declares preserved failure evidence. Different scopes require review. Expired, malformed, mismatched, unknown, or unpreserved entries are withheld or returned for review.

The evidence tool's output remains caller-declared. Matching local bytes do not authenticate who ran the tool, the environment, the source's authority, the actual effect, or the truth of a reported outcome. `EFFECT_PRESENT` is not a task-success claim. The caller must separately decide whether the reference is useful and must independently authorize any later execution.

Run from the repository root:

```bash
python3 -B ignition/tools/toolbox_executed_experience_preflight.py --stdin \
  < ignition/data/operations/toolbox-executed-experience-real-task-input-r0.json
```

The input schema is `ignition/schemas/operations/toolbox-executed-experience-preflight-r0.schema.json`; the result contract is `ignition/schemas/operations/toolbox-executed-experience-result-r0.schema.json`. The C1 record compares its scope with the existing reusable-context and execution-effect receipt tools. Current evidence does not establish replacement or portfolio-wide net benefit.
