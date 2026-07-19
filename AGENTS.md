# Agent operating boundary

Read `AI-START-HERE.md`, `AI-HANDOFF.md`, `llms.txt`, `ITERATION.md` and the active task command before state-changing work.

Current iteration method is `1.2.0`; `1.1.0` is Historical. Q32I method `1.3.0` and map `0.3.0` are Draft candidates, not independently accepted, not merged and not Current. Current map is `0.2.0`.

For Q32I profiles, keep authority, execution capability and validation capability separate. Manual or external validation must not invoke a local validator. A local `validator_argv` is permitted only when it is complete, exists, runs successfully and validates the declared component responsibility. Never substitute the incomplete generic `python3 tools/validate_protocol_canonical.py --check` command.

Tests, CI, cache and artifacts are repository evidence only. They do not perform independent review, merge a PR, establish Current state or prove real-world truth or causality.
