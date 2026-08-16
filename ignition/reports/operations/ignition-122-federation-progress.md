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

## Step 06 — COMPLETE

- Result: `STEP_06_CODEX_ADAPTER_COMPLETE`.
- Adapter: `agent_federation/adapters/codex.py`; fixture:
  `tests/fixtures/federation/codex-exec-jsonl-response.jsonl`.
- Current local help confirmed `codex exec --json`, `--ephemeral`,
  `--ignore-user-config`, `--ignore-rules`, `--sandbox`, `--cd` and the
  `exec resume` command family. The adapter uses the JSONL machine surface,
  config/rules isolation, an explicit default `read-only` sandbox and an
  optional explicit absolute workspace scope.
- Codex permission is the intersection of the OS envelope, sandbox and
  approval policy. `workspace-write` requires explicit adapter construction and
  an envelope that permits external execution; dangerous bypass flags are
  never emitted. The default adapter cannot satisfy `repo.write` or
  `repo.test`.
- JSONL events are reduced to a bounded public summary, optional progress
  fraction and pointer-only `codex-thread-id`; raw event history and token
  usage are not retained as OS state. Completion remains
  `COMPLETED_UNVALIDATED` / `REQUIRES_RECONCILIATION`.
- Gates: Codex fixture/JSONL/sandbox/pointer/receipt tests plus Hermes,
  OpenClaw and 121 core set = `94/94 PASS`; inventory, ownership and
  runtime-boundary validators = `PASS`.
- Live smoke: `LIVE_SMOKE_NOT_RUN`; nested Codex formal-repository
  modification was explicitly forbidden.

## Step 07 — COMPLETE

- Result: `STEP_07_FEDERATION_ROUTER_COMPLETE`.
- Router: `agent_federation/router.py`; policy:
  `data/agent-federation/federation-routing-policy-r1.json`; schema:
  `schemas/agent-federation/federation-routing-policy-r1.schema.json`.
- `FederationRouter` evaluates explicit pin priority, declared capability and
  permission ceiling, approval/effect compatibility, availability/health,
  granularity, privacy, workspace locality, configured task preference,
  least-privilege surplus and stable executor/instance ID tie-break in a
  fixed order.
- `RoutingDecision` records every candidate, typed rejection reasons, selected
  executor, effective permission and fallback order. Unavailable candidates
  may fall back only to an already-compatible candidate; no capability is
  widened. Preferences are policy data; router code contains no brand branch,
  marketing ranking or inferred model-quality claim.
- Gates: routing policy validator plus router/policy/filter/fallback tests and
  the prior adapter/core set = `101/101 PASS`; inventory, ownership and
  runtime-boundary validators = `PASS`.
- Residual: this step produces a vendor-neutral routing plan; approval bridge,
  handoff/failover and Supervisor execution integration remain the next
  governed boundaries.

## Step 08 — COMPLETE

- Result: `STEP_08_APPROVAL_HANDOFF_FAILOVER_COMPLETE`.
- Boundary: `agent_federation/approval_handoff.py`; failover taxonomy:
  `data/agent-federation/failover-reasons-r1.json`.
- `ApprovalBridge` applies the strict OS/external intersection: OS `DENY`
  cannot be overridden; Owner-required policies wait for Owner; external
  approval remains a typed non-authoritative gate.
- `build_handoff_bundle` copies only public goal/work/acceptance, validated
  receipt actions, artifact hashes, capability/workspace refs, operational
  memory capsule refs and pointer-only sessions. `accept_handoff` requires a
  different target to re-observe the workspace and verify the source receipt.
- Failover is automatic only for read-only tasks or validated/replayable side
  effects with a verified receipt and a target that already satisfies the same
  capability ceiling. Unknown side effects and unverified receipts become
  `REQUIRES_RECONCILIATION`.
- Gates: approval, handoff, takeover, capability and failover tests plus the
  previous router/adapter/core set = `109/109 PASS`; inventory, ownership and
  runtime-boundary validators = `PASS`.
- Residual: cross-executor progress/memory deduplication and disposable
  federation pilots remain for Steps 09–10.

## Step 09 — COMPLETE

- Result: `STEP_09_CROSS_EXECUTOR_CONVERGENCE_COMPLETE`.
- Convergence: `agent_federation/convergence.py`; fixtures:
  `tests/fixtures/federation/streaming-progress-events.jsonl` and
  `malformed-event.txt`.
- `ProgressLedger` gives public progress stable ordering, duplicate keys,
  late-event/late-terminal classification and non-regressing canonical state.
  `ReceiptRegistry` stores only digest/status/validator refs/artifact refs;
  `COMPLETED_VALIDATED` without validator refs remains unverified.
- `MemoryProjection` is the narrow bridge into the existing
  `OperationalMemoryStore`. It accepts public summaries, validated receipt
  evidence, failures, approval and recovery decisions, and the absorber
  rejects hidden markers and deduplicates event keys/memory IDs. Vendor
  telemetry, prompts, CoT, token data and private session history remain out.
- Gates: streaming/partial/malformed parser, ordering, duplicate, receipt,
  memory and hidden-state tests plus the prior set = `116/116 PASS`;
  inventory, ownership and runtime-boundary validators = `PASS`.
- Residual: the absorber's exactly-once dedup index is process-local in R1;
  persistent integrity/tombstones remain owned by the existing memory store.

## Step 10 — COMPLETE

- Result: `STEP_10_DISPOSABLE_FEDERATION_PILOTS_COMPLETE`.
- Pilot A: `agent_federation/pilots.py` runs one `repo.read` envelope against
  the bounded Reference Executor view and all three inventory `AVAILABLE`
  adapters. The disposable fixture contains one incorrect manifest hash and
  one broken Markdown link; the formal repository is not a live target.
- The vendor rows use captured public CLI boundaries injected into the
  existing adapters. OpenClaw is denied because its observed descriptor does
  not claim `repo.read`; Hermes is a text-degraded bridge; Codex exposes JSONL
  progress. All live calls remain explicitly
  `NOT_RUN_LIVE_EXTERNAL_INVOCATION`.
- Pilot B builds a public handoff from a Reference Executor receipt, requires
  workspace/artifact re-observation, then dispatches the Codex adapter
  fixture. The target executor completion remains
  `REQUIRES_RECONCILIATION` until the OS-owned validator independently
  confirms the same two deterministic issues and source immutability.
- Pilot C injects timeout, malformed output, unsupported capability, stale
  receipt, duplicate progress/dispatch, forged terminal/approval, incapable
  handoff and unknown side effects. Only the bounded read-only timeout is
  automatically failover-eligible; unknown side effects remain
  `REQUIRES_RECONCILIATION` and no irreversible action repeats.
- Machine result: `data/agent-federation/federation-pilot-results-r1.json`;
  validator status `PASS`. Gates: Pilot A/B/C plus the prior set =
  `122/122 PASS`; inventory, ownership and runtime-boundary validators =
  `PASS`.
- Residual: no live external inference was needed or run; protocol
  compatibility and bounded failure behavior do not establish intelligence,
  production autonomy, external approval or universal safety.

## Step 11 — COMPLETE

- Result: `STEP_11_FEDERATION_ARCHITECTURE_AND_HUMAN_SURFACE_SYNC_COMPLETE`.
- Canonical projection: component registry `1.6.0`, topology `1.6.0`, layout
  `1.4.0`, current system map `0.7.0`; the deterministic map contains `82`
  registry components, `70` visible nodes, `77` typed edges and `12` hidden
  representative components.
- Federation identity: the map now shows the OS contract, OpenClaw/Hermes/Codex
  adapters, frozen Reference Executor and deferred Future Executors. The
  propagation contract isolates `agent_federation/` as
  `agent_platform.federation` and forbids direct Knowledge, Writing, Human
  front-door and Pack-registry projection.
- Human Surface: cold-start, handoff, architecture, current state, Results,
  Results Book, Pack docs, root README, materiality fingerprints and the
  append-only STATE-CHANGELOG delta are synchronized. The materiality manifest
  changed only source fingerprints for the manually updated canonical surfaces;
  no Knowledge claim or asset was added.
- Gates: deterministic generators, ownership/routing/runtime validators,
  blast-radius contract, Human Surface contract/visibility/front-door validators
  and the targeted federation/architecture regression = `132/132 PASS`; state
  changelog validator = `PASS`.
- Repair: one bounded repair round expanded historical sealed-source handling
  for append-only map/current-state projections and regenerated the blast-radius
  report after adding the federation source domain.
- Residual: Step 12 adversarial/full discovery, fresh-clone replay, final normal
  fast-forward and independent 1111 receipt remain open. `main` has not moved.

| Step | Status | Commit | Remote | Targeted gate |
| --- | --- | --- | --- | --- |
| 00 | COMPLETE | `05ac54db` | `05ac54db` | inventory schema + 121 core = PASS |
| 01 | COMPLETE | `a8b0cadd` | `a8b0cadd` | ownership + freeze + 66 tests = PASS |
| 02 | COMPLETE | `53585047` | `53585047` | federation core + 71 tests = PASS |
| 03 | COMPLETE | `43af8300` | `43af8300` | SDK/conformance + 76 tests = PASS |
| 04 | COMPLETE | `fa0a6890` | `fa0a6890` | OpenClaw adapter + 82 tests = PASS |
| 05 | COMPLETE | `1e5d3590` | `1e5d3590` | Hermes adapter + 88 tests = PASS |
| 06 | COMPLETE | `74796f6a` | `74796f6a` | Codex adapter + 94 tests = PASS |
| 07 | COMPLETE | `1ac6880e` | `1ac6880e` | router + 101 tests = PASS |
| 08 | COMPLETE | `5dbbdfa9` | `5dbbdfa9` | approval/handoff/failover + 109 tests = PASS |
| 09 | COMPLETE | `954a5bad` | `954a5bad` | convergence + 116 tests = PASS |
| 10 | COMPLETE | `2773c303` | `2773c303` | pilots + 122 tests = PASS |
| 11 | COMPLETE | pending self commit binding | pending `ls-remote` binding | architecture/Human Surface + 132 tests = PASS |
| 12 | PENDING | — | — | — |
