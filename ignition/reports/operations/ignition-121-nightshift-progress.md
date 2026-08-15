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

## Step ledger

| Step | State | Commit | Remote SHA | Gate summary |
| --- | --- | --- | --- | --- |
| 00 | COMPLETE | `8cc9291c0af9d3df686628bfd7dbae365523e327` | `8cc9291c0af9d3df686628bfd7dbae365523e327` | 16 runtime tests and boundary gates PASS |
| 01 | COMPLETE | `94a74caf0bcda84cccb60f820f9f1abbbf068615` | `94a74caf0bcda84cccb60f820f9f1abbbf068615` | Admission policy, provenance migration, projection rebuild, and closure gates PASS |
| 02 | COMPLETE | `b8f1b76c11a80e9e6b6bb320789f92ca6b4317e1` | `b8f1b76c11a80e9e6b6bb320789f92ca6b4317e1` | Pack Registry/Bus, four Pack manifests, CLI and runtime regression gates PASS |
| 03 | COMPLETE | `7e8ac52122e815751870ed9b7d3354f7787d787e` | `7e8ac52122e815751870ed9b7d3354f7787d787e` | Cross-run operational memory, bounded capsule, redacting forget and regression gates PASS |
| 04 | COMPLETE | `f6d93c119bde1049aaf032b0871479fa2fc86510` | `f6d93c119bde1049aaf032b0871479fa2fc86510` | Supervisor R0 DAG, budgets, approvals, bounded retry/handoff, recovery and regression gates PASS |
| 05 | COMPLETE | pending until checkpoint commit | pending | Agent Profile R1 registry, legal scope projection, Pack selection and profile-driven approval gates PASS |
| 06 | PENDING | — | — | — |
| 07 | PENDING | — | — | — |
| 08 | PENDING | — | — | — |
| 09 | PENDING | — | — | — |
| 10 | PENDING | — | — | — |
| 11 | PENDING | — | — | — |
| 12 | PENDING | — | — | — |

All step rows are updated only as part of the corresponding step checkpoint;
each checkpoint is committed and pushed before the next step begins.
