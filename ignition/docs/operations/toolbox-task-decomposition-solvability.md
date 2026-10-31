# Task Decomposition Solvability Comparator

`planning.compare_task_decomposition_solvability@0.1.0` is an optional, offline CLI for checking several caller-declared task DAGs against the same typed task inputs, required outputs, executor capability contracts, validator contracts, and resource budget.

It checks dependency references and cycles, whether declared inputs are reachable from task inputs or declared ancestors, whether each executor contract accepts the requested inputs and can produce the declared outputs, whether every listed required validator is compatible and available for every work-unit output, and whether complete caller estimates fit the stated budget. An unknown validator availability stays unknown when its declared contract covers the output; a missing, incompatible, or unavailable required validator blocks that alternative. It reports feasible, blocked, and unknown alternatives. Complete estimates can produce a Pareto frontier; incomparable alternatives remain together.

```sh
python3 -B ignition/tools/toolbox_compare_task_decomposition_solvability.py --stdin \
  < ignition/tests/fixtures/toolbox-task-decomposition-solvability/valid-input-r0.json
```

The CLI reads at most 262,144 UTF-8 JSON bytes from stdin and writes one JSON result to stdout. It accepts 2–16 alternatives, up to 64 work units per alternative, and up to 128 declared executor and validator contracts of each kind. Identifiers use a bounded ASCII form. Unknown cost fields are represented as `null`. Integer cost and budget fields are limited to 32 decimal digits.

## Result meaning

- `UNSOLVABLE_AS_DECLARED` means at least one required capability, dependency, input edge, output type, validator, or declared budget condition is contradicted by the input contract.
- `SOLVABILITY_UNKNOWN` means no declared contradiction was found, while executor or validator availability or a complete resource estimate remains unknown.
- `SOLVABLE_AS_DECLARED` means the declarations are internally consistent and their complete serial cost estimates fit the supplied budget. This is a structural result; it does not predict successful execution.
- `resource_frontier` compares only caller-declared `action_count`, `wall_clock_seconds`, and `output_bytes`. Those estimates are summed serially and are not measured by this program. No global preference or unique leader is inferred among non-dominated alternatives.

Executor/validator availability is supplied by the caller and is not live-probed. Validators are checked by declared type contract and are never run. Executors are never invoked. The tool does not execute, schedule, authorize, approve, or dispatch any alternative; it does not read repository files, access a network, use secrets, incur provider billing, or write files. The fixed output flags remain `validators_executed=false`, `executors_invoked=false`, and `execution_authorized=false`.

Use the existing `ignition.adaptive_toolbox_route_planner` when the task needs an input/output operation-set proposal. Use `collaboration.validate_agent_episode_binding` for declared agent roles, permissions, context, feedback, and write-domain consistency. Use the Current Agent Runtime Scheduler only after a DAG has been selected and separately authorized. This comparator covers the narrower gap of comparing alternative DAG contracts for declared executor and validator solvability; it does not replace those tools or interfaces.

The tool is `EXPERIMENTAL_AVAILABLE`, default off, and selectable only through an explicit experimental allowlist. A route is a proposal and does not authorize a call. If the task has only natural-language requirements, a missing contract, or unverified availability that matters to the conclusion, report `SOLVABILITY_UNKNOWN` or stop for human clarification. If the program rejects input, preserve the caller's original bytes and repair the request from the input schema; error output never echoes the request body.

Runtime code is covered by BUSL-1.1 during its Change Date period. Input/output schemas are Apache-2.0 interface assets. This documentation is CC-BY-NC-SA-4.0. See the root `LICENSE` and `ignition/LICENSES/README.md`.
