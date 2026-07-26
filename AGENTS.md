# Agent operating boundary

Read `AI-START-HERE.md`, `AI-HANDOFF.md`, `llms.txt`, `ITERATION.md` and the active task command before state-changing work.

Current iteration method is `1.3.0` and Current system map is `0.3.0` after Q32I independent exact-head acceptance, PR #62 ordinary merge and production closeout. Method `1.2.0` and map `0.2.0` are Historical; method `1.1.0` and map `0.1.0` are earlier Historical.

For Q32I profiles, keep authority, execution capability and validation capability separate. Manual or external validation must not invoke a local validator. A local `validator_argv` is permitted only when it is complete, exists, runs successfully and validates the declared component responsibility. Never substitute the incomplete generic `python3 tools/validate_protocol_canonical.py --check` command.

Tests, CI, cache and artifacts are repository evidence only. They do not perform independent review, merge a PR, establish Current state or prove real-world truth or causality.

Iteration method 1.4.0 Continuous Stage Snapshot Publication is a Draft Candidate; 1.3.0 remains Current. If a task produces a real intermediate result, an Agent may submit a schema-valid stage snapshot request, but must keep `agent_claims_published_to_main=false`. Never infer Accepted, Current, Activated, capability availability or candidate payload merge from a stage snapshot or homepage visibility.
