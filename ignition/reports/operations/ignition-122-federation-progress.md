# IGNITION-20260816-122 Federation R1 Progress

Task branch: `codex/ignition-122-external-agent-federation-r1-20260816`  
Formal baseline: `277ea6c17883d9fe7661a92175a02c3cdfabac9d`  
Control pointer: `1111 origin/relay/current = bb0b2f9ff3d32906ff5aa6fd0642ffb2bee54eba`

This ledger is a task-branch execution record. A step row is written before
its step commit, so the commit and remote SHA columns remain `null` until the
independent Git/remote closure receipt binds them. No row is evidence of
external truth, Owner acceptance, production safety or epistemic acceptance.

## Step 00 — COMPLETE

- Result: `STEP_00_BASELINE_AND_EXECUTOR_INVENTORY_COMPLETE`.
- Machine record: `data/agent-federation/executor-inventory-r1.json`.
- Audit: `reports/architecture/external-agent-interface-audit-r1.md`.
- Inventory validator: `python3 tools/validate_executor_inventory.py`.
- Local executors: OpenClaw `2026.7.1-2`, Hermes `v0.20.0`, Codex `0.144.4`.
- Targeted 121 core regression: `63/63 PASS` across Runtime, Pack, Profile,
  Memory, Supervisor, Gateway, routing, R2 pilot and propagation.
- Live smoke: `NOT_RUN_STEP_00` for all external executors.
- Safety: no secret content read; no external configuration changed; no
  installation or upgrade; no external message/device/browser action.
- Residuals: inherited environmental `T16_SYMPY_COUNTEREXAMPLE`; broad
  unittest discovery deferred to Step 12 after a no-output baseline probe.

## Step 01 — COMPLETE

- Result: `STEP_01_OWNERSHIP_CONTRACT_AND_REFERENCE_FREEZE_COMPLETE`.
- Contracts: `data/agent-federation/os-executor-ownership-r1.json`,
  `build-vs-integrate-policy-r1.json` and
  `executor-component-ownership-r1.json`.
- Human Surface: `docs/architecture/external-agent-federation-r1.md`.
- Gate: `python3 tools/validate_federation_ownership.py` = `PASS`;
  protected new runtime path negative fixture = `PASS`;
  121 core plus inventory/ownership tests = `66/66 PASS`.
- Reference Executor stays existing, bounded and provider-neutral; no browser,
  network, messaging, provider/model, daemon, subagent or remote-Git layer was
  added.
- Residual: no build-vs-integrate exception is recorded; future protected
  runtime layers remain deferred.

## Step 02 — COMPLETE

- Result: `STEP_02_FEDERATION_CORE_CONTRACT_COMPLETE`.
- Package: `agent_federation/contracts.py`; schema:
  `schemas/agent-federation/federation-core-r1.schema.json`.
- Typed records: `ExecutorDescriptor`, `FederatedTaskEnvelope`,
  `FederatedProgressEvent`, `FederatedResultReceipt`, `ExternalSessionRef`,
  `FederatedHandoffBundle`, health and nested policy/output/validation/budget
  contracts, plus the narrow `FederatedExecutor` protocol.
- Gates: typed roundtrip, bounded progress, receipt digest/tamper rejection,
  pointer-only session refs and hidden-field rejection; 121 core plus new
  contract tests = `71/71 PASS`.
- Residual: external session state is a pointer only; no vendor history,
  prompt, hidden reasoning, token or private memory is canonical OS state.

## Step 03 — COMPLETE

- Result: `STEP_03_ADAPTER_SDK_AND_CONFORMANCE_COMPLETE`.
- Package: `agent_federation/sdk.py` and `agent_federation/conformance.py`;
  taxonomy: `data/agent-federation/capability-taxonomy-r1.json`.
- Boundary utilities cover `shell=False` argv execution, executable discovery,
  version matching, timeout/output caps, JSON/JSONL parsing, secret redaction,
  capability mapping, cancellation, pointer refs and receipt construction.
- `FederationConformanceSuite` exercises probe/descriptor, unsupported
  capability denial, dispatch/progress, status ordering, cancel, optional
  resume and idempotency without a hidden agent loop.
- One redaction repair round removed sensitive field names from canonical
  telemetry and retained only a `redacted_fields` count; targeted regression is
  `76/76 PASS`.
- Residual: SDK cancellation/output caps are boundary utilities, not runtime
  permissions.

## Step 04 — COMPLETE

- Result: `STEP_04_OPENCLAW_ADAPTER_COMPLETE`.
- Adapter: `agent_federation/adapters/openclaw.py`; fixture:
  `tests/fixtures/federation/openclaw-agent-json-response.json`.
- Observed public invocation: `openclaw agent --json --message-file
  <disposable UTF-8 envelope> --timeout <seconds>`, with optional observed
  `--agent` and `--session-key` arguments. argv is literal and the default
  runner is `shell=False` through the adapter SDK.
- Descriptor is derived from the real version/help shape. The adapter declares
  only `long_task`; it does not infer progress, cancellation, native resume,
  workspace authority, Gateway/channel/device access, or structured validation
  from OpenClaw's internal behavior.
- Executor completion is represented as `COMPLETED_UNVALIDATED`; the receipt
  remains `REQUIRES_RECONCILIATION` with `OS_VALIDATION_NOT_PERFORMED` until
  Ignition validators establish evidence. Session values are pointer-only.
- Gates: OpenClaw fixture/CLI/redaction/receipt tests plus the 121 core set =
  `82/82 PASS`; inventory, ownership and runtime-boundary validators = `PASS`.
- Live smoke: `LIVE_SMOKE_NOT_RUN`; no external inference, Gateway, private
  SQLite/session inspection, configuration change, channel action, install or
  upgrade was performed.

## Step 05 — COMPLETE

- Result: `STEP_05_HERMES_ADAPTER_COMPLETE`.
- Adapter: `agent_federation/adapters/hermes.py`; fixture:
  `tests/fixtures/federation/hermes-oneshot-final-response.txt`.
- Current local help confirmed Hermes `-z/--oneshot PROMPT`, `--safe-mode`,
  `--ignore-user-config`, `--ignore-rules`, `--resume` and
  `--no-restore-cwd`. The adapter uses only the one-shot text surface and
  passes the bounded task body as one literal argv value.
- Because Hermes one-shot approvals are auto-bypassed and stdout is final
  text, the adapter declares only `repo.read`, requires explicit low-risk
  effects and forbidden effects, and rejects write, send, terminal, browser,
  device, gateway, network and other non-read actions. It never passes
  `--yolo` or `--accept-hooks`.
- Hermes config, memory, rules, skills, subagents, providers, gateways,
  sessions and auth remain external-owned. Optional resume values are
  pointer-only. Completion maps to `COMPLETED_UNVALIDATED` and the receipt
  remains `REQUIRES_RECONCILIATION`.
- Gates: Hermes fixture/descriptor/read-only/session/receipt tests plus the
  OpenClaw and 121 core set = `88/88 PASS`; inventory, ownership and
  runtime-boundary validators = `PASS`.
- Live smoke: `LIVE_SMOKE_NOT_RUN`; no inference, provider/config/auth change,
  memory read, Gateway, message, installation or upgrade was performed.

| Step | Status | Commit | Remote | Targeted gate |
| --- | --- | --- | --- | --- |
| 00 | COMPLETE | `05ac54db` | `05ac54db` | inventory schema + 121 core = PASS |
| 01 | COMPLETE | `a8b0cadd` | `a8b0cadd` | ownership + freeze + 66 tests = PASS |
| 02 | COMPLETE | `53585047` | `53585047` | federation core + 71 tests = PASS |
| 03 | COMPLETE | `43af8300` | `43af8300` | SDK/conformance + 76 tests = PASS |
| 04 | COMPLETE | `fa0a6890` | `fa0a6890` | OpenClaw adapter + 82 tests = PASS |
| 05 | COMPLETE | pending self commit binding | pending `ls-remote` binding | Hermes adapter + 88 tests = PASS |
| 06 | PENDING | — | — | — |
| 07 | PENDING | — | — | — |
| 08 | PENDING | — | — | — |
| 09 | PENDING | — | — | — |
| 10 | PENDING | — | — | — |
| 11 | PENDING | — | — | — |
| 12 | PENDING | — | — | — |
