# Governed Improvement Transition Preflight R0

`maintenance.preflight_governed_improvement_transition` summarizes one caller-declared predecessor-to-successor record. It is a narrow, offline implementation candidate for Workbench AB-19's governed improvement transition.

Run from the repository root:

```bash
python3 -B ignition/tools/toolbox_governed_improvement_transition.py --stdin < transition.json
```

The input is one UTF-8 JSON object, limited to 128 KiB. It binds predecessor and successor digests, the declared mechanism change, preregistration, evaluator/benchmark/held-out digests, quality/cost/failure values, permission scopes, rollback target/status, and an optional next-round R&D metric. A changed evaluation anchor makes the primary quality values incomparable. A caller-supplied successor replay is comparable only when its explicit evaluator, benchmark, and held-out digests match the predecessor binding; the tool checks this declaration but cannot authenticate the replay. A positive next-round metric must be measured explicitly; absence remains `NEXT_ROUND_GAIN_NOT_MEASURED`.

The result always has `status=REVIEW_REQUIRED`. It performs exact structural checks and arithmetic over caller-provided values, and never authenticates those values or accepts an improvement. It does not execute a successor, modify code, select an evaluator, start a recursive loop, grant permission, deploy, merge, or publish. Even favorable arithmetic is only an input-bound review aid. No repository files, network, secrets, subprocesses, billing, or external actions are used.

Use only when comparing a specific frozen predecessor with a successor candidate and the task needs the transition-level deltas. Do not use it as a general benchmark/Pareto analyzer, a release gate, or a substitute for the existing Iteration Method, preregistration, independent review, or rollback machinery. Existing Pareto, producer-consumer, and writing-migration tools retain their distinct task contracts.

Input contract: `ignition/schemas/operations/governed-improvement-transition-r0.schema.json`. Synthetic input: `ignition/tests/fixtures/toolbox-governed-improvement-transition/valid-input-r0.json`.

## C1 comparison

A matched synthetic three-candidate task was run through the transition preflight for each successor and through the neighboring Pareto summary across all candidates. Pareto reported the pass-rate/resource frontier in one call; the transition preflight reported evaluation-anchor, failure/cost, authority, rollback, and next-round status per successor. The result supports complementary output coverage only. Replacement value, real-task utility, reliability, and calibrated cost remain unknown; no tool was retired.

See `ignition/data/operations/toolbox-governed-improvement-transition-c1-matched-comparison-r0.json` and the three pinned inputs under `ignition/tests/fixtures/toolbox-governed-improvement-transition/` for the synthetic comparison and local CLI timing protocol.
