# External Capability Provider Adapter Spikes R0

Task: `IGNITION-20260831-149`

This is an implemented and validated provider spike. It is not a capability activation, permission grant, Current integration or production-readiness decision.

## Decision summary

| Scope | Recommendation | Future role | Current integration | Production readiness |
| --- | --- | --- | --- | --- |
| Archify | `CONTINUE_EXPERIMENT` | `DERIVED_VISUALIZATION_PROVIDER` | `NOT_CURRENT_INTEGRATION` | `NOT_PRODUCTION_READY` |
| Agent Reach public read | `CONTINUE_EXPERIMENT` | `READ_ONLY_SOURCE_ACQUISITION_PROVIDER` | `NOT_CURRENT_INTEGRATION` | `NOT_PRODUCTION_READY` |
| Agent Reach authenticated/session-bearing | `DEFER` | No role until explicit channel admission | `NOT_CURRENT_INTEGRATION` | `NOT_PRODUCTION_READY` |

The overall spike status is `PROVIDER_ADMISSION_CANDIDATE`. The allowed recommendation vocabulary is preserved: `ADMIT_AS_CURRENT_BOUNDED_CANDIDATE`, `CONTINUE_EXPERIMENT`, `DEFER`, `REJECT`. No row is promoted to Current.

## Archify

Archify was evaluated as a `DERIVED_VISUALIZATION_PROVIDER`. The adapter consumed Ignition canonical architecture/system-map inputs, produced typed IR, retained source and revision provenance, and never treated the derived artifact as architecture truth.

- Pinned upstream: `tt-a1i/archify`, revision `2bfb47132c057195d8dddb3e25ae966dd7c7a72e`, declared version `2.16.0`.
- Validation: `validate` PASS 9/9 with zero errors/warnings; `deliver` PASS with 19 formal source references; visual-check PASS for the base artifact.
- Artifact: HTML bytes `753375`, SHA-256 `978008823b3941622a8ba21e751913f37d8c87310e28b46c5bca6f17db913017`; artifact remains `NOT_COMMITTED` to avoid vendoring the external viewer bundle.
- Architecture Delta: authored components, connections and boundaries all had zero changes; provenance changed only because before/after lineage revisions differed. The Delta is not an impact, risk, safety, correctness or merge-readiness authority.
- Known limits: the Delta viewer visual-check retained six `viewer/viewport-overflow` diagnostics across the recorded viewports; upstream `visualReview` remains pending; external viewer output is a derived surface only.
- Dependency/license: Node.js runtime and the external viewer bundle are required; MIT attribution is required; no source copy or vendoring was performed.

Archify must not be used as canonical architecture truth, runtime impact authority, correctness authority, merge-readiness authority, external-truth authority or Current capability. Recommendation: `CONTINUE_EXPERIMENT`.

## Agent Reach

Agent Reach was evaluated as a `READ_ONLY_SOURCE_ACQUISITION_PROVIDER`, with provider selection and provenance remaining Ignition-owned.

- Pinned upstream: `Panniantong/Agent-Reach`, revision `06c202b03400a7d31886bf4399213706da1a0324`, declared/installed version `1.5.0`, MIT attribution required, no source copy.
- Pinned-source health: `BLOCKED_DEPENDENCY` on missing PyYAML. The installed executable's isolated doctor observation is separate from the pinned-source import result.
- Channel matrix: 15 doctor channels and 17 operation-level capability records. `ok`/`warn`/`off`, active backend, environment availability, authentication requirement and testability remain separate fields.
- Public smoke: Jina web, RSS/feedparser, Bilibili public search API and V2EX public API returned bounded read results; YouTube returned metadata only (`PASS_WITH_LIMITS`); GitHub gh routes returned `AUTH_REQUIRED`; Exa semantic search returned `ENVIRONMENT_MISSING`.
- Native coexistence: native curl/public HTTP and Agent Reach routing were compared for GitHub read/search and generic web read. Web normalization worked with different representations; GitHub route authentication failure was retained. Provider switching was `PARTIAL` with no upper-workflow change.
- Safety: zero-auth only; no login, Cookie/session read, system install/configuration or external write. Authenticated/session-bearing channel admission remains `NO_AUTHENTICATED_CHANNEL_ADMISSION`.

Agent Reach must not be treated as global Internet authority, external-truth authority, credentials, permission or a replacement for Ignition-owned provider selection. Recommendation for public read: `CONTINUE_EXPERIMENT`. Recommendation for authenticated/session-bearing channels: `DEFER`.

## Claim ceiling

`EXTERNAL_PROVIDER != IGNITION_AUTHORITY`

`PROVIDER_CAPABILITY != PERMISSION`

`PROVIDER_OUTPUT != EXTERNAL_TRUTH`

`PROVIDER_LOCAL_POLICY != IGNITION_GLOBAL_POLICY`

`ADAPTER_SPIKE_PASS != CURRENT_CAPABILITY`

The evidence is repository-local, provider-bound and validated only within the recorded environment. It does not establish external truth, Owner acceptance, production readiness, authenticated credentials, permission, Current capability or live external completion.

## Next action

`AWAIT_OWNER_PROVIDER_ADAPTER_REVIEW`
