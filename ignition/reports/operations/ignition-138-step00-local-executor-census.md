# IGNITION-138 — Step 00 Amendment-01 Local Executor Census

This is a read-only, observation-time census performed before any new Task138
live inference. The control material was refreshed from
`origin/relay/current@4ab09c3d6595f254577739ec1d87e64144c61803`; the formal
candidate observed by the census is
`99389c846b6766ca8b373812ece4191660b6474f`.

## Observed candidates

| Candidate | Kind | Observation | Admission result |
| --- | --- | --- | --- |
| Gemini CLI 0.53.1 | `AGENTIC_EXECUTOR` | `-p`, JSON/stream-JSON, plan mode and sandbox flags are public; `~/.gemini/oauth_creds.json` was observed by presence/mode only | Blocked: no public separate auth-source/ephemeral-home boundary; billing/auth not re-attested |
| Codex CLI 0.144.4 | `AGENTIC_EXECUTOR` | JSONL, output schema, `--ephemeral`, `--sandbox read-only`, and public `codex login status`; R3 runtime scratch exists | Blocked at census: current adapter still binds `CODEX_HOME` to scratch rather than a read-only auth reference |
| Hermes Agent 0.20.0 | `AGENTIC_EXECUTOR` | bounded `-z` and `--safe-mode`, but text-only final result and open prior reconciliation | Blocked |
| OpenClaw 2026.7.1-2 | `AGENTIC_EXECUTOR` | agent help/JSON surface observed, but workspace/channel/read-only boundary is not publicly proven | Blocked |
| GitHub Copilot CLI | `AGENTIC_EXECUTOR` candidate | `gh copilot --help` says absent CLI would download; no local Copilot binary/cache was present | Not installed; no download or billing probe performed |
| plain `gh` 2.96.0, git, jq | `TOOL_ONLY` | command/tool surfaces only | Never eligible as Agent |
| Ollama, LM Studio, MLX DSpark, bundled llama-server | `REASONER_RUNTIME` | local model/runtime surfaces; Ollama 3 models and LM Studio 4 models observed; servers were not running | Not an external Agent completion path |
| Claude Desktop, QwenWorkCN | `UI_OR_NONAUTOMATABLE` | application bundles only; no stable public machine-facing Agent CLI observed | Excluded |

The known-name list was used only as a search prompt. PATH, `~/.local/bin`,
Homebrew, npm global, pipx/uv, Cargo and selected application bundles were
checked. No Aider, Goose, Qwen Code, Cursor/agent CLI or other named Agent CLI
was found in the checked machine-facing surfaces.

## Dynamic selection

The census deliberately produces `NO_SAFE_CANDIDATE` rather than silently
selecting by brand. Codex ranks first for the next re-attestation because it
has the clearest public structured/read-only/ephemeral surface and an existing
authenticated public status, but it cannot be live-admitted until the auth
source is explicitly separated from runtime scratch and behaviorally shown
unchanged. Gemini is the next real Agent candidate, but the current CLI's
public surface does not provide a separate auth file or ephemeral home; using
`~/.gemini` directly would violate the task's read-only auth/config boundary.

`gh copilot` was not installed: its help path advertises a download, which
would mutate local state and introduce an un-re-attested auth/billing boundary.
No internet install was necessary because installed candidates were found, and
no install, login, re-authentication, config, provider, channel, browser, or
billing operation was performed.

The exact machine receipt is
`ignition/data/operations/iterations/138/local-executor-census-r1.json`; its
validator recomputes the ranking and rejects any attempt to classify plain
`gh`, a local model runtime, or a UI bundle as an external Agent.

Claim ceiling: repository-local census and admission evidence only. No live
inference, validated completion, model ranking, production readiness, external
truth, Owner acceptance, or epistemic acceptance is inferred.
