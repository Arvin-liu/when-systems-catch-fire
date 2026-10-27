# IGNITION-20260905-155 任务报告：cross-contract review map 历史盲测

Status: `RESEARCH_COMPLETE / PARTIAL_INCREMENT / DRAFT_PR_PENDING_REVIEW / NON_CURRENT`

## 1. 绑定、基线与边界

- Command source: `Arvin-liu/1111:agent-commands/IGNITION-20260905-155.md`
- Command commit: `b75ad68925178ef4cc7ab97c53fa63cfe9965902`
- Command blob SHA: `ceca66aa7734ba338923461345d52442e5bdaf1e`
- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Exact Task154 head used as baseline: `56e57906ef6e54c3721499430aaec8da1182c322`
- Task155 branch: `work/IGNITION-20260905-155`
- Base branch: `work/IGNITION-20260904-154`
- Blind freeze commit: `6618f0b8d5dee9a63e2970c470da95eefc59f4f4`
- Historical corpus cutoff: `2026-09-04T00:00:00+08:00`; no Task153 or Task154 artifact is a case.
- `1111/instructions/CURRENT.md` and `1111/relay/current` were observed as stale control pointers and preserved unchanged per Owner confirmation. The residual is recorded in the research freeze ledger.

This is `research/data/docs only`. No canonical layer, failure class, runtime state, authority, capability, schema, registry, validator or mandatory gate was added. No live executor, provider, authenticated action, secret, configuration or successor task was used. Task153, Task154 and Task155 remain outside Ready, merge, Current, Owner acceptance and epistemic acceptance.

## 2. Method executed

The task first froze a purposeful maximum-variation corpus of 27 real repository events spanning lifecycle, evidence, control-plane, runtime, publication and provider-boundary families. The deterministic partition is `SHA256(case_id).first_byte mod 3`: 20 discovery and 7 holdout. An exclusion ledger contains zero post-freeze removals; Task153/154 are excluded by the cutoff rule.

The criteria file then froze three junction questions—claim, authority and consequence—and minimum observable criteria for the five proposed diagnostics. It also froze the redundancy, incremental, false-positive and undecidable rules. The blind packets contain only material available at each pre-outcome cutoff. Blind outputs record two separate passes: existing contracts only, then the cross-contract review map. They were committed and pushed before outcome sources were read for scoring.

The repository-history authoring context means this is temporal/data-level blinding rather than independent cognitive double-blind review. Purposeful sampling is descriptive and cannot estimate a population error rate.

## 3. Empirical result

The 27 cases classify as:

| Classification | Count |
| --- | ---: |
| `INCREMENTAL_TRUE_POSITIVE` | 2 |
| `REDUNDANT_TRUE_POSITIVE` | 9 |
| `FALSE_POSITIVE` | 2 |
| `TRUE_NEGATIVE_CONTROL_PASS` | 10 |
| `MISS_FALSE_NEGATIVE` | 1 |
| `UNDECIDABLE` | 3 |

The two incremental cases are both holdout cases and come from independent families:

1. CC-012 (Task136 Hermes timeout) — the local technical receipt and reconciliation state did not expose a concrete accountable observer/stop binding; later read-only reconciliation confirmed missing PID/PGID, workspace, session, raw-output and matching-artifact evidence and kept the obligation open.
2. CC-026 (Task150 Base/Delta admission scope) — the Draft closeout preserved lifecycle/provider non-intents but did not separate the Base operation and Delta extension as admission objects; later Owner reopening removed the combined gate and prevented Delta-to-Base promotion.

Nine flags are redundant with existing local contracts or validators: CC-001, CC-003, CC-004, CC-008, CC-010, CC-018, CC-019, CC-021 and CC-023. CC-005 and CC-007 are false positives. CC-009, CC-016 and CC-027 are undecidable. CC-020 is a concrete miss: a prior PASS cross-surface audit was followed by four identity/projection failures and a source-path repair.

Raw edge flags overlap: consequence 10, claim 8 and authority 7. The incremental evidence is one consequence case and one claim-plus-authority case; no single edge is established as generally dominant. The descriptive false-positive burden is 2/15 flags, and the holdout split contains two incremental signals, two redundant positives, two controls and one undecidable case. These are case counts, not accuracy or incidence estimates.

## 4. Diagnostic decisions

- `PROVENANCE_WITHOUT_CEILING`: `SINGLE_CASE_SIGNAL` (CC-026 incremental; four redundant cases).
- `ABSTENTION_AS_AVOIDANCE`: `FALSE_POSITIVE_PRONE` (CC-005 treated a deliberate unsafe/unavailable abstention as avoidable without a safe alternative).
- `BUDGET_AS_HARM_LICENSE`: `NO_HISTORICAL_SUPPORT` (no selected case meets its minimum observable criteria).
- `SIGNATURE_WITHOUT_CONTESTABILITY`: `INSUFFICIENT_EVIDENCE` (three redundant cases and one undecidable case; no independent incremental signer/contest failure).
- `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY`: `SINGLE_CASE_SIGNAL` (CC-012 incremental; one redundant, one false positive and one undecidable case).

The result does not preserve a label because it is theoretically attractive. In particular, a signer or actor reference without a later material contest/revocation/consequence failure is not sufficient for `SIGNATURE_WITHOUT_CONTESTABILITY`.

## 5. Strict threshold and bounded verdict

CC-012 and CC-026 satisfy the narrow research signal conditions: distinct real events, distinct task families, pre-outcome actionable warnings, no equivalent local capture of the specific junction, independent later support and holdout presence. The result is still not a basis for a new canonical object because discovery yielded no incremental positive, one real miss remains, three cases are undecidable, most positive-looking flags are redundant, and the test is not cognitively independent.

Final verdict: **`PARTIAL_INCREMENT`**. The two cases justify recording a bounded `CROSS_CONTRACT_FAILURE_SIGNAL_CONFIRMED` research observation. They do not justify `CROSS_CONTRACT_INCREMENT_CONFIRMED` as a general capability, a new failure class, a mandatory gate, a schema, a registry, a runtime state or authority. Retain `EXISTING_FEDERATED_CONTRACTS + CROSS_CONTRACT_REVIEW_MAP` as a non-canonical review lens only.

The negative findings are material: `BUDGET_AS_HARM_LICENSE` has no historical support, `SIGNATURE_WITHOUT_CONTESTABILITY` has no independent support, discovery produced zero incremental positives, and CC-020 shows that the lens can miss a real cross-surface regression. A future study would need a newly frozen corpus or one explicitly authorized executable junction fixture.

## 6. Deliverables

- `ignition/docs/governance/cross-contract-historical-blind-test-2026-09-05.md`
- `ignition/docs/governance/cross-contract-failure-casebook-2026-09-05.md`
- `ignition/data/research/cross-contract-blind-test-2026-09-05/` (manifest, criteria, packets, blind outputs, results, freeze and exclusion ledgers)
- `ignition/reports/governance/task-IGNITION-20260905-155.md`
- `ignition/agent-results/IGNITION-20260905-155-result.md`
- Minimal `ignition/docs/governance/README.md` discoverability entry.

The casebook keeps every pre-outcome card above `--- UNBLIND ---` and later evidence below it. The result dataset carries the exact outcome and resolution pointers. No production registry or formal gate consumes the research data.

## 7. Validation and lifecycle

The first final-head Foundation CI run (`33940447499`) failed because the existing official function-census and nonfunction-claim generators auto-discovered the new research corpus and narrative/result files as canonical inputs. The unbounded generator trial produced six extra function candidates and 176 extra nonfunction claim rows, which would have violated the research-only boundary. Task-scoped exclusions were then added to those two official generators: the research data stays visible to source-discovery accounting but cannot feed the authoritative function census or nonfunction claim registry. This was an input-boundary repair, not a validator, gate, schema, runtime, authority or lifecycle change. Official regeneration and local `validate_foundation.py` then returned `ALL_FOUNDATION_VALID` (`63/63`), with both generator `--check` commands deterministic.

The next final-head Foundation run (`33942616041`) passed the core Foundation, function and nonfunction checks but failed in the downstream human-result/self-correction bundle because its official projections had not been regenerated for the changed governance inputs. The repository-owned generators were then run: task-scoped `build_human_results` exclusions keep the research casebook/report/result out of the human result ledger, and `run_self_correction`, `build_knowledge_experience`, `build_fire_seed_census` and `build_claim_browsers` refreshed their projections. Local human-result, self-correction, Fire Seeds, Knowledge Experience audit/determinism and architecture checks now pass. This remains generated input/projection maintenance; no validator, gate, schema, runtime, authority or lifecycle rule changed. A new final-head CI run is required before remote validation can be called complete; the failed run is retained as a residual.

Local validation parsed every JSON/JSONL artifact, recomputed all deterministic splits, verified every manifest commit and selected path with `git cat-file`, matched blind and result case IDs/fields, and passed `git diff --check`. The repository-owned path-classification generator was run after staging the new records; its follow-up `--check` passed 10/10 (`tracked=4013`, `manifest=4013`, no unresolved or stale paths, no anti-backflow violation). These checks establish repository-local data integrity only. No full repository regression is claimed for the docs/research-only change; no validator was weakened and no expected skip was converted into a pass.

The final formal SHA, tracking/remote equality, CI state, Draft PR observation and independent `1111` receipt are external evidence planes. The formal candidate must remain Draft and non-Current; those observations are recorded in the separate control-repository receipt and are not used to upgrade this report's epistemic status.
