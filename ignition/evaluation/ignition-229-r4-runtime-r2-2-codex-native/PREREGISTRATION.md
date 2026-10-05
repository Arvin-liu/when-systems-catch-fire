# Task229-R4 Runtime Preregistration R2.2 — Local Provider Tool Inventory Proof

Status: local tool inventory proof passed in two complete fresh repetitions; Formal R2.2 candidate remains Draft-only, with no live execution started.

## Marker

`TASK229_R4_RUNTIME_PREREGISTRATION_R2_2_LOCAL_TOOL_PROOF_FROZEN_EXECUTION_NOT_STARTED`

## Exact base and scope

- Formal repository: `Arvin-liu/when-systems-catch-fire`.
- Parent: open Draft PR #247, unmerged; exact parent head `ef819228adf52bd162ba834095fb2489b348cb8e`.
- Branch: `work/IGNITION-20261005-229-R4-runtime-prereg-r2-2-codex-native`.
- This package records only a local Codex host-side request serialization proof. It does not change the frozen R4 scientific inputs, 18-unit order, thresholds, outcomes, prompts, bindings, references, schemas or evaluator. CI compares the frozen R0 scientific subtree and R1 package against their pinned baselines.

## Codex identity and upstream contract

The runtime was exactly `codex-cli 0.159.2` at `/Users/zhiyuan/.local/lib/node_modules/@openai/codex/bin/codex.js`, with SHA-256 `61b0194f3bb6534439c8d26a3ed57d0805f84b884588b761795323eeb92fcf70`. Upstream source is pinned to `openai/codex@rust-v0.159.2`; exact tag, peeled commit and source blob SHAs are in `proof-receipt.json`. The temporary structured request implementation is the reference for thread-level no-tool isolation.

## Corrected local configuration proof

Each complete repetition wrote valid TOML to the exact `$CODEX_HOME/config.toml` path in a fresh isolated root. Before `thread/start`, `realpath(config_written) == realpath($CODEX_HOME/config.toml)` and TOML parsing passed. The exact user layer and provider origins appeared in `config/read`; effective provider ID was `local_loopback`, `base_url` was `http://127.0.0.1:<per-run-port>/v1`, `requires_openai_auth=false`, retries were zero, web search was disabled, and configured MCP servers were absent. Both raw effective-config responses were persisted and hashed before interpretation. No `OPENAI_API_KEY`, copied ChatGPT auth or credential environment was provided.

## Thread isolation and decisive request

After the effective-config gate passed, each run started one fresh ephemeral thread with approval `never`, read-only sandbox, network access disabled, empty runtime workspace roots/environments/dynamic tools/selected capability roots, disabled discovered MCP servers, and accepted root feature/tool disables. The only turn input was `Return exactly LOCAL_TOOL_INVENTORY_PROBE_OK.`

The decisive evidence is the exact HTTP model request captured by Codex 0.159.2's host-side client at the loopback mock before request JSON parsing. In both completed repetitions `tools` was an empty array and no non-empty tool namespace was present, including shell/exec/unified-exec, web/search, MCP/dynamic, app/plugin/memory/multi-agent/image/request-input/update-plan, or workspace/environment capability authority. The mock returned a deterministic synthetic response; this does not constitute external model inference.

## Two-run result and residual attempt

Both complete fresh repetitions passed the effective local-provider gate, model-facing empty-tools assertion, isolation assertions, assistant payload comparison, normalized request comparison and clean process exit. The canonical normalized request hashes match after excluding the serialized `turn_started_at_unix_ms`; UUIDs, request IDs, thread/turn/response IDs and loopback port are also run-specific. Per-artifact hashes are in `proof-receipt.json`; full manifests are recorded for each run.

For transparency, one earlier fresh process reached `thread/start` after its config gate, then was stopped by a preliminary harness rule on the expected synthetic-model metadata fallback warning before any loopback model request. It captured no tool inventory and is not counted among the two complete repetitions. The initial local failure file used the `NO_TOOL_BOUNDARY_FAILED` marker even though no model request existed; that marker is not evidence that a tool was present. A separate fresh root/process then completed the second repetition.

The metadata fallback warning was recorded in both completed repetitions. It did not change the effective local provider, and each host request went only to the local mock. This proof makes no claim about model metadata quality or performance.

## Egress, claim ceiling and lifecycle

The process-scoped macOS sandbox allowed only the exact loopback listener; the HTTP proxy never forwards non-loopback targets. Observed non-loopback proxy attempts: `0`. External provider/model requests transmitted: `0`. Raw host request and protocol bytes remain in local temporary roots; the repository package contains only hashes and safe semantic assertions, not system/developer prompt contents. No TCP/TLS capture claim is made.

This establishes a repository-local Codex 0.159.2 request-serialization result against a deterministic local mock only. It is not provider acceptance, live canary evidence, an R4 result, evaluator result, Owner/GPT review, or permission to execute. The Formal PR stays Draft and unmerged; no Ready action is authorized or taken.

Counts: local mock requests `2`; external provider/model requests `0`; live canary `0`; R4 units `0`; evaluator runs `0`; Task230 `false`; Ready/merge `0`.
