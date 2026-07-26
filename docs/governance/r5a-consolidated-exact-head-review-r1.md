# R5-A consolidated exact-head review R1

## Decision

`R5A_CONSOLIDATED_EXACT_HEAD_REJECTED_NARROW_REPAIR_REQUIRED`

The independently reviewed target was PR #130 at exact head
`f33be64b26ef14d14098f42ec947bd93fddd245c`, based on
`f236543dadcaf79ba9dba750fa21bd8b5c65a33a`. The base/head topology, five
source commits, two narrow-repair commits, PR #131 ordinary merge
`062f223f...`, status commit `f33be64b...`, generated artifacts, synchronized
surfaces, exact-head GitHub Actions logs and repository validation ladder were
all inspected directly.

The reviewed head remains `OPEN / DRAFT`, was not moved to Ready, and was not
merged into its predecessor. It is not Main, Current, activated or accepted.

## Green evidence that did not establish acceptance

- focused R5-A suite: `177 passed`;
- exact 30-case narrow-repair gate: `PASS`;
- inherited ARR suite: `595 passed, 2 skipped` in PR-equivalent branch context;
- Foundation, Lean, synchronization, typed propagation, system-map generation,
  human front door and ARR static gate: `PASS`;
- exact-head R5-A PR run `30185503853`, R5-A push run `30185502688`, and
  Foundation PR run `30185503856`: `SUCCESS` after log inspection;
- deterministic generation: byte-clean;
- missing-case, duplicate-case, changed-expectation and deleted-required-ID
  mutation probes: correctly `BLOCKED`.

Those checks do not cover every public construction and schema-validation path.
They therefore cannot override the concrete blockers below.

## Required failed instances

Every instance below used synthetic, non-private input. Each expected fail-closed
rejection but completed without exception or JSON Schema validation error.

| Stable ID | Contract surface | Concrete bypass |
|---|---|---|
| `R5A-CR-001` | tradition translation | direct `TranslatedClaim` construction accepted `PHENOMENOLOGICAL_REPORT -> EMPIRICALLY_SUPPORTED_MECHANISM` |
| `R5A-CR-002` | tradition translation | blank provenance/language/status/attribution and confidence `2.5` were accepted |
| `R5A-CR-003` | embodied view | an agent with provenance boundary A accepted a view carrying boundary/provenance B |
| `R5A-CR-004` | embodied relation | whitespace-only `relation_type` was accepted as a typed relation |
| `R5A-CR-005` | safety envelope | stop-treatment language in a structured field passed because only `raw_text` was scanned |
| `R5A-CR-006` | safety envelope | integer consent and mapping-valued `unknowns` passed runtime validation |
| `R5A-CR-007` | longitudinal revision | equal observation/decision times passed despite the declared distinct-time contract |
| `R5A-CR-008` | concept lifecycle | construction accepted an out-of-set `current_state` |
| `R5A-CR-009` | life-integrity public schema | standard Draft 2020-12 validation accepted all `UNKNOWN` disclosures and no evidence object because `not_unknowns` is not an enforcing keyword |
| `R5A-CR-010` | translated-claim public schema | a two-field object passed although the contract requires all provenance/translation/attribution/reference/evidence/scope/rights/confidence/UNKNOWN/revision fields |
| `R5A-CR-011` | longitudinal public schema | integers for every required field passed because the artifact declares no `properties` constraints |

## Single narrow repair request

Only one next task is requested:

`IGNITION-R5A-CONSOLIDATED-CONTRACT-BYPASS-NARROW-REPAIR-R1-20260726`

It must bind `R5A-CR-001`–`R5A-CR-011` as an exact required-ID set with one
typed evidence object and one executed result per instance. The repair must make
the runtime constructors/validators and the generated standard JSON Schemas
reject the same invalid fixtures, add schema metaschema and instance tests,
regenerate public artifacts deterministically, and rerun the complete inherited
ladder. Unknown JSON Schema keywords, prose-only `fail_closed_rules`, counts or
green legacy CI cannot substitute for rejection of an instance.

The repair is limited to R5-A contract closure. It may not start R5-B, R5-C,
R6, activation, a domain pack, federation, human intervention, medical claims,
L7, a second executor, PROMOTE or EVOLVE. It may not merge PR #130, change Main,
or rewrite published history. Independent acceptance of the repair and a fresh
exact-head review of the consolidated candidate remain separate later gates.

## Synchronization decisions

| Surface | Decision | Reason |
|---|---|---|
| R5-A runtime/schema/test implementation | `NO_CHANGE_WITH_REASON` | this PR issues the bounded repair request; implementation requires its own reviewable repair head |
| README / project current state / iteration application record | `CHANGE` | expose the exact-head rejection and prevent premature progression |
| AI start, handoff and machine front doors | `CHANGE` | prohibit treating PR #130 as accepted or starting R5-B/C/R6 |
| changelog and governance/future boundary | `CHANGE` | preserve the review decision and exact repair scope |
| system map / component registry / Pages production | `NO_CHANGE_WITH_REASON` | rejected Draft is not a Current component and is not deployed |
| Foundation / ARR runtime / Function OS / licenses | `NO_CHANGE_WITH_REASON` | no implementation, authority or license change in this request-only PR |

Maximum claim ceiling: `repository_contract_bypass_reproduced`. The review does
not establish human harm, human safety, efficacy, universal semantics, cultural
validity, causality or real-world behavior.
