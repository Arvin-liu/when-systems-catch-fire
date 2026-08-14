# Task 98 dependency impact

The generated graph contains 1,923 declared `consumer -> dependency` edges across 541 assets with dependencies. This report binds the first correction set to both its outgoing declarations and all direct reverse consumers.

| Corrected asset | Declared dependencies | Direct consumers | Required action |
|---|---|---|---|
| T2 | — | D517 | Restrict consumer to typed algebra; structural comparison remains unvalidated |
| D127 | D91, D180 | D123 | Block computed-path inference; queue D123 |
| D182 | D181, D270, D211, D220 | D185 | D185 downgraded in this task |
| D183 | D181, D270, D211, D220 | D516, T26 | Block gate-count monotonicity and physical-unification claims |
| D184 | D181, D270, D211, D220 | — | No direct reverse consumer |
| D185 | D181, D270, D211, D220, D182, D254 | — | Corrected in this task |
| D186 | D181, D270, D211, D220 | — | Corrected in this task |
| D187 | D181, D270, D211, D220 | — | Corrected in this task |
| D188 | D181, D270, D211, D220 | — | Corrected in this task |
| D189 | D181, D270, D211, D220, D169 | — | Corrected in this task |
| D190 | D181, D270, D211, D220 | — | Corrected in this task |
| D260 | D181, D270, D211, D220 | — | Corrected in this task |

The outgoing dependencies are not automatically invalidated: a correction to a consumer does not downgrade its inputs. Reverse consumers are authoritative in `dependency-actions.jsonl`. Open actions remain blocked/queued and cannot inherit the old strong conclusion.
