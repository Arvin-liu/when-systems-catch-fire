# IGNITION-20260827-142 Step 04 — Provider-Neutral Executor Admission

Status: PASS.

The admission contract is now provider-neutral. It distinguishes `AGENTIC_EXECUTOR`, `REASONER_RUNTIME`, `TOOL`, and `UI_SURFACE`; only an agentic executor can enter the live-eligible pool. Admission requires public authentication, auth separation, strict argv and structured-result contracts, disposable read-only workspace, durable capture, exact validator binding, cleanup, permission ceiling, exact result binding, and a proven no-effect scope.

The live policy is explicit: at most two total synthetic/read-only attempts, at most one per family, child spawning denied, all channels/browser/remote-Git/configuration/billing effects denied, and immediate stop after the first exact validated completion. The result-binding contract requires task, dispatch, attempt, executor, family, lease, workspace, capture, structured-result, and validator references to match one attempt.

Step 04 contains only the contract and a blocked placeholder. It performs no executor probe or invocation. The contract and validator are `ignition/data/operations/executor-admission-contract-r1.json` and `ignition/tools/validate_executor_admission_contract.py`.
