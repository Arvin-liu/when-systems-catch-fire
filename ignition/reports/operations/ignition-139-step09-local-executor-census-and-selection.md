# IGNITION-20260825-139 Step 09 — Fresh local executor census and why-executor

## Result

`PASS`: the current host was re-attested at `2026-08-25T05:37:35Z` using only
public version/help surfaces, binary/help digests, application-bundle presence
and auth-status presence/exit behavior. No model, Agent inference, UI action,
login, secret read, installation, configuration or billing operation occurred.

The scan found 14 candidates: five Agentic Executor records (four installed),
four local Reasoner Runtime records, three Tool-only records and two UI-only
records. Gemini CLI `0.53.1`, Codex `0.144.4`, Hermes and OpenClaw are the four
installed Agentic candidates. Plain `gh` `2.96.0` remains `TOOL_ONLY`; Ollama,
LM Studio, MLX DSpark and bundled `llama-server` remain `REASONER_RUNTIME`;
Claude Desktop and QwenWorkCN remain UI-only. Aider, Goose, Qwen Code and
Cursor/agent CLI were not found in the declared scan scope.

## Dynamic selection

Codex is the only currently admitted Agentic Executor. Its public
`codex login status` returned exit 0 without exposing output, and the census
records the auth file as presence-only. The R3 adapter now keeps the auth
reference separate from the attempt runtime scratch, while the ten census
checks cover disposable workspace, read-only ceiling, one-shot operation,
structured output, public auth status, no-new-billing, cleanup, channel/browser
denial, independent validation and auth-source separation.

Gemini remains blocked by auth/home and billing re-attestation; Hermes by strict
structured-result and auth/no-billing boundaries; OpenClaw by workspace,
channel and process-cleanup boundaries; and Copilot CLI by not being installed.
This `why_executor` result is an admission trace only, not a model-quality
ranking or a completion result.

Machine evidence: [`local-executor-census-r1.json`](../../data/operations/iterations/139/local-executor-census-r1.json) and [`step09-local-executor-census-and-selection.json`](../../data/operations/iterations/139/step09-local-executor-census-and-selection.json).

## Next gate

Step10 must independently freeze the capability lease, synthetic read-only
workspace, auth/runtime-scratch separation, durable capture support, no-channel
boundary, child-depth guard and validator contract. Only then may Step11 make
the single authorized live invocation.

Claim ceiling: fresh repository-local observation-time census, executor-kind
classification, admission checks and why-executor trace only; no inference,
validated completion, model-quality ranking, production readiness, external
truth, Owner acceptance or epistemic acceptance is inferred.
