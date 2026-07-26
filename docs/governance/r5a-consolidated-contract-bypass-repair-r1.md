# R5-A consolidated contract-bypass narrow repair R1

## Lifecycle

`R5A_CONSOLIDATED_CONTRACT_BYPASS_NARROW_REPAIR_DRAFT_AWAITING_REVIEW`

- task: `IGNITION-R5A-CONSOLIDATED-CONTRACT-BYPASS-NARROW-REPAIR-R1-20260726`;
- exact starting head: `f33be64b26ef14d14098f42ec947bd93fddd245c`;
- base branch: `architecture/ignition-r5a-life-integrity-charter-candidate-r1`;
- implementation is a bounded Draft candidate only;
- no independent acceptance, Ready transition, merge, Main or Current claim.

## Gap and repair

The consolidated exact-head review reproduced eleven public fail-open paths.
This repair moves validation into every affected public constructor/validator,
declares Draft 2020-12 for all six generated schemas, replaces non-enforcing
schema prose/keywords with standard constraints, and binds runtime and schema
representations of the same fixture where both surfaces exist.

| ID | Repaired surface | Required machine rejection |
|---|---|---|
| `R5A-CR-001` | direct translated-claim construction and schema | forbidden phenomenology-to-supported-mechanism upgrade |
| `R5A-CR-002` | translated-claim required fields, confidence and schema | blank/mistyped incomplete claim |
| `R5A-CR-003` | agent/view provenance boundary | boundary A/B mismatch |
| `R5A-CR-004` | cross-view relation runtime/schema | whitespace-only relation type |
| `R5A-CR-005` | safety structured text runtime/schema | treatment-stop language outside `raw_text` |
| `R5A-CR-006` | safety runtime/schema types | integer consent and mapping-valued UNKNOWNs |
| `R5A-CR-007` | longitudinal runtime | non-distinct ordered times |
| `R5A-CR-008` | concept construction/schema | out-of-set caller-supplied current state |
| `R5A-CR-009` | life-integrity assessment schema | UNKNOWN disclosures without typed evidence |
| `R5A-CR-010` | translated-claim schema | two-field incomplete object |
| `R5A-CR-011` | longitudinal schema | integers for every required field |

Every ID has one concrete synthetic non-private fixture, one typed
`EvidenceObject`, one expected rejection and executed per-surface results. The
machine gate requires exact ordered ID equality, unique case/evidence identity,
and PASS for every surface. It blocks a missing case, duplicate case, changed
expectation, bypass-restoring fixture or deleted required identity.

## Schema acceptance

The six public schemas each:

- declare `https://json-schema.org/draft/2020-12/schema`;
- pass `Draft202012Validator.check_schema`;
- accept one complete valid instance;
- reject one concrete invalid instance;
- contain no `not_unknowns` pseudo-keyword;
- remain candidate repository interfaces, not human-safety or scientific proof.

Deterministic generation now emits fourteen artifacts: the candidate manifest,
three registries, six standard schemas, the retained 30-case gate registry and
receipt, and the new 11-case consolidated registry and receipt.

## Validation and claim boundary

At the implementation checkpoint, the focused R5-A suites report `193 passed`,
the exact eleven-case gate reports PASS, all six schema matrices pass, all five
gate mutations block, and deterministic artifacts regenerate byte-identically.
The full inherited ladder and exact-head GitHub CI remain mandatory publication
evidence and are recorded externally after the final commit exists.

Maximum claim ceiling:
`repository_contract_repair_implemented_awaiting_independent_review`.

Neither a test count, green CI nor deterministic generation accepts this repair.
A separate independent exact-head repair review is still required before the
complete PR #130 candidate can be reviewed again.

## Synchronization decisions

| Surface | Decision | Reason |
|---|---|---|
| R5-A runtime, schemas, tests, generator, machine gate and CI | `CHANGE` | exact eleven-instance closure |
| README, current state, iteration application record | `CHANGE` | expose Draft repair without acceptance overclaim |
| AI start/handoff, `llms.txt`, summary and changelog | `CHANGE` | preserve the only allowed lifecycle and hard stop |
| philosophy/governance indexes | `CHANGE` | add the separately requested “永远进行时” principle |
| system map and component registry | `NO_CHANGE_WITH_REASON` | a Draft repair is not a new Current component |
| Pages production | `NO_CHANGE_WITH_REASON` | unmerged Draft must not deploy to production |
| Foundation, ARR runtime, Function OS and licenses | `NO_CHANGE_WITH_REASON` | no authority, runtime-stage or license change |

No R5-B, R5-C, R6, source corpus, human intervention, medical claim, domain
pack, federation, L7, second executor, PROMOTE, EVOLVE, Ready, merge, Main,
activation, rebase, squash, amend, force push or history rewrite is included.
