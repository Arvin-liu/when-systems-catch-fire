# External Agent Interface Audit R1

Task: `IGNITION-20260816-122`  
Audit mode: read-only inventory, local help, and official-source inspection  
Accessed: 2026-08-16 15:01 Asia/Shanghai  
Formal baseline: `277ea6c17883d9fe7661a92175a02c3cdfabac9d`

## Decision boundary

This audit records observable machine surfaces. It does not grant permissions,
prove external-agent correctness, import external memory, or make an executor a
part of the Ignition OS. No credentials, tokens, cookies, OAuth material,
private session databases, or message contents were read. No external
configuration was changed, and no package was installed or upgraded.

The inventory is the machine record:
[`executor-inventory-r1.json`](../../data/agent-federation/executor-inventory-r1.json).
Its validator is [`validate_executor_inventory.py`](../../tools/validate_executor_inventory.py).

## Repository baseline

- `origin/main` and the task worktree both point to the Task 121 final candidate
  `277ea6c17883d9fe7661a92175a02c3cdfabac9d`.
- The current platform spine is `agent_kernel/`, `agent_runtime/`, the four
  Domain Pack manifests, Supervisor, operational Memory, Profile, Reasoner
  Gateway and the registry-derived system map.
- The existing local action plane is deliberately bounded: local file
  operations, directory reads, literal allowlisted argv, read-only Git
  observations, typed approval, lease/idempotency and journal/reconciliation.
  It is recorded as `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR /
  FALLBACK_MINIMAL`, not as an external-agent replacement.
- The Task 121 targeted core gate ran 60 tests across Runtime, Pack, Profile,
  Memory, Supervisor, Gateway, routing, the R2 pilot and propagation, with
  `OK`. A broad discovery probe was deferred to the final full-regression
  stage after it produced no output for several minutes; this is not treated
  as a passing full-repository result.
- The inherited `T16_SYMPY_COUNTEREXAMPLE` remains an explicitly environmental
  `SymPy unavailable` residual. This audit does not alter any proof, claim,
  M/E, scope, provenance, lifecycle or epistemic state.

## Local executable inventory

| Executor | Observed version | Stable machine surface observed | Key limits for an adapter |
| --- | --- | --- | --- |
| OpenClaw | `2026.7.1-2 (0790d9f)` | `openclaw agent --json`, `--message-file`, `--session-key`/`--session-id`, `--timeout`; ACP and Gateway command families are present | JSON result and CLI timeout are observable; progress/cancel/resume/workspace semantics are not assumed from the agent help alone; channel/tool/runtime ownership stays with OpenClaw |
| Hermes Agent | `v0.20.0 (2026.8.3)` | `-z/--oneshot`, query mode, `--resume`/`--continue`, `--worktree`, ACP command, JSON usage report | One-shot stdout is final text, not a normalized event stream; timeout/cancel/structured progress require a separate bounded probe; memory, skills, subagents, gateway and providers stay Hermes-owned |
| Codex CLI | `0.144.4` | `codex exec --json`, JSONL events, `--output-schema`, stdin, `exec resume`, sandbox and approval flags | Permission is the intersection of OS and Codex policy; nested long-running Codex modification is forbidden; internal session history is only an optional external pointer |

The exact help SHA-256 values, binary paths, configuration-directory
presence-only results and `NOT_RUN_STEP_00` smoke statuses are in the machine
inventory. All three binaries were already present; absence would have been
recorded as `UNAVAILABLE_NOT_INSTALLED`, without installation.

## Official sources

Only official project repositories and documentation were used for the source
audit:

- OpenClaw repository at
  <https://github.com/openclaw/openclaw> (main commit
  `507e8b985e55e4a549a73afcf7d4a4fa7942e1e3`); the public machine-facing
  reference is <https://github.com/openclaw/openclaw/blob/main/docs/cli/agent.md>.
- Hermes repository at
  <https://github.com/NousResearch/hermes-agent> (main commit
  `8ad055414bcae75486952c5080d366679e074c1b`); the official CLI reference is
  <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/cli.md>.
- Codex repository at <https://github.com/openai/codex> (main commit
  `9ded177ce7c1c0bd2047f902936c177612ab3434`) and the official CLI reference
  at <https://developers.openai.com/codex/cli/reference/>.

The official documents are used to select public machine-facing surfaces, not
to infer undocumented internals. Local `--help` and `--version` remain the
execution-time compatibility authority for later adapters.

## Step 00 result

`STEP_00_BASELINE_AND_EXECUTOR_INVENTORY_COMPLETE`.

Proceeding boundary: build a vendor-neutral ownership contract and keep the
Reference Executor frozen. No live smoke was run in this step; Steps 04–06 and
10 may run at most the bounded probes explicitly allowed by the task.
