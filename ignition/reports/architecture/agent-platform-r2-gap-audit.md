# Agent Platform R2 gap audit — IGNITION-20260816-121 Step 00

## Audit boundary

This is a repository-scoped baseline audit performed from a fresh worktree at
`2becca3ffd93d6ca1e147a75c159e476f4686f5d`. It records engineering structure,
deterministic projections, and open implementation work. It does not establish
external validity, general intelligence, production readiness, Owner acceptance,
or `EPISTEMICALLY_ACCEPTED`.

The task branch is
`codex/ignition-121-agent-platform-r2-nightshift-20260816`. Formal `main` was
not modified during Step 00.

## Baseline evidence

| Surface | Baseline |
| --- | ---: |
| `agent_kernel/` tracked files | 5 |
| `agent_runtime/` tracked files | 14 |
| Foundation function census records | 7,588 |
| Foundation nonfunction claim records | 18,476 |
| Knowledge Experience search records | 26,372 |
| Fire Seed census records | 7,243 |
| Foundation tracked text files scanned | 3,484 |
| Nonfunction tracked files accounted | 3,802 |
| Agent Runtime R0/R1 tests | 16/16 passed |
| Agent Runtime boundary validator | PASS, 17 files scanned |
| Agentization boundary validator | PASS, 75 components |

The previous R1 commit changed 91 generated or knowledge-facing files. Its
projection delta included 132 new function-census records, a net 39-record
nonfunction registry change, 8,004 additions and 7,833 removals in the
Knowledge Experience search index, and 161 additions and 148 removals in the
Fire Seed census. This is the measured evidence for the blast-radius problem;
it is not treated as a causal or epistemic result.

## Current platform shape

### CRITICAL

1. **Corpus admission is implicit rather than typed.** The current Foundation
   and Knowledge Experience projections contain platform references: 186
   function-census records include `agent_kernel/` or `agent_runtime/`
   occurrence paths, 42 nonfunction records include those paths in evidence,
   and 228 Knowledge Experience records point at those sources. The existing
   Agent Runtime boundary validator protects imports and authority direction,
   but does not decide whether a source is eligible for the Knowledge Pack.
2. **There is no runtime Pack Registry or Bus.** `DomainPackManifest` is a
   kernel-owned record and `packs/knowledge/manifest.json` is a static manifest;
   discovery, load/unload, capability routing, validator hooks, health checks,
   and dependency checks are not yet a single runtime contract.
3. **Memory is run-local.** R1 persists action journals, approvals, leases,
   checkpoints, and resume material, but there is no typed cross-run
   operational memory with retention, supersession, forget, and bounded export.
4. **There is no Supervisor.** R1 executes one `R1RunSpec`; episode identity,
   child-run DAGs, aggregate budgets, independent continuation, handoff, and
   terminal roll-up do not exist.

### STRUCTURAL

1. Agent Profile is an R0 kernel contract and is not yet projected into runtime
   and supervisor scopes with allowed packs, approval thresholds, budgets, and
   retention policy.
2. The JSONL transport is a useful R1 adapter but not yet a version-negotiated
   Reasoner Gateway with request digests, context capsules, output limits,
   adversarial adapters, and an explicit no-execution boundary.
3. The existing topology includes Agent Runtime and Domain Pack relations, but
   generator contracts do not yet express domain-specific affected sets or
   reject an unexplained cross-domain projection.
4. Public architecture and cold-start surfaces describe the R0/R1 boundary,
   but do not yet present Supervisor, persistent operational Memory, Pack Bus,
   and Gateway as one Agent Platform spine.

### DEFER

The task explicitly defers live provider APIs and secrets, vector storage,
Telegram/OpenClaw/Hermes daemons, browser or internet automation, automatic
remote Git mutation, persona claims, Charter mutation, and any epistemic or
Owner-acceptance upgrade. These remain hard boundaries for R2.

## Required R2 closure tests

The remaining steps must make these properties executable, not merely
documented:

- runtime-only source changes do not create new Knowledge Pack assets unless a
  typed admission record explicitly allows them;
- a Pack can be discovered, validated, loaded, and routed without import side
  effects or authority expansion;
- operational memory is typed, integrity-checked, bounded, supersedable, and
  forgettable without becoming a truth registry;
- Supervisor resumes a persisted multi-run DAG after process interruption and
  keeps child permissions bounded;
- Reasoner output is a proposal only, with malformed, oversized, timed-out,
  forged, and self-escalating responses rejected;
- Pack validators cannot upgrade claims, permissions, or epistemic status;
- propagation tests distinguish runtime, knowledge, writing, and manifest
  changes and report expected affected sets;
- the offline episode and fresh-clone replay preserve negative outcomes and
  `EPISTEMICALLY_ACCEPTED=0`.

## Step 00 conclusion

`STEP_00_BASELINE_COMPLETE`. The current R0/R1 gates pass, and the audit found
the critical gaps that authorize implementation of Step 01. No implementation
or generated knowledge projection was changed in this step.
