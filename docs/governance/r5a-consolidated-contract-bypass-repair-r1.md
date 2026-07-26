# R5-A consolidated contract-bypass narrow repair R1

## Lifecycle

`R5A_CONSOLIDATED_CONTRACT_BYPASS_REPAIR_ACCEPTED_MERGED_TO_PR130_SOURCE_CANDIDATE_NOT_MAIN_NOT_CURRENT`

- task: `IGNITION-R5A-CONSOLIDATED-CONTRACT-BYPASS-NARROW-REPAIR-R1-20260726`;
- exact starting head: `f33be64b26ef14d14098f42ec947bd93fddd245c`;
- base branch: `architecture/ignition-r5a-life-integrity-charter-candidate-r1`;
- independently accepted exact head:
  `c4576972047a47045e95b1c794570597f58e6c9a`;
- PR #133: Draft to Ready to ordinary merge;
- merge commit into PR #130 source branch:
  `ff158ba0351d68918a135ec3446f4f68ddf9387b`;
- accepted-head tree equals merge tree;
- PR #130 remains Draft, unmerged into its predecessor, non-Main, non-Current
  and unactivated.

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

At the final local checkpoint, the focused R5-A suites report `193 passed`, the
exact eleven-case gate reports PASS, all six schema matrices pass, all five gate
mutations block, and deterministic artifacts regenerate byte-identically. The
inherited ARR suite reports `611 passed, 2 skipped`; Lean, Foundation,
iteration synchronization, typed propagation, Phase D/E, the registry-derived
system map, human front door and second-executor static gate pass. The inherited
Foundation/synchronization/front-door/propagation/Pages/Phase-E/production-
authority unittest ladder reports `176` run, `1` skipped, PASS. Exact-final-head
GitHub CI remains mandatory publication evidence and is recorded externally
after the final commit exists.

Independent acceptance separately replayed the rejected predecessor and exact
repair head instance by instance, reviewed both commits and all changed files,
reran the complete local ladder, and inspected the exact-head and merge-head raw
Actions logs. Maximum claim ceiling:
`repository_contract_repair_independently_accepted_and_merged_to_candidate_source`.

Neither a test count, green CI nor deterministic generation substituted for
that review. Acceptance applies only to the exact repair; it does not accept the
complete PR #130 candidate or establish Main, Current, activation, human safety,
clinical efficacy or universal semantic coverage.

## Synchronization decisions

| Surface | Decision | Reason |
|---|---|---|
| R5-A runtime, schemas, tests, generator, machine gate and CI | `CHANGE` | exact eleven-instance closure |
| README, current state, iteration application record | `CHANGE` | expose accepted repair merge without candidate overclaim |
| AI/Agent start/handoff, `llms.txt`, summary and changelog | `CHANGE` | preserve accepted-repair versus Draft-candidate boundary |
| philosophy/governance indexes | `CHANGE` | add the separately requested “永远进行时” principle |
| system map and component registry | `NO_CHANGE_WITH_REASON` | repair acceptance is not a new Current component |
| Pages production | `NO_CHANGE_WITH_REASON` | candidate-branch merge is not a Main/Current deployment |
| Foundation, ARR runtime, Function OS and licenses | `NO_CHANGE_WITH_REASON` | no authority, runtime-stage or license change |

No R5-B, R5-C, R6, source corpus, human intervention, medical claim, domain
pack, federation, L7, second executor, PROMOTE, EVOLVE, Main, activation,
rebase, squash, amend, force push or history rewrite is included. The only
Ready/merge actions were the independently authorized PR #133 transition and
ordinary merge recorded above.

## Unique next-task request

迭代点火操作法，建立“阶段成果进入 Main、但不自动成为 Accepted/Current”的持续
快照与分层发布制度，使 GitHub 项目主页能够及时显示 Agents 已完成的阶段成果。

This request is recorded only. It is not started by this repair acceptance and
does not authorize a Main change in this task.
