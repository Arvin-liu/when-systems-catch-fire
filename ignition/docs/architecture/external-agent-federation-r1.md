# External Agent Federation R1 — ownership boundary

点火是 OS，不是另一个 OpenClaw、Hermes 或 Codex。它维护目标、价值、
任务契约、权限、长期状态、Pack、记忆、验证、handoff、provenance 和结果
吸收；外部智能体是可替换执行器。适配器只翻译可观察边界，不复制外部
Agent 的运行时。

## 一句话

> 点火负责“为什么做、做到哪里、由谁做、怎样证明、怎样记住”；外部智能体负责“具体怎么动手”。

## Machine contract

- [OS / Executor ownership](../../data/agent-federation/os-executor-ownership-r1.json)
- [Build versus integrate policy](../../data/agent-federation/build-vs-integrate-policy-r1.json)
- [Executor component ownership](../../data/agent-federation/executor-component-ownership-r1.json)
- [Step 00 inventory](../../data/agent-federation/executor-inventory-r1.json)

The ownership labels are `OS_OWNED`, `EXTERNAL_AGENT_OWNED`,
`ADAPTER_BOUNDARY`, `REFERENCE_ONLY` and `DEFERRED`. These are engineering
ownership labels, not truth or authority upgrades.

## Reference Executor freeze

The existing `agent_runtime` local action plane remains available as
`REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL`. It may verify
the protocol, support deterministic conformance fixtures, provide a minimal
offline fallback and receive safe fault injection. It does not gain a browser,
network, messaging, provider/model, daemon, general subagent or remote Git
runtime in this task.

## Build versus integrate

The default decision is to integrate a public machine-facing interface from an
existing executor. A new executor shell is proposed only after a concrete,
reproducible failure crosses a declared permission, checkpoint, provenance,
provider-neutrality, validation, fail-closed, privacy, performance,
maintenance or architectural threshold. “We can write it ourselves” and “we
do not want to write an adapter” are not exceptions.

The validator is intentionally fail closed for new paths that look like
browser/gateway/channel/model-provider/subagent/daemon/remote-Git layers unless
the policy contains a complete `build_vs_integrate_exception` record.

## Boundary ceiling

This page describes repository engineering ownership. It does not establish
production autonomy, universal safety, external validity, Owner acceptance,
claim maturity or `EPISTEMICALLY_ACCEPTED`; the current state remains
`CURRENT_WITH_OPEN_OBLIGATIONS`.
