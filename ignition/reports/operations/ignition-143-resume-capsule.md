# IGNITION-143 Resume Capsule

## Parking point

The architecture and external-executor qualification phase is closed at the verified Task142 baseline. Publication production is the active work mode of Task143. The external-Agent line is `OWNER_DEFERRED_NOT_FAILED`: this is a deliberate parking decision, not a claim that qualification is solved or disproved.

The frozen formal baseline is `Arvin-liu/when-systems-catch-fire` `refs/heads/main` at `b359580fe31866bc04eeb24911011e0baba9b66d`. The architecture identity remains `os-control-plane-r8-task-lifecycle-decoupling-executor-admission-r1`, the latest architecture-changing task remains Task142, and the Current map remains `0.16.0`.

## What remains open

`LIVE_EXTERNAL_INVOCATION` remains `OPEN`. The historical ledger-derived projection retains six attempts, zero validated completions, zero unreconciled attempts and two observation-incomplete outcomes. Its historical next action was `RUN_DYNAMIC_EXECUTOR_ADMISSION`; its current operational action is now `OWNER_DEFERRED_REQUIRES_EXPLICIT_REOPEN_AND_LOCAL_ENVIRONMENT_PREPARATION`.

The Task142 census remains the source of the executor snapshot: 14 candidates were observed. Gemini remains blocked by auth-source, adapter-attestation and public-auth-status boundaries; Hermes remains blocked by auth-source, re-attestation and structured-result boundaries; Openclaw remains blocked by auth-source, cleanup, structured-result and workspace/channel boundaries; Codex is technically admitted in the census but excluded by the existing same-family retry policy. No Task143 live process or inference was started.

## How to resume later

A future task may resume this line only after both conditions hold:

1. the Owner explicitly reopens external-Agent qualification;
2. the local environment is deliberately prepared, installed and attested before any qualification or live attempt.

The future task must re-read the machine capsule, the phase-closure record, the open-obligation registry, the historical live projection and ledger, the Task142 census, the executor inventory and the current identity contract. It must re-establish disposable workspace, read-only scope, auth-source separation, structured-result capture, independent validation and cleanup boundaries from current evidence. The capsule itself never authorizes an attempt.

## Evidence paths

- Machine capsule: `ignition/data/operations/iterations/143/resume-capsule-r1.json`
- Phase state: `ignition/data/operations/iterations/143/phase-closure-state-r1.json`
- Phase-closure audit: `ignition/data/operations/iterations/143/step01-phase-closure.json`
- Open-obligation registry: `ignition/data/operations/open-obligation-registry-r1.json`
- Historical projection: `ignition/data/operations/iterations/141/live-current-projection-r3.json`
- Historical attempt ledger: `ignition/data/operations/iterations/139/live-attempt-ledger.jsonl`
- Executor census: `ignition/data/operations/iterations/142/local-executor-census-r2.json`
- Executor inventory: `ignition/data/agent-federation/executor-inventory-r1.json`
- Current identity: `ignition/data/architecture/current-system-identity.json`

Claim ceiling: this capsule is repository-local continuity and resume evidence only. It does not establish production readiness, validated completion, external truth, Owner acceptance or epistemic acceptance.
