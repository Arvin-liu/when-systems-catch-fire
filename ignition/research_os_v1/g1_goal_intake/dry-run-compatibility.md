# Dry-run compatibility table

| Steering type | Input or method used by this adapter | Dry-run outcome | Prohibited effect |
| --- | --- | --- | --- |
| `IntentRecord` | `from_dict` over a closed synthetic snapshot | Proposal scope and version are compared with the request. | No `IntentRegistry` lookup, registration, or owner authorization. |
| `GoalRecord` | `from_dict`; existing `objective_digest()` | Stable goal/version/digest and parent relationship are compared. | No `GoalRegistry` mutation or lifecycle transition. |
| `CompletionContract` | Construct from supplied exact contract snapshot | Request success predicates must equal contract acceptance predicates; forbidden shortcut predicates fail closed. | No completion evaluator and no `SATISFIED` outcome. |
| `GoalEpisodeBinder` | Fresh local binder for one projection | Binding identity and handoff digests are reported for a structurally valid proposal. | No persisted or canonical episode binding. |
| `GoalDriftGuard` | `inspect` using supplied proposal bytes only | Existing drift reasons are shown for digest/predicate differences. | No claim of live canonical currentness or memory-conflict check. |

`RUN_PASS` and test success are not Goal-completion predicates. All result statuses are preflight observations, and structurally valid proposals still require Owner authority.
