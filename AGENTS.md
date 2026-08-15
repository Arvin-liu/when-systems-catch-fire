# Agent operating boundary

Read `ignition/AI-START-HERE.md`, `ignition/STATE-CHANGELOG.md` (baseline and recent deltas), `ignition/AI-HANDOFF.md`, `ignition/llms.txt`, `ignition/ITERATION.md` and the active task command before state-changing work. The state delta log is a high-priority recovery surface: current main merges must append one short delta in the same iteration.

Current iteration method is `1.4.0` and Current system map is `0.6.0`. Method `1.3.0` and maps `0.5.0`/`0.4.0`/`0.3.0`/`0.2.0` are Historical; method `1.2.0` and map `0.1.0` are earlier Historical.

## Task 121 Agent Platform R2 cold start

The current task-branch engineering projection is a bounded, auditable and
recoverable Agent Platform prototype. Knowledge Governance is its first large
Domain Pack, not the whole system. Before acting, read
`ignition/docs/architecture/agent-platform-r2.md`, the Kernel and Runtime
READMEs, all four `ignition/packs/*/manifest.json` files, the R2 pilot receipt,
the propagation contract and the night-shift ledger. Until Step 12 fast-forward,
fresh-clone replay and formal receipt close, this is not a claim that `main` has
moved. `EPISTEMICALLY_ACCEPTED=0` remains unchanged.

Keep these boundaries explicit: `Kernel ≠ Knowledge`, `Reasoner ≠ Executor`,
`Pack ≠ truth authority`, and `pilot ≠ general intelligence`. R2 does not
authorize live providers, daemons, multi-Agent concurrency, vector memory,
network/browser actions, automatic Git mutation, physical Pack migration,
Owner acceptance or external validity.

For Q32I profiles, keep authority, execution capability and validation capability separate. Manual or external validation must not invoke a local validator. A local `validator_argv` is permitted only when it is complete, exists, runs successfully and validates the declared component responsibility. Never substitute the incomplete generic `python3 ignition/tools/validate_protocol_canonical.py --check` command.

Tests, CI, cache and artifacts are repository evidence only. They do not perform independent review, merge a PR, establish Current state or prove real-world truth or causality.

Every formal iteration merged to `main` appends one short, validated delta to `ignition/STATE-CHANGELOG.md`; the log is an AI recovery surface, not a replacement for canonical registries or claim records. A formal main merge without a delta is not a synchronized project state.

Iteration method 1.4.0 Continuous Stage Snapshot Publication is Current. If a task produces a real intermediate result, an Agent may submit a schema-valid stage snapshot request, but must keep `agent_claims_published_to_main=false`. Never infer Accepted, Current, Activated, capability availability or candidate payload merge from a stage snapshot or homepage visibility.

For any function/model/theorem/formula/law or strong cross-domain claim, apply `ignition/docs/foundation/claim-governance-and-function-identity.md` and the task-99 canonical `ignition/data/foundation/function-assets/identity-cards.jsonl`. Automatic census identities are candidates only; explicit quarantine is not validation; uncertain gates remain `REQUIRES_HUMAN_REVIEW`. T2, D127, D182—D190 and D260 use the task-98 correction overlay. Never claim that the current gate model unifies the forces or proves grand unification universally impossible.

For every non-function theorem, law, mechanism, causal judgment, impossibility claim, cross-domain correspondence, prediction, empirical assertion or ontology claim, use the task-100 `ignition/data/foundation/nonfunction-claims/claim-registry.jsonl` and future-claim admission protocol. Preserve all thirteen gates, evidence lineage, M/E independence, replication status, dependency closure, disposition and public claim ceiling. Registry closure through explicit quarantine is not content validation; renamed structural or meta language cannot revive a withdrawn conclusion.

Task 102 makes `ignition/KNOWLEDGE/README.md` the no-path human entry. Any meaningful knowledge change must update the deterministic What's New, subject map, asset card, applicable reading layers, aliases/supersession, source and bidirectional dependency projection. Run both knowledge-experience build/check and validator; never hand-edit generated `ignition/KNOWLEDGE/` or its machine indexes.

All agents inherit `K13_ASSERTION_NON_ESCALATION` / `ASSERTION_INFLATION_GUARD`: no workflow, engineering, writing, repeated citation, cross-domain correspondence, model elegance or consensus may auto-upgrade a claim; workflow, semantic, logic, proof, evidence, scope and provenance remain separately recorded; M/E and the nine state axes remain independent; withdrawn or quarantined conclusions cannot rebound. When evidence is insufficient, preserve, downgrade, quarantine, open-question or explicitly mark uncertainty.
