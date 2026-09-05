# Cross-contract historical blind test — 2026-09-05

Status: `RESEARCH_COMPLETE / PARTIAL_INCREMENT / DRAFT_PR_PENDING_REVIEW / NON_CANONICAL / NON_CURRENT`

This document reports the empirical falsification requested by `IGNITION-20260905-155`. It tests whether the research-only `CROSS_CONTRACT_REVIEW_MAP` can give a concrete warning before a later repository event, after the local contracts visible at that time fail to give an equivalent warning. It does not introduce a new failure class, canonical layer, schema, validator, gate, registry, runtime state, capability or authority.

## Binding and scope

- Command source: `Arvin-liu/1111:agent-commands/IGNITION-20260905-155.md` at `b75ad68925178ef4cc7ab97c53fa63cfe9965902`
- Command blob SHA: `ceca66aa7734ba338923461345d52442e5bdaf1e`
- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Exact Task154 starting head: `56e57906ef6e54c3721499430aaec8da1182c322`
- Task155 branch: `work/IGNITION-20260905-155`
- Task155 base: `work/IGNITION-20260904-154`
- Task153 and Task154 remain Draft candidates; neither was promoted, merged, marked Current, accepted by Owner or epistemically accepted.
- The empirical corpus contains repository-local events before the Task153 boundary. Task153 and Task154 are design inputs only, not cases. Task152 is the latest eligible case.
- Sampling is purposeful maximum-variation sampling across lifecycle, evidence, control-plane, runtime, publication and provider-boundary families. The counts are descriptive and cannot estimate an event rate.
- No live external executor, provider admission, authenticated action, permission expansion, secret read, configuration change or successor task was performed.

The stale `1111/instructions/CURRENT.md` and `1111/relay/current` pointers were observed during preflight and intentionally left unchanged under the Owner confirmation. They are recorded as residuals in `ignition/data/research/cross-contract-blind-test-2026-09-05/freeze-ledger.json` and are not control inputs for this task.

## Frozen data-level design

The machine-readable corpus is under the explicit `data/research` directory:

- `case-manifest.json` — 27 stable case IDs, event and pre-outcome pointers, later source pointers, cutoffs and deterministic split.
- `exclusion-ledger.json` — zero post-freeze exclusions; Task153/154 excluded by rule.
- `criteria.json` — frozen claim, authority and consequence questions; minimum observable criteria for all five diagnostics; redundancy, incremental, false-positive and undecidable rules.
- `blind-packets.jsonl` — one pre-outcome packet per case. It contains no later outcome or resolution payload.
- `blind-outputs.jsonl` — the two review passes and predicted warning for each case, frozen before unblinding.
- `results.jsonl` — unblinded case classification and evidence links.
- `freeze-ledger.json` — hashes, exact baseline, residual pointers and the unblind record.

Freeze evidence:

| Artifact | SHA-256 |
| --- | --- |
| `case-manifest.json` | `05b74d11e07aeaf9f454de07af323ff5f4f7a82ae9f3c5a7a03962475d5c1a04` |
| `exclusion-ledger.json` | `4af7831e53bf8b08e8af5ee1b75071d63d3106becb20b81cb24b5c234528f12d` |
| `criteria.json` | `15d08c6f754cf102e2258f16e7b1a8ab2f69f028593d2f0474dc8a6e196f8f43` |
| `blind-packets.jsonl` | `b7ce6f59dae65002e5fc4bb5e124087f07ec68927ff9e942aaf53c493a545a92` |
| `blind-outputs.jsonl` | `1c7449424a42b7eadd80bb989f598097e0caa71a4d918fc4c82807a6baafbeaa` |
| blind freeze commit | `6618f0b8d5dee9a63e2970c470da95eefc59f4f4` |

The split is `SHA256(case_id).first_byte mod 3`: values 0/1 are discovery and value 2 is holdout. It yields 20 discovery cases and 7 holdout cases. The authoring agent had repository-history access while selecting and writing the corpus; this is temporal/data-level blinding, not cognitive independence or an independent replication.

## Two review passes

For every case, Pass 1 asks what the local contract, validator, gate and record visible at the cutoff could state, and whether that was sufficient to stop, review, repair or refuse. Pass 2 uses only the three frozen junction questions:

1. **Claim edge:** do provenance, evidence, M-E and claim ceiling align with wording, decision reason and action, or does the action cross the evidence ceiling?
2. **Authority edge:** are proposer, approver, refuser, revoker and accountable human/role visible and distinct, or does an approval/signature/capability record omit a contest boundary?
3. **Consequence edge:** are execution, observation, ownership and stop/rollback/reconciliation paths connected, or can a complete trace leave an effect unowned or unreconcilable?

A `FLAG` had to be specific, visible before the cutoff and actionable. A local warning already equivalent to the flag is redundant. A later explanation cannot turn an otherwise unsupported pre-outcome concern into a positive. Evidence that cannot establish the predicate or its ordering remains `UNDECIDABLE`.

## Descriptive results

There are 15 `FLAG` outputs, 11 `NO_FLAG` outputs and one `UNDECIDABLE` output. Unblinding gives:

| Classification | Count | Share of 27 (descriptive only) |
| --- | ---: | ---: |
| `INCREMENTAL_TRUE_POSITIVE` | 2 | 7.4% |
| `REDUNDANT_TRUE_POSITIVE` | 9 | 33.3% |
| `FALSE_POSITIVE` | 2 | 7.4% |
| `TRUE_NEGATIVE_CONTROL_PASS` | 10 | 37.0% |
| `MISS_FALSE_NEGATIVE` | 1 | 3.7% |
| `UNDECIDABLE` | 3 | 11.1% |

The two incremental cases are both holdout cases:

- **CC-012, Task136 live bridge / Hermes timeout:** the local receipt represented timeout, unknown effect and required reconciliation, but did not expose a concrete accountable observer/stop binding. Later read-only reconciliation independently found no attempt PID/PGID, durable workspace, session pointer, raw output or matching artifact and kept the obligation open.
- **CC-026, Task150 admission scope:** the Draft closeout preserved lifecycle and provider non-intents but did not separate the Base operation from the Delta extension as admission objects. Later Owner reopening removed the combined gate, prevented Delta from polluting Base and kept both objects out of Current/live authority.

These cases are from different task families and subsystems: live executor/reconciliation consequence handling and provider-bound visualization admission/lifecycle authority. Both were holdout cases, so the frozen questions reproduced a bounded signal after the discovery wording was fixed. Discovery contained no incremental positive, which limits claims about stability and is one reason the final verdict is `PARTIAL_INCREMENT`, not a general performance claim.

The nine redundant positives are CC-001, CC-003, CC-004, CC-008, CC-010, CC-018, CC-019, CC-021 and CC-023. In each, the local evidence gate, lifecycle contract, projection validator or provider boundary already supplied the same actionable warning or repair predicate. The two false positives are CC-005 (a deliberate unsafe/unavailable abstention with no safe authorized alternative) and CC-007 (a policy-level timeout/reconciliation concern without a concrete Task124 unowned effect). CC-009, CC-016 and CC-027 remain undecidable because their outcome sources cannot establish the specific junction or its ordering. CC-020 is a miss: a PASS cross-surface audit was followed by four identity/projection failures and a source-path repair.

By edge, the frozen review produced 10 consequence flags, 8 claim flags and 7 authority flags. The counts overlap because a case can carry more than one edge. The two incremental cases contain one consequence signal (CC-012) and a claim-plus-authority signal (CC-026). Consequence is the noisiest descriptive edge because it carries one false positive and one undecidable case; claim has no classified false positive in this corpus but is mostly redundant; authority has one false positive and one undecidable case. These are corpus observations, not population rates.

## Five diagnostic dispositions

The labels remain review vocabulary only. They were not promoted to protocol primitives.

| Diagnostic | Empirical disposition | Evidence |
| --- | --- | --- |
| `PROVENANCE_WITHOUT_CEILING` | `SINGLE_CASE_SIGNAL` | CC-026 is one holdout incremental signal. CC-001, CC-003, CC-021 and CC-023 are redundant because local claim/source contracts already expose the boundary. |
| `ABSTENTION_AS_AVOIDANCE` | `FALSE_POSITIVE_PRONE` | CC-005 overread a deliberately fail-closed unsafe/unavailable route; no safe authorized alternative was visible. |
| `BUDGET_AS_HARM_LICENSE` | `NO_HISTORICAL_SUPPORT` | No pre-153 case met the minimum criteria of an explicit budget choice that externalized or concealed material harm across a Charter/policy/stop boundary. The label is not retained on conceptual importance alone. |
| `SIGNATURE_WITHOUT_CONTESTABILITY` | `INSUFFICIENT_EVIDENCE` | CC-004, CC-010 and CC-019 are redundant local authority/recovery boundaries; CC-009 is undecidable. No independent incremental signer/contest failure is established. |
| `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY` | `SINGLE_CASE_SIGNAL` | CC-012 is one holdout incremental consequence signal. CC-007 is false positive, CC-008 and CC-018 redundant, and CC-027 undecidable. |

`SIGNATURE_WITHOUT_CONTESTABILITY` therefore has no independent historical support in this corpus. A signer or actor reference alone was not treated as a failure; the case needed a missing refusal, revocation, rollback, scope or consequence-contest route that later mattered.

## The ten required questions

1. **How many true incremental historical failures?** Two: CC-012 and CC-026.
2. **How many different task families/subsystems?** Two independent families/subsystems: Task136 live bridge/reconciliation and Task150 provider-bound admission/lifecycle scope.
3. **Did holdout reproduce the signal?** Yes, both incremental cases are holdout cases (2 of 7 holdout records). Discovery produced zero incremental positives, so this is bounded holdout support rather than broad stability evidence.
4. **Which flags merely repeat existing validators?** CC-001, CC-003, CC-004, CC-008, CC-010, CC-018, CC-019, CC-021 and CC-023; nine redundant positives.
5. **Which edge has the most increment?** Consequence has the larger raw flag count (10). The incremental split is one consequence case (CC-012) and one combined claim/authority case (CC-026), so no single edge is established as universally superior.
6. **Which edge is easiest to overflag?** Consequence is the clearest overgeneralization risk in this corpus: it has the highest raw flag count and includes a false positive plus an undecidable case. Authority also overflags CC-005; claim produced no classified false positive but was often redundant.
7. **What is the disposition of each diagnostic?** `PROVENANCE_WITHOUT_CEILING=SINGLE_CASE_SIGNAL`; `ABSTENTION_AS_AVOIDANCE=FALSE_POSITIVE_PRONE`; `BUDGET_AS_HARM_LICENSE=NO_HISTORICAL_SUPPORT`; `SIGNATURE_WITHOUT_CONTESTABILITY=INSUFFICIENT_EVIDENCE`; `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY=SINGLE_CASE_SIGNAL`.
8. **Does `SIGNATURE_WITHOUT_CONTESTABILITY` have real historical support?** No independent support. Three flags were redundant and one was undecidable; no later outcome requires the diagnostic as a non-equivalent lens.
9. **Did all relevant local contracts pass while their combination later caused a confirmed problem?** Yes, in a bounded sense. CC-012 had a technically valid timeout receipt, durable closeout and verification record while the consequence/accountability binding remained unresolved. CC-026 had a valid Draft/provider-boundary posture while the combined Base/Delta admission topology still needed separation. Neither case establishes a new canonical failure class.
10. **Is there enough evidence to make `cross-contract failure` a worthwhile next research object?** Yes, as a bounded research question: two independent holdout signals, actionable pre-outcome warnings and a descriptive false-positive burden of 2/15 flags. The evidence does not justify a protocol object, failure class, mandatory gate or authority. The safe conclusion is `PARTIAL_INCREMENT` with a research-only lens retained for reproduction.

## Strict threshold and final verdict

The two positive cases meet the narrow signal threshold: they are independent real events from different families; the local records did not express the specific junction warning equivalently; the frozen warning was available before the later result; the later records independently support the junction; and the holdout contains both signals. The corpus also exposes limits: nine redundant flags, two false positives, one miss, three undecidable cases, zero discovery incremental positives and no cognitive independence. The 27 cases are purposefully selected and cannot support an accuracy or incidence claim.

Final recommendation: **`PARTIAL_INCREMENT`**. The report records a bounded `CROSS_CONTRACT_FAILURE_SIGNAL_CONFIRMED` for CC-012 and CC-026 as a research observation, while refusing to promote `cross-contract failure` into a new object. Keep `EXISTING_FEDERATED_CONTRACTS + CROSS_CONTRACT_REVIEW_MAP` as a non-canonical review lens only. Do not add a canonical layer, schema, registry, validator, mandatory gate, runtime state, capability or authority from this result.

Negative findings are part of the result: `BUDGET_AS_HARM_LICENSE` has no historical support; `SIGNATURE_WITHOUT_CONTESTABILITY` has no independent support; the discovery split yielded no incremental case; and CC-020 demonstrates that the lens can miss a real cross-surface regression. A future study should begin with a new frozen corpus or a named executable junction fixture under explicit Owner direction, rather than treating this report as automatic successor authority.

## Validation and lifecycle boundary

The machine records were parsed as JSON/JSONL, all manifest commits and selected paths were checked with `git cat-file`, deterministic split recomputation matched every case, blind and result fields matched case-for-case, and `git diff --check` passed. The repository-owned path-classification generator was run after the new tracked records were staged; its `--check` then passed 10/10 with `tracked=4013`, `manifest=4013`, no unresolved or stale paths and no anti-backflow violation. No production validator was changed or fed these records; no formal full-repository regression is claimed for this research-only addition. The formal branch remains Draft and non-Current. Exact final SHA, remote-ref equality, CI state, Draft PR state and the independent `1111` receipt are separate evidence planes and are recorded outside this self-referential report when available.

Primary evidence cards: [`cross-contract-failure-casebook-2026-09-05.md`](./cross-contract-failure-casebook-2026-09-05.md). Machine evidence: [`cross-contract-blind-test-2026-09-05/`](../../data/research/cross-contract-blind-test-2026-09-05/).
