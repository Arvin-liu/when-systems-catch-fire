# IGNITION-20260816-121 night-shift progress

## Step 00 — COMPLETE

- Baseline: `origin/main = 2becca3ffd93d6ca1e147a75c159e476f4686f5d`.
- Task branch: `codex/ignition-121-agent-platform-r2-nightshift-20260816`.
- Formal worktree was clean before and after the audit.
- R0/R1 runtime tests: `16/16 PASS`.
- Agent Runtime boundary: `PASS`.
- Agentization boundary: `PASS` (`75` components).
- State changelog, Human Front Door, Human Surface, Human Visibility, Knowledge
  Experience validation, and determinism checks: `PASS`.
- Gap audit: [agent-platform-r2-gap-audit.md](../architecture/agent-platform-r2-gap-audit.md).
- Machine ledger: [nightshift-progress.jsonl](../../data/operations/iterations/121/nightshift-progress.jsonl).

### Step 00 decision

`STEP_00_BASELINE_COMPLETE`; proceed to Step 01, Knowledge Corpus Admission
Policy and provenance-preserving migration. No failure repair round was needed.

## Step 01 — COMPLETE

- Admission policy: `KNOWLEDGE_CORPUS_ADMISSION_R1`, with five typed classes and
  a narrow architecture/Knowledge Pack explicit allowlist.
- Provenance migration: `5,202` platform-only baseline rows preserved in the
  append-only report (`2,187` function and `3,015` nonfunction), with original
  record hashes, source hashes, baseline Git provenance, and no claim-ceiling
  changes.
- Projection counts: function `7,588 → 5,401`, nonfunction `18,476 → 15,466`,
  Knowledge search `26,372 → 21,175`; Fire Seed candidates `64 → 64` and
  source records `369 → 370`.
- Human Surface materiality was refreshed to `44` current entries; `4` test-path
  presentation entries were withdrawn from the current surface and retained in
  `materiality-manifest.json` as provenance-only withdrawals.
- Gates: policy unit tests `4/4 PASS`; function closure `46/46 PASS`; nonfunction
  evidence-lineage closure `54/54 PASS`; Knowledge Experience audit and
  determinism `PASS`; Human Surface materiality, Human Surface, Front Door and
  Visibility `PASS`; Fire Seed validation `PASS`; migration validation `PASS`.
- Two deterministic repair rounds were recorded: the migration first
  attempted to read the post-withdrawal projection, then was corrected to read
  the frozen Step 00 commit; then the downstream Human Surface fingerprints and
  four withdrawn test-path entries were refreshed. The final migration report
  contains `5,202` rows.
- Claim ceilings remain unchanged; this is a repository-scoped projection and
  provenance result, not external truth or epistemic acceptance.

## Step 02 — COMPLETE

- Added provider-neutral `PackRegistry`, `PackLoader`, `CapabilityRoute` and
  `PackBus` under `agent_runtime/pack_registry.py`.
- Registered four manifests: `knowledge.r0`, `research.reos-light`,
  `writing.zhiyuan`, and `maintenance.repository`; validation reports `4/4`
  healthy Packs and `10` deterministic capability routes.
- Added CLI `agent-runtime packs list/show/validate` and a standalone
  `validate_pack_registry.py` gate.
- Loading is declarative metadata only: no Pack import or hook execution;
  routing returns a proposal digest and cannot grant permission, executor,
  Owner, truth, or epistemic authority. Active Pack unload is bounded.
- Gates: Pack tests `6/6 PASS`; R0/R1 runtime regression `16/16 PASS`; Pack
  validator, runtime boundary, agentization boundary, and diff check `PASS`.
- Claim ceilings, `EPISTEMICALLY_ACCEPTED=0`, and the deferred live-provider /
  daemon / network boundaries remain unchanged.

## Step 03 — COMPLETE

- Added locked `OperationalMemoryStore` and typed `MemoryEntry` with eight
  operational types: episodic, procedural, owner feedback, failure, rollback,
  approval, Pack usage, and unresolved continuation.
- Each entry carries source run, timestamp, retention, visibility, sensitivity,
  provenance/owner-feedback refs, summary, tags, expiry/forget policy,
  supersession lineage and integrity SHA-256.
- Added append/query/show/supersede/forget/expire/export/audit APIs and CLI
  `memory add/query/show/supersede/forget/export/audit`.
- Secret, prompt and hidden-reasoning material is rejected; forget/expire
  redacts body and references while retaining a bounded tombstone audit;
  capsules are count/character bounded and explicitly not Knowledge truth.
- Gates: operational-memory tests `6/6 PASS`; memory validator, Pack Registry
  regression `6/6`, R0/R1 runtime regression `16/16`, runtime/agentization
  boundaries and diff check `PASS`.
- One targeted repair round fixed prompt-marker rejection and a test fixture
  tag override; no data was persisted outside temporary fixtures.

## Step 04 — COMPLETE

- Added persisted `Supervisor R0`, `EpisodeSpec`, `ChildRunSpec` and
  `EpisodeBudget` around independent R1 child run directories. The Supervisor
  validates DAG acyclicity, child-to-episode capability ceilings and offline
  network boundaries before any child starts.
- Added sequential scheduling with global action/time/output budgets,
  `FAIL_FAST` and `CONTINUE_INDEPENDENT` policies, bounded retries capped at
  three, approval aggregation, explicit executor-instance handoff, durable
  checkpoint/resume and typed episode roll-ups. It never emits generic
  `SUCCESS` and cannot replace a child executor adapter or widen permissions.
- Added CLI `episode start/status/resume/trace/pending-approval`, typed
  `episode approve` and `episode handoff`, plus the Supervisor validator and
  six targeted tests. Recovery preserves R1 journal/idempotency evidence and
  only promotes a child after the R1 terminal state is explicit.
- Gates: Supervisor tests `6/6 PASS`; Supervisor validator, Pack Registry
  regression `6/6`, operational-memory regression `6/6`, R0/R1 runtime
  regression `16/16`, runtime boundary, Agentization boundary and diff check
  `PASS`.
- Three deterministic repair rounds corrected roll-up precedence, explicit
  checkpoint stop/resume behavior and recovery scheduling; no external or
  network action was introduced.

## Step 05 — COMPLETE

- Extended the generic `AgentProfile` contract with allowed Packs,
  preferred/forbidden tool classes, typed approval thresholds, bounded budget
  defaults, update authority and explicit prohibited authority upgrades. The
  legacy R0 profile remains parseable without personality fields.
- Added the three capability profiles `repository-maintainer`,
  `bounded-researcher` and `human-surface-writer` in
  `data/agent-runtime/agent-profiles-r1.json`, with the matching strict schema.
  They are capability configurations, not personality or identity replicas.
- Added `agent_runtime.profile` projection. It intersects declared and Profile
  capabilities, can lower action/write/output budgets, can only strengthen
  typed approval classes, and rebinds the action-plan digest after a legal
  approval tightening. Pack selection is allowlist-only.
- Wired Profile projection into `Supervisor.start(..., profiles=...)` and CLI
  `episode start --profiles`; a real projected write waits for typed approval,
  while the bounded researcher cannot acquire write capability.
- Gates: Profile tests `5/5 PASS`; Profile validator, Supervisor validator,
  Pack Registry regression, operational-memory regression, R0/R1 runtime
  regression `16/16`, runtime boundary, Agentization boundary and diff check
  `PASS`.
- One deterministic repair round canonicalized Pack ordering and tightened the
  action-plan digest assertion; no permission or Charter authority was added.

## Step 06 — COMPLETE

- Added versioned `GatewayRequest` / `GatewayResponse` schemas for
  `reasoner-gateway-r1`, deterministic request digests, bounded context
  capsules, and read-only available Pack/capability catalogs.
- Added `ReasonerGateway` validation around deterministic scripted,
  literal-argv subprocess and adversarial offline adapters. The Gateway only
  accepts typed plan/action proposals, verifies packet lineage and plan hash,
  rejects unknown capabilities, self-approved authority, forged completion and
  generic `SUCCESS`, and treats provider/model metadata as telemetry only.
- Added typed handling for schema mismatch, digest mismatch, malformed JSON,
  oversized output, timeout, subprocess crash and secret/prompt/hidden-
  reasoning material. R1 supports `gateway-scripted` and `gateway-jsonl` while
  the existing local executor remains the sole action authority.
- Gates: Gateway tests `4/4 PASS`; Gateway validator, Profile/Agent Runtime
  regression `43/43 PASS` across the Step 00–05 focused suite, Pack Registry,
  operational-memory, Supervisor, runtime boundary, Agentization boundary and
  diff check `PASS`.
- One deterministic repair round tightened subprocess start failure typing;
  no live provider, API key, network action or provider-specific dependency was
  introduced (`OPTIONAL_LIVE_SMOKE=NOT_RUN`).

## Step 07 — COMPLETE

- Added `PackAwareRouter`, `PackActionProvenance` and
  `PackValidationReceipt`. Plans now name a unique loaded manifest route,
  declared object type, validator and optional hook; validator and hook calls
  remain proposals and never import or execute domain code through the Bus.
- Gateway responses now carry `requested_packs`; the read-only catalog check
  rejects a Pack outside the available catalog before any load or action.
  Profile-scoped routers expose only selected loaded Packs.
- Added three cross-Pack negative boundaries: Knowledge claim validation cannot
  assert truth or runtime authority; Writing surface quality cannot assert
  epistemic acceptance; REOS LIGHT workflow validation cannot assert Owner
  acceptance. All results remain declared-scope receipts.
- Gates: Pack-aware routing tests `4/4 PASS`; Gateway tests `4/4 PASS`; focused
  Step 00–06 regression `47/47 PASS`; routing, Gateway, Profile, Supervisor,
  Pack, Memory, runtime boundary, Agentization boundary and diff validators
  `PASS`.
- One deterministic repair round corrected a validator entrypoint to match the
  live Knowledge Pack manifest; no cross-domain authority was added.

## Step 08 — COMPLETE

- Added the source-driven `agent-platform-r2-propagation-contract.json` and
  strict schema. Its four fixtures have explicit source domains, affected
  projections and forbidden projections for runtime-only, Knowledge claim,
  Writing surface and Pack manifest changes.
- Updated the declared propagation topology to `1.5.0` with non-map-visible
  R2 Runtime/Pack relations. The component registry is `1.5.0`, the R2 Runtime
  node now names the bounded R2 surface, and the registered maintenance Pack is
  represented by the visible Domain Pack Contract rather than added as a new
  public architecture layer. The derived system map remains `64` visible
  nodes / `70` typed edges.
- Added `impact_contract.py` blast-radius derivation and historical sealed-source
  handling. Tasks 104/105/106 retain their own append-only system-map baselines;
  their old NO_IMPACT decisions are not rewritten by the R2 topology change.
- Added the generator source contract/schema, registered
  `agent_platform_r2_blast_radius`, deterministic report and standalone
  validators. The stale pre-existing `compute_change_propagation` registry
  digest was repaired to the live canonical tool digest.
- Gates: blast-radius fixtures `5/5 PASS`; change-propagation regression
  `57/57 PASS` (one historical skip); reconciliation `16/16 PASS`; all five
  changed JSON contracts schema-valid; system-map generator, blast-radius
  report, generator-source contract and reconciliation checks `PASS`.
- Two deterministic repair rounds handled historical impact-spec drift and
  regenerated the report after source-authority hash changes. No network,
  remote mutation, Knowledge claim, Owner, truth or epistemic authority was
  introduced.

## Step 09 — COMPLETE

- Added the real offline R2 pilot at
  `agent_runtime/pilots/r2_repository_maintenance.py`. It creates a disposable
  source repository, makes a fresh local clone before supervision, and drives
  the `audit → repair → validate` dependency DAG through the checked-in
  `repository-maintainer` Profile.
- The audit recorded one typed `MISSING_HASH` finding. The approved repair
  added the local README SHA-256 and a repair receipt; validation produced a
  typed PASS report. The main episode reached
  `EPISODE_COMPLETED_VALIDATED` with `FAIL_FAST`, four typed approvals, one
  checkpoint and a handoff from `instance-1` to
  `repair-executor-instance-2`.
- A `post_execute_before_persist` repair fault was captured at the Supervisor
  approval boundary as `EPISODE_CHECKPOINTED_RESUMABLE`; resume reconciled the
  durable postimage without duplicating the repair. The approval-path capture
  closes the R0/R1 integration gap found by the first pilot attempt.
- The adversarial `CONTINUE_INDEPENDENT` episode retained two independent
  `CAPABILITY_UNAVAILABLE` child failures for a denied network request and
  denied remote Git mutation. Gateway probes for permission expansion and
  forged completion were rejected; the protected local file was preserved.
- `durable-memory.jsonl` contains typed FAILURE and EPISODIC records, and the
  exported capsule is bounded operational recall only. The committed receipt
  proves only this offline fixture: `network_allowed=false`,
  `remote_mutation=false`, `git_push_invoked=false`, and sanitized paths.
- Gates: R2 pilot plus Supervisor tests `7/7 PASS`; pilot receipt validator,
  Supervisor validator, Pack Registry validator and Operational Memory
  validator `PASS`; the committed Human Report preserves the observation
  ceiling and does not claim production safety, Owner acceptance, truth or
  epistemic acceptance.

### Step 09 decision

`STEP_09_OFFLINE_MULTI_RUN_EPISODE_COMPLETE`; proceed to Step 10, whole-repo
Agent-first/Human Surface convergence. The commit and exact remote SHA are
recorded in the ledger at the Step 09 checkpoint below.

## Step 10 — COMPLETE

- Synchronized the root `AGENTS.md`, `.github/README.md`, AI cold-start and
  handoff surfaces, `llms.txt`, `ARCHITECTURE.md`, current-state, Human Reading,
  Results and Results Book identity chapter around the bounded Agent Platform
  R2 sentence. The final main identity remains pending Step 12; the task-branch
  pre-release state is explicitly not a main merge receipt.
- Added the R2 architecture spine and red-line explanation across Kernel,
  Runtime, Supervisor, Memory, Reasoner Gateway, Profile, four Pack READMEs and
  the agentization boundary. Knowledge is positioned as the first large Domain
  Pack, not the system本体; no L7 or truth/Owner/epistemic authority was added.
- Kept the existing unique registry-derived system map as the only complete
  graph: map `0.6.0`, `76` registry components, `64` visible nodes, `70` typed
  edges and `12` hidden components represented by visible nodes. No second map
  or parallel governance surface was introduced.
- Rebuilt affected deterministic projections with their official generators:
  Human Surface materiality now has `48` active entries and `4` retained
  `PLATFORM_CODE_EXCLUDED` provenance withdrawals; Knowledge Experience has
  `367` cards, `292` changes, `308` layered readings, `21,175` search records
  and `22,556` checked links. The claim-browser generator now preserves prior
  withdrawal provenance on full rebuilds.
- Gates: Human Surface structure `48/48` entries PASS; Front Door and
  Visibility PASS; R2 Human Surface validator/test `1/1 PASS`; system-map
  derived check PASS; Knowledge Experience audit PASS; Knowledge Experience
  two-pass determinism PASS (`308` sources, `75` outputs); materiality and
  claim-browser generator checks PASS; Runtime/Agentization boundary PASS;
  state changelog and `git diff --check` PASS.
- Claim ceilings remain unchanged: this is repository navigation and generated
  projection evidence only. It does not establish general intelligence,
  long-term autonomy, production safety, external validity, Owner acceptance,
  causality or `EPISTEMICALLY_ACCEPTED=0` upgrade.

### Step 10 decision

`STEP_10_AGENT_PLATFORM_HUMAN_SURFACE_CONVERGENCE_COMPLETE`; proceed to Step 11,
adversarial, fault-injection and full regression review. This task-branch
checkpoint is committed and pushed only after the ledger and exact SHA are
written below.

## Step ledger

| Step | State | Commit | Remote SHA | Gate summary |
| --- | --- | --- | --- | --- |
| 00 | COMPLETE | `8cc9291c0af9d3df686628bfd7dbae365523e327` | `8cc9291c0af9d3df686628bfd7dbae365523e327` | 16 runtime tests and boundary gates PASS |
| 01 | COMPLETE | `94a74caf0bcda84cccb60f820f9f1abbbf068615` | `94a74caf0bcda84cccb60f820f9f1abbbf068615` | Admission policy, provenance migration, projection rebuild, and closure gates PASS |
| 02 | COMPLETE | `b8f1b76c11a80e9e6b6bb320789f92ca6b4317e1` | `b8f1b76c11a80e9e6b6bb320789f92ca6b4317e1` | Pack Registry/Bus, four Pack manifests, CLI and runtime regression gates PASS |
| 03 | COMPLETE | `7e8ac52122e815751870ed9b7d3354f7787d787e` | `7e8ac52122e815751870ed9b7d3354f7787d787e` | Cross-run operational memory, bounded capsule, redacting forget and regression gates PASS |
| 04 | COMPLETE | `f6d93c119bde1049aaf032b0871479fa2fc86510` | `f6d93c119bde1049aaf032b0871479fa2fc86510` | Supervisor R0 DAG, budgets, approvals, bounded retry/handoff, recovery and regression gates PASS |
| 05 | COMPLETE | `a16c2c3ed61e825ec3e7e14d24cd85f205f027bc` | `a16c2c3ed61e825ec3e7e14d24cd85f205f027bc` | Agent Profile R1 registry, legal scope projection, Pack selection and profile-driven approval gates PASS |
| 06 | COMPLETE | `b1710307f17160cb820fb54876c0ff75ee285f3f` | `b1710307f17160cb820fb54876c0ff75ee285f3f` | Reasoner Gateway R1 schema, digest, bounded capsule, provider-neutral adapters and adversarial gates PASS |
| 07 | COMPLETE | `64e20ef250397a9aebefa5a6f6cf475c279d67a1` | `64e20ef250397a9aebefa5a6f6cf475c279d67a1` | Pack-aware catalog/provenance/routing and three cross-Pack authority negative gates PASS |
| 08 | COMPLETE | `71ffd9aa5e185d0eddc53e185f2cfc931f16a0df` | `71ffd9aa5e185d0eddc53e185f2cfc931f16a0df` | Four source-contract blast-radius fixtures, topology/impact/generator updates, historical reconciliation and map gates PASS |
| 09 | COMPLETE | `983aff0b280313c79d82484f609e5a45d721fd63` | `983aff0b280313c79d82484f609e5a45d721fd63` | Offline fresh-clone A/B/C episode, approval-path fault checkpoint, executor handoff, operational memory and adversarial episode PASS |
| 10 | COMPLETE | pending until checkpoint commit | pending | Human/AI surface R2 convergence, deterministic projection rebuilds, unique map and Knowledge/Front Door/boundary gates PASS |
| 11 | PENDING | — | — | — |
| 12 | PENDING | — | — | — |

All step rows are updated only as part of the corresponding step checkpoint;
each checkpoint is committed and pushed before the next step begins.
