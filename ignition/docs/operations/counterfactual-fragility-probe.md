# Counterfactual Fragility Probe

`research.probe_counterfactual_fragility@0.1.0` runs one baseline and up to eight independent, caller-declared input edits against the same pure symbolic FunctionSpec. It reports the model output before and after each edit, whether the declared conclusion stayed stable within that model, and whether the observed direction matched the caller's expectation.

The tool composes the existing `function_os.run_bounded_symbolic_spec` evaluator. That evaluator remains appropriate for a single FunctionSpec/input pair. This wrapper adds a typed baseline-to-probe comparison and binds each probe to one caller-declared load-bearing assumption and one declared FunctionSpec input.

## Use

Provide UTF-8 JSON on stdin:

```sh
python3.12 -B ignition/tools/toolbox_counterfactual_probe.py --stdin < request.json
```

The request includes a target conclusion ID and wording, one FunctionSpec, its baseline inputs, one to sixteen assumption declarations, and one to eight probes. Each probe changes exactly one declared numeric or Boolean input, names the assumption that input represents, includes a caller-written admissibility note, and records the expected output direction before evaluation. Every probe starts from a fresh copy of the same baseline; edits are never chained.

Limits are 64 KiB per request, 16 KiB for the FunctionSpec, sixteen model inputs, sixteen assumptions, eight probes, and 256 KiB of output. Expressions inherit the stricter bounded-pure Function OS 0.2 runner limits. The runtime is Python 3.10 or newer; it uses the standard library and the checked-in Function OS candidate implementation.

The input and output contracts are [`toolbox-counterfactual-probe-input-r0.schema.json`](../../schemas/operations/toolbox-counterfactual-probe-input-r0.schema.json) and [`toolbox-counterfactual-probe-output-r0.schema.json`](../../schemas/operations/toolbox-counterfactual-probe-output-r0.schema.json). The runner rejects duplicate JSON keys, unknown fields, duplicate probe IDs, no-op edits, unsupported value types, and edits not bound to the declared assumption.

## Interpret the report

- `STABLE_WITHIN_DECLARED_MODEL` and `FRAGILE_WITHIN_DECLARED_MODEL` describe only exact outputs of the supplied symbolic model.
- `CALLER_DECLARED_NOT_VERIFIED` means the admissibility note is retained as supplied. The tool does not verify it.
- An unmet expected direction is kept as `EXPECTED_DIRECTION_NOT_OBSERVED_PRESERVE_AS_DISCONFIRMING_RESULT`; an expected direction that appears is explicitly not confirmation.
- A failed or precondition-failing probe remains in the output as unassessable. It does not change source evidence.
- Every report states that counterfactual edits are not evidence about the actual world, source evidence was not mutated, and no external action was taken.

## Boundaries and rollback

The tool does not identify causal effects, validate that a FunctionSpec models reality, decide that an intervention is admissible in the real world, prove a conclusion, or provide scientific or external validation. It reads the checked-in Function OS implementation to execute the bounded model; it does not read task evidence or source documents. It writes no files, makes no network calls, and does not invoke a tool router.

To roll back this optional candidate, remove its candidate card and CLI/schema/docs/tests from the isolated branch, regenerate the identity-card and `TOOLBOX.md` projections, and rerun the focused checks. Keep the source binding, comparison, task, and route records as historical evidence.
