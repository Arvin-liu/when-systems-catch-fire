# IGNITION-20260826-140 — Step 10 Dynamic Live Admission Freeze

Status: `PASS`

The admission gate revalidated the Task140 census and selected the currently admitted family from `local-executor-census-r1.json`; it did not bind the task contract to a brand before census. The current selection is Codex CLI (`external.codex`, `codex-cli 0.144.4`) because its public login-status probe returned exit `0` and all ten bounded admission checks passed. The gate remains fail-closed if the fresh census changes that selection.

The preflight created a disposable synthetic read-only fixture, observed its write guard, exercised public Codex version/help through the bounded transport, froze a capability lease with effective capability `repo.read`, built the strict JSONL/output-schema argv, verified isolated attempt runtime scratch and host durable-capture support, proved the auth source is a read-only reference, and passed the one-level child-depth guard. The independent validator self-test passed for the four public fields `nonce`, `line_count`, `field_value` and `checksum_prefix`.

No live executor process or model inference was started: `inference_started=false`, `probe_calls=2`, capture/live dispatch calls were not made, the formal and control repositories were not used as a child workspace, and no auth content, configuration, billing or installation state was changed.

The frozen attempt policy allows at most two different executor families, at most one attempt per family, forbids blind retry, and stops immediately after the first exact `LIVE_READONLY_VALIDATED_COMPLETION`. The current projection remains five attempts, zero validated completions, zero unreconciled attempts and two observation-incomplete records, with unknown external effect preserved.

Claim ceiling: Task140 repository-local admission, capability-lease, filesystem-domain and validator-freeze evidence only; no live result, validated completion, external truth, production readiness, Owner acceptance or epistemic acceptance is inferred.
