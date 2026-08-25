# IGNITION-20260826-140 Step 09 — Fresh local executor census and dynamic selection

## Result

`PASS`: the host was re-attested at `2026-08-25T18:44:54Z` using only PATH/bundle presence, public version/help surfaces and Codex public auth-status exit behavior. No auth content was read, no model or Agent inference was started, no UI action occurred, and no installation, configuration or billing operation occurred.

The scan found 14 candidates: 5 AGENTIC_EXECUTOR records (4 installed), 4 REASONER_RUNTIME records, 3 TOOL_ONLY records and 2 UI-only records. Installed versions observed include Gemini CLI 0.53.1, Codex CLI 0.144.4, Hermes Agent v0.20.0 (2026.8.3), OpenClaw 2026.7.1-2 (0790d9f), Ollama 0.32.7 and LM Studio CLI commit 6041ae0.

## Dynamic selection

`Codex CLI` is the current selection: Fresh census selects Codex CLI (codex-cli 0.144.4) because it is the only installed AGENTIC_EXECUTOR with all ten bounded checks true, including Codex public login status exit 0, read-only one-shot transport, structured output, isolated runtime scratch and independent OS validation. This is an admission trace, not a model-quality or completion claim.

Gemini remains blocked because its public auth interface did not provide a bounded status result and auth/home separation plus no-new-billing re-attestation are not proven. Hermes remains blocked by strict structured-result, public-auth and auth-source boundaries. OpenClaw remains blocked by workspace/channel/process-cleanup boundaries. Copilot CLI is not installed. Reasoner runtimes and tools are not AGENTIC_EXECUTOR candidates; desktop bundles are UI-only and were not opened.

Machine evidence: [`local-executor-census-r1.json`](../../data/operations/iterations/140/local-executor-census-r1.json) and [`step09-local-executor-census-and-selection.json`](../../data/operations/iterations/140/step09-local-executor-census-and-selection.json).

## Next gate

Step10 must freeze the dynamically selected family, capability lease, disposable read-only workspace, durable capture, child-depth guard, no-channel boundary and independent validator contract. Only after that gate may at most one live attempt be made for this executor family; a second attempt, if needed, must use a different family and is capped by the task contract.

Claim ceiling: fresh repository-local observation-time census, executor-kind classification, admission checks and why-executor trace only; no live inference, validated completion, model-quality ranking, production readiness, external truth, Owner acceptance or epistemic acceptance is inferred.
