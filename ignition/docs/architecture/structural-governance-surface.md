# Structural Governance Surface

这是一张由 canonical transition grammar 投影出的关系表，不是提示词、命令、
权限清单或真值层。它把“当前状态 → 可以说到哪里 → 缺什么才能更强”并排呈现，
让人和模型都能看到边界，但不能凭阅读它获得任何 hard authority。

## 先读这里

如果证据只支持一个局部工程结论，表面不会把它自动变成外部真值；如果证据
缺口没有补上，未知可以保持未知；如果状态已撤回或隔离，改标题也不会让它
回弹。下面每行是一个可回链关系，不是对读者或模型的行为授权。

## Relations

| 关系 | 当前前件 | 允许的局部转移 | 被阻断的越级 | 更强转移所需 |
| --- | --- | --- | --- | --- |
| `CONSENSUS_NOT_AUTHORITY` | One or more models, Agents, reviewers or executors produce matching judgments or receipts. | The record may note agreement as bounded observation or review evidence. | Do not convert agreement into Owner authority, truth or permission. | Bind each judgment to its role, source, scope and independent validation path. |
| `ENGINEERING_COMPLETION_NOT_EXTERNAL_TRUTH` | A repository implementation, validator, CI run or bounded pilot reaches its declared local completion state. | The local record may transition to a repository-scoped engineering completion state. | Do not infer external truth, production safety or universal validity. | Use the declared repository validator and retain its scope and residuals. |
| `EVIDENCE_LEVEL_CEILING` | A source, fixture, review or observation supports a conclusion at a bounded evidence level. | The conclusion may be stated only up to the licensed level and scope. | Do not widen scope, quantifier, causal force or generality without a new gate. | Use the claim ceiling, provenance and relevant adjudication or replication requirement. |
| `LOCAL_FIXTURE_NOT_GENERALIZATION` | A disposable fixture or offline pilot produces a reproducible observation. | The fixture may support a repository-scoped compatibility or coordination statement. | Do not generalize the result to production, all models, all providers or the external world. | Name the fixture, environment, provider status and untested dimensions. |
| `MISSING_PROVENANCE_DEGRADES` | A proposed claim, observation or publication lacks recoverable source, rights or provenance binding. | The item may remain private, pending, non-republished or bounded as an observation. | Do not treat a summary, path, hash or confidence score as a substitute for missing source bytes. | Recover the required source and rights binding or preserve the restrictive disposition. |
| `M_E_ORTHOGONAL` | A mathematical maturity, formalization or engineering-quality observation changes on one axis. | Only the named axis and its evidence-bound record may change. | Do not infer an automatic M-to-E or E-to-M upgrade. | Use the independent axis gate and preserve the other axis as recorded. |
| `OWNER_ONLY_AUTHORITY` | An Agent, model, receipt or local workflow proposes an Owner-level acceptance or permission decision. | The proposal may be recorded for Owner review without changing Owner state. | Do not self-assign Owner acceptance, Owner authority or an Owner gate result. | Require the explicit Owner-controlled gate and its auditable record. |
| `PERMISSION_INTERSECTION_ONLY_NARROWS` | Task, profile, pack, executor and approval scopes are composed for a proposed action. | The effective capability is the validated intersection of declared scopes. | Do not widen permission because a model is cautious, a surface was read or an ESI score is high. | Use the canonical policy/permission intersection and explicit approval contract. |
| `PUBLICATION_COMPLETION_NOT_TRUTH` | A report, Results Book entry or public-safe explanation has passed its publication and privacy gates. | The material may become a bounded public projection with its claim ceiling preserved. | Do not infer that publication proves the represented proposition. | Preserve source, provenance, privacy, disposition and claim ceiling. |
| `RUNTIME_NOT_EPISTEMIC_ACCEPTANCE` | A local runtime, executor adapter, pilot, receipt or recovery path reaches a terminal success state. | The local operational record may transition to its declared bounded completion status. | Do not set EPISTEMICALLY_ACCEPTED or claim external success from the runtime state. | Preserve the explicit runtime claim ceiling and separate epistemic/Owner gates. |
| `UNKNOWN_MUST_REMAIN_UNKNOWN` | The evidence packet, provenance or gate does not license a stronger conclusion. | The record may retain UNKNOWN, conditional or pending status. | Do not fill an evidence gap with a plausible story, consensus or formatting cue. | Name the missing evidence or authority required for a future transition. |
| `WITHDRAWN_NO_REBOUND` | A claim or result is withdrawn, quarantined, downgraded or marked historical. | It remains in append-only lineage with the restrictive disposition. | Do not revive it by changing its title, identifier, wording or projection surface. | Require a governed successor with new provenance and independently reviewed evidence. |

## Hard versus soft

Hard governance（permission、validator、state machine、K13、Claim Ceiling、Owner gate）
决定能不能做、能不能晋级。这个表面属于 soft structural governance：它至多
影响模型默认怎样判断和表达。`esi_score`、`soft_context_exposure`、风格相似度
或阅读记录都不能授权、改真值、升级 M/E、扩大 claim ceiling、代替 Owner 或
放行安全副作用。

## Projection boundary

Generated from `ignition/data/epistemic-governance/transition-grammar-r0.json`, `ignition/data/epistemic-governance/soft-governance-non-authority-invariant-r0.json` and `ignition/data/architecture/current-system-identity.json`.
Current State 的工程状态仍为 `CURRENT_WITH_OPEN_OBLIGATIONS`，
`EPISTEMICALLY_ACCEPTED=0`。本页不证明 ESI 已成立，也不包含私人观察原文。
