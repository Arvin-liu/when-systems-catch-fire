# IGNITION-20260905-156 任务报告：前瞻性 cross-contract junction fixture 复现

Status: `RESEARCH_COMPLETE / BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE / DRAFT_PR_PENDING / NON_CURRENT`

## 1. 命令源、起点与权限边界

- Command source: `Arvin-liu/1111:agent-commands/IGNITION-20260905-156.md`
- Command source commit observed on `main`: `966e88605a53d68a7812663d9a844d05bd032a47`
- Command blob SHA: `02fb09c23f4191fa9b08cf96eda65030bf0d7021`
- Command content SHA-256: `91df65029cd6962b5026a207757dc430c27253bec16a18d084778787cbb97045`
- Formal repository: `Arvin-liu/when-systems-catch-fire`
- Exact Task155 starting head: `work/IGNITION-20260905-155@9bed8e42ee824fc0c0a10717b6163fe7052423e8`
- Task154 predecessor: `56e57906ef6e54c3721499430aaec8da1182c322`
- Task155 PR observed before execution: `#205 OPEN + DRAFT`, head `9bed8e42...`, base `work/IGNITION-20260904-154@56e57906...`
- Formal branch: `work/IGNITION-20260905-156`

The shared `when-systems-catch-fire` checkout and shared `1111-sync` checkout were not modified. Work was performed in an independent formal clone. The known stale pointers `1111/instructions/CURRENT.md` and `1111/relay/current` were recorded and preserved unchanged; they did not override this explicit command. No live external/provider/authenticated operation, executor, secret, production configuration, authority action or lifecycle promotion was used.

The only non-research source changes are task-scoped input-boundary exclusions in the official function-census, nonfunction-claim and human-results discovery configurations. They keep the research paths visible to repository accounting while preventing research labels and receipt prose from feeding canonical projections. No production validator, gate, runtime, authority, capability, schema, registry or canonical layer was added or weakened.

## 2. Final freeze and amendment history

The final freeze was committed before the final blind scoring:

- Final freeze commit: `4321dcb2f9f434ed7936d5cb5c8648089eeb4964`
- Freeze status: `FROZEN_BEFORE_BLINDED_SCORING`
- Base commit recorded in every fixture: `9bed8e42ee824fc0c0a10717b6163fe7052423e8`
- Final frozen model hash: `0fbdced20181897d3faefea04b9f0ea9da933723606f8c21fe7428db8f42ce71`
- Final frozen threshold hash: `2e509a21b354947fd36193d941d4e318fe37b61210495e7fb58da7b88e3d90f7`
- Blind packet digest: `f2e3ebe92b9f840cd2f3428cf6cca7cf5188aac1094859ab242934031fa91a47`
- Answer-key digest: `83cfc510f9acf7f15b6a0a53e5052ee66c91be3b2fe4d98d0d4f66a5f11678d6`
- Blind and answer-key digests differ: `true`

The first two execution attempts were not silently overwritten:

1. `e942fb8482adbca5f4dd29eb9377b2aef0218f73` was invalidated because the initial partial metamorphic aggregator counted models without the relevant predicate as repair violations (`57` false aggregation failures).
2. `f521ffa67de43285e140e1a2ace7aae0730d958a` corrected that suite but did not yet materialize counterfactual minimality, lineage-share enforcement, safe Draft controls and explicit open-obligation fields.

Both runs, their frozen files, score outputs, summaries and validation records are retained under `data/research/cross-contract-prospective-fixtures-2026-09-05/invalidated-freeze-*` and indexed by `restart-ledger.json`. The final amendment-02 freeze is the only run used for the result below.

## 3. Prospective corpus and scoring method

The corpus contains 48 pairs / 96 instances, with eight pairs in each family. Each pair has one primary packet and one matched control in the same deterministic split. The final truth partition is 46 synthetic defect instances, 48 matched controls and two signer-only ambiguous-stress instances. The split is `SHA256(pair_id).first_byte mod 3`: 36 calibration pairs and 12 holdout pairs.

| Family | Shape | Historical genealogy | Pairs |
|---|---|---|---:|
| F1 | consequence/accountability, observer, owner, retry and stop | CC-012 shape; no historical record replay | 8 |
| F2 | admission, Base/Delta scope, lifecycle and provider/current distinction | CC-026 shape; no historical record replay | 8 |
| F3 | source, identity, projection, surface, release and lifecycle binding | CC-020 shape; novel recombinations | 8 |
| F4 | claim ceiling, evidence, action and claim/action identity | Task155 claim-ceiling map | 8 |
| F5 | effect, preimage, rollback and stop path | Task155 rollback/consequence map | 8 |
| F6 | signer, approval, scope, contestability and consequence visibility | Task155 signer diagnostic; signer-only cases deliberately stress unsupported vocabulary | 8 |

The anti-overfitting counts are 39 novel-recombination pairs, 46 distractor-bearing pairs and 46 cross-object-family pairs. Controls include safe `NON_INTENT`/Draft admission, valid abstention, open-but-accountable reconciliation obligations, matched reversible controls and explicitly non-authoritative surfaces. The F2-P06 pair makes the matched control a safe Draft state and changes only Current-use attempt in the primary. The blind packets contain no truth class, role, injected change, historical outcome or answer-key field.

The four frozen models were scored in order M0 `EXISTING_ONLY`, M3 `THREE_EDGE_V1`, M3R `THREE_EDGE_REFINED` and M4B `THREE_EDGE_PLUS_BINDING_CHALLENGER`. M3R sharpens the claim edge with exact source/identity/projection/surface/release relations. M4B adds only existing object/version/scope/lifecycle/reference binding checks and is not allowed to invent a new authority or truth state. The scorer reads `blind-packets.jsonl` and `model-definitions.json`; it does not load `answer-key.jsonl`. Unblind/metrics is a separate command.

## 4. Final empirical result

The two final clean-state blind scoring passes each produced 384 model rows and were byte-identical:

- Score-run SHA-256 for both passes: `c53ed43394aa7ece8fd138b1e272b745b3e59a4a908a16b17c4ce37a22db96e3`
- Final unblind: `96` results, `808` metamorphic checks, `0` metamorphic violations
- Invalid fixtures: `0`
- Counterfactual-minimality rows: `75`; every row is `REQUIRES_NEW_LOCAL_PREDICATE / REVIEW_ONLY`

### Holdout metrics

| Model | Defects detected | Incremental beyond M0 | Redundant with M0 | False positives on 12 controls | False negatives | Exact actionability |
|---|---:|---:|---:|---:|---:|---:|
| M0 | 0/12 | 0 | 0 | 0 | 12 | n/a |
| M3 | 6/12 | 6 | 0 | 0 | 6 | 1.0 |
| M3R | 8/12 | 8 | 0 | 0 | 4 | 1.0 |
| M4B | 12/12 | 12 | 0 | 0 | 0 | 1.0 |

The holdout M3 incremental fixtures are `F1-P04`, `F2-P03`, `F4-P06`, `F5-P01`, `F5-P08` and `F6-P04`. M3R adds two detections beyond M3, `F3-P02` and `F3-P03`, without adding a fourth edge. M4B adds four detections beyond M3R: `F2-P01`, `F3-P07`, `F4-P07` and `F6-P01`, spanning `lifecycle_epoch`, `claim_action_object` and `approval_action_object`. M3R incremental detections cover all six families; the largest single historical-lineage-inspired family share is `0.25`, below the frozen `0.50` ceiling.

Across all 96 instances, M0 detected 13 defect-local failures; M3, M3R and M4B detected 32, 36 and 46 defects respectively. All four models had zero matched-control false positives. The 48 controls remain descriptive controls, not a population accuracy estimate. The two ambiguous signer-only stress instances were not flagged by any model.

## 5. Required questions and bounded answers

1. **Was M0 fair?** Yes within the declared protocol: it received only packet-local contract statuses and caught 13 local-baseline defects; all cross-junction incremental rows had local statuses `PASS`. This is a fairness check for the fixture harness, not proof that the repository's entire local contract inventory is complete.
2. **Does M3 produce non-redundant holdout signal?** Yes: six holdout incremental detections, all exact-actionable and with zero matched-control FP. M3 is not sufficient for the full source/identity/projection family.
3. **Does M3R gain without a fourth edge?** Yes: two holdout detections beyond M3, both F3 source/projection cases, while retaining the same claim/authority/consequence edge categories.
4. **Does M4B gain beyond M3R?** Yes: four additional holdout defects, three binding subtypes, zero additional control FP and no new authority/truth state. This meets the pre-frozen challenger threshold only as a bounded research candidate.
5. **Can a CC-020-like defect be caught without a fourth edge?** Yes for the source/path/identity/projection/surface relation represented by F3-P02/P03: M3R catches it on the refined claim edge. That does not establish general CC-020 historical recall.
6. **Are family flips stable?** M3R's eight holdout increments replicate across all six families, with family shares 0.125–0.25. M4B's four additional flips occur across four families and three subtypes. This is cross-family fixture replication, not external generalization.
7. **What is the FP and ambiguity picture?** All model/control FP counts are zero on the matched controls; M3R/M4B holdout FP rate is `0.0`; both ambiguous signer-only stress packets remain unflagged. The metamorphic suite reports `0` model-quality violations.
8. **What happened to the CC-012-like and CC-026-like genealogies?** F1 and F2 each contribute holdout incremental synthetic fixtures, but they are repository-shaped recombinations rather than replays of the historical records. Their result supports only a prospective fixture signal.
9. **Does the signer/contestability label survive?** No as an independently supported failure vocabulary. The two signer-only stress controls have no consequence gap and no model flags them; the disposition remains `INSUFFICIENT_DISCRIMINATION`.
10. **Should weak diagnostics be retired?** `BUDGET_AS_HARM_LICENSE` and `ABSTENTION_AS_AVOIDANCE` remain insufficiently discriminated; `SIGNATURE_WITHOUT_CONTESTABILITY` remains insufficient. `PROVENANCE_WITHOUT_CEILING` and `COMPLETE_RECORD_WITHOUT_ACCOUNTABILITY` have bounded synthetic support, not a real historical failure-class upgrade. No label is promoted merely for conceptual elegance.
11. **Does the junction-invariant candidate survive?** The M4B challenger passes the pre-frozen holdout threshold and survives as `BINDING_CHALLENGER_SUPPORTED_AS_RESEARCH_INVARIANT_CANDIDATE`. Counterfactual minimality remains `REVIEW_ONLY`; therefore “candidate” is deliberately weaker than “invariant”.
12. **What exact predicate is supported, and what was not added?** The candidate is equality of existing source, identity, projection, surface, release and admission tuples over `(object_id, version, scope, lifecycle_epoch)`, plus existing `action.claim_id == claim.object_id` and `action.approval_id == authority.approval_id`. No new authority, truth, capability, lifecycle state, registry, schema or production gate was introduced.
13. **What is the next step?** Preserve the result as a replaceable review lens, keep the formal and receipt PRs Draft, and if further work is authorized, run a fresh independently authored corpus that explicitly compares a narrow local-predicate alternative. Do not promote this synthetic result to Current, production readiness, Owner acceptance or external truth.

## 6. Metamorphic and counterfactual evidence

The final suite has 808 checks and zero violations. It includes exact single-field repair, binding locality, irrelevant evidence volume, valid-signature versus consequence, rollback label versus irreversible effect, safe-authorized alternative, signer-only stress and deadline passage. Not-applicable model coverage is recorded separately from failures, and the 24 safe-authorized route changes are marked explicitly allowed.

For every incremental detection, `counterfactual-minimality.jsonl` asks whether one narrow local predicate could be an alternative explanation. The answer is not silently inferred: all 75 rows are marked `REQUIRES_NEW_LOCAL_PREDICATE`, `POSSIBLE_IN_PRINCIPLE_BUT_NOT_EXPERIMENTALLY_COMPARED` and `REVIEW_ONLY_NO_LOCAL_MUTATION`. Thus the surviving M4B structure remains a bounded review lens even though its frozen threshold passes.

## 7. Validation, intermediate failures and lifecycle

Completed local checks include:

- `py_compile` and the five research unit tests;
- deterministic corpus generation and `generate --check`;
- separate `validate-freeze` after the final freeze commit;
- blind-packet separation and exact model-definition comparison;
- two clean-state scoring passes from detached clones at `4321dcb2...`, byte identity confirmed;
- final unblind, metrics, metamorphic and counterfactual generation;
- `git diff --check`.

Formal remote evidence was observed on the exact initial submitted candidate head before this report-recording commit:

- Draft PR [#206](https://github.com/Arvin-liu/when-systems-catch-fire/pull/206) is `OPEN + DRAFT`, with base `work/IGNITION-20260905-155@9bed8e42ee824fc0c0a10717b6163fe7052423e8` and initial candidate head `work/IGNITION-20260905-156@92f2a1f4bb04ba1fdf26901e767908f977a11b16`.
- `foundation-validation` run `33967225384`, job `101309362262`, completed `success` with 49 completed steps.
- `architecture-pages` run `33967225387`: build job `101309362294` completed `success`; deploy job `101309466377` was `skipped` because the PR is Draft.
- `repository-path-accounting-preflight` run `33967225386`, job `101309362260`, completed `success`.
- `q33-governance-validation` run `33967225481`, job `101309362401`, completed `success`.

These remote observations are a separate evidence plane and cannot upgrade this report's research status. The commit that records these observations advances the formal branch; the resulting branch head and its own exact CI binding are recorded in the independent relay receipt. No full repository regression, Current transition, merge, Ready promotion or Owner acceptance is claimed.

The stale 1111 pointers remain an explicit residual. The two invalidated freezes and their 57-violation first-run diagnostic are retained rather than erased. No post-final-freeze threshold, model definition, answer key or holdout-selection change was made.

## 8. Deliverables

- `ignition/docs/governance/cross-contract-prospective-fixture-experiment-2026-09-05.md`
- `ignition/docs/governance/junction-invariant-candidate-assessment-2026-09-05.md`
- `ignition/docs/governance/cross-contract-prospective-casebook-2026-09-05.md`
- `ignition/data/research/cross-contract-prospective-fixtures-2026-09-05/`
- `ignition/tools/research/cross_contract_prospective_experiment.py`
- `ignition/tests/test_cross_contract_prospective_experiment.py`
- `ignition/reports/governance/task-IGNITION-20260905-156.md`
- `ignition/agent-results/IGNITION-20260905-156-result.md`
- Minimal discoverability entry in `ignition/docs/governance/README.md`

The formal candidate, any independent receipt, and any CI result are evidence of repository state and review workflow only. They do not prove Current status, production/publication readiness, external truth, epistemic acceptance or Owner acceptance.
