# IGNITION-20260827-143 Step 01 — Campaign Ledger and Qualification States

Status: PASS.

The campaign uses the existing provider-neutral Executor Admission plane and
adds one minimal, task-scoped qualification record at
`ignition/data/operations/iterations/143/executor-qualification-campaign-r1.json`.
It does not create a second scheduler, agent shell, provider gateway or
obligation registry.

The ledger records the only allowed family states:
`NOT_INSTALLED`, `BLOCKED`, `QUALIFYING`, `LIVE_SELECTABLE`, `ATTEMPTED`,
`VALIDATED`, and `TERMINAL_BLOCKED`. Gemini, Hermes and OpenClaw are
`QUALIFYING` with the exact prior blocker set and deterministic blocker
fingerprint; Codex is `TERMINAL_BLOCKED` by the unchanged Task140 same-family
blind-retry policy; GitHub Copilot CLI remains `NOT_INSTALLED` and is not
installed.

The campaign policy permits at most three different families, at most one
attempt per family, and stops immediately on the first exact validated
completion. The execution contract binds this campaign to the refreshed
`origin/relay/current` task definition and formal baseline
`b359580fe31866bc04eeb24911011e0baba9b66d`.

The record and JSON Schema are validated by
`ignition/tools/validate_executor_qualification_campaign.py`; blocker
fingerprints are recomputed from sorted public blocker codes. No auth content,
secret, configuration or billing state was read or changed; no executor,
channel, browser, inference or task-workspace action was started.

Claim ceiling: repository-local qualification campaign state only. Installed
status and prior blockers do not prove authentication, live selectability,
inference, validated completion or external truth.
