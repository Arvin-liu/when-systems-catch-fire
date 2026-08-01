# 点火迭代操作法 / Ignition Iteration Method

Historical: `1.3.0` (incremental execution and selective materialization; Q32I closeout complete)

Current: `1.4.0` (continuous stage snapshot publication; snapshot record merged to Main via PR #134 and promoted to Current by controlled sync R1-20260726; R5-A snapshot is PUBLISHED_SNAPSHOT but still not Accepted/Current/Activated)

Historical: `1.2.0` (typed declared change-propagation closure; superseded by 1.3.0)

Earlier Historical: `1.1.0` (synchronization registry closure; superseded by 1.2.0)

Q32I lifecycle: Accepted, Merged by PR #62, Current and Closed. Q33 launch packet ready externally; Q33 and Q34—Q40 not started.

1.4.0 lifecycle: Current. Its snapshot record (`data/operations/stage-snapshots.json` and deterministic repository Markdown projection) entered Main via the PR #134 merge (R3 exact-head acceptance of the repair stack + R2 main closeout, merge commit `f9abf90e`) and the method was promoted to Current by controlled sync R1-20260726; the R5-A snapshot is `PUBLISHED_SNAPSHOT` but still not Accepted/Current/Activated. The `PUBLISHED_SNAPSHOT` transition was executed by that same controlled sync.

Status: canonical operation method. This method governs how 点火 changes itself. It is not a truth layer, proof system, value charter, causal model or substitute for external evidence.

Historical lifecycle evidence: method 1.3.0 entered `main` through Q32I third independent exact-head acceptance, PR #62 ordinary merge and the external checks required at that historical time. Method 1.2.0 remains Historical. Task 101 retires the separate deployed reading surface from current and future gates without deleting its historical evidence.

## 0. Read This Boundary First

An iteration can produce a candidate artifact, a verified candidate, an accepted change, a merged change or a current repository capability. These are different states.

An open Draft PR is never current project capability. A merged change becomes current only after exact-head merge verification and required post-merge checks.

Following this method can show that an operation was disciplined. It cannot prove that a claim is true, valuable, causal, complete or wise.

## 1. Remote-Truth Recovery

Before planning, recover the actual repository state:

- fetch current `main`;
- inspect open PRs, branches and exact HEADs;
- read `README.md`, `docs/project-current-state.md`, `AI-HANDOFF.md`, `AI-START-HERE.md`, `llms.txt`, `SUMMARY.md` and this file;
- inspect schemas, tools, tests and workflows relevant to the requested area;
- inspect frozen assets and explicit forbidden surfaces;
- read recent reports, completion seals and current-state records;
- treat chat memory, summaries and prior receipts as leads, not authority.

Output: a short remote-truth note with repository, branch, PR, starting HEAD, known open work and blocked surfaces.

## 2. Gap-First Selection

Select the smallest material gap before naming a new architecture.

Ask:

- What actual artifact, test, schema, state page, report or workflow is missing, stale or contradictory?
- What user-facing or Agent-facing decision becomes safer after this gap is closed?
- What is the smallest reversible state-changing action that closes it?
- What evidence would show that no change is needed?

Do not invent a grand name first and then look for a place to attach it.

## 3. Change Classification

Classify the change before editing:

- `REPAIR`
- `CAPABILITY_ADDITION`
- `INTERFACE_CHANGE`
- `EVIDENCE_UPDATE`
- `GOVERNANCE_CHANGE`
- `RELEASE_OR_CURRENT_STATE_SYNC`
- `HISTORICAL_ONLY`
- `OPERATIONS_METHOD`

Multiple labels are allowed, but each label must have an affected surface and validation path.

## 4. Claim Ceiling

Every iteration states its maximum justified claim.

Examples:

- `artifact_created`
- `schema_validated`
- `workflow_passed`
- `implementation_observed`
- `mechanism_plausible`
- `mechanism_discriminated`
- `current_state_synchronized`
- `causal_identification_pending`
- `insufficient_evidence`

Never raise the claim ceiling because the prose is convincing, the maintainer wants the result, CI is green, or multiple AI systems agree.

For any function, model, theorem, formula, law, decision rule or cross-domain claim, apply `docs/foundation/claim-governance-and-function-identity.md` before publication. Mathematical maturity M0—M7 and external evidence E0—E7 are independent; a high M level never raises E. Run the ten audit gates. Any gate that cannot be automated reliably must return `REQUIRES_HUMAN_REVIEW`, never an inferred pass. A withdrawn strong claim must change its text, scope, allowed inference direction, dependencies, public projection and test expectation; renaming it cannot restore the conclusion.

The task-99 function-asset registry is closed only when every discovery has one canonical identity card and a final disposition. `UNRESOLVED_IDENTITY` plus `QUARANTINE_UNTIL_DEFINED` is an explicit bounded outcome, not a validator pass. Removing quarantine requires evidence that discharges the recorded proof or empirical obligation and a dependency/public-claim propagation review.

Task 100 applies the same boundary to all non-function assertions. A new theorem, law, mechanism, causal judgment, impossibility result, cross-domain correspondence, prediction, empirical assertion, ontology claim or framework conclusion must enter through `docs/foundation/future-claim-admission-protocol.md`; it must receive a canonical ID, thirteen gates, evidence lineage, dependencies, independent M/E status, one disposition and one public ceiling before current publication. A single-model failure never supports universal impossibility, and a renamed structural or meta label cannot restore a withdrawn conclusion.

## 5. Impact And Synchronization Matrix

For each iteration, decide whether these surfaces change:

- code and runtime behavior;
- schema and machine-readable data;
- tests and validators;
- workflows and CI;
- reports and completion seals;
- `README.md`;
- `docs/project-current-state.md`;
- `AI-HANDOFF.md`, `AI-START-HERE.md`, `llms.txt` and `SUMMARY.md`;
- versioning and changelog;
- governance, sustainability and licensing;
- frozen assets, legacy tables and historical evidence.

Use `CHANGE`, `NO_CHANGE_WITH_REASON` or `NOT_APPLICABLE`. A capability, identity, usage, current-state or handoff change must synchronize the front-door/current-state surfaces or record validator-enforced reasons.

### 5.1 Whole-Project State Transition

An iteration is a repository state transition, not merely a local file edit. A change to capability, identity, usage, handoff, lifecycle/current state, governance, deployment/rendering or this operation method must propagate to every affected declared surface. The project is not synchronized while any required human, AI, Agent, machine, current-state, version/history or deployment surface still projects the superseded state.

Not every registered surface must change. Every applicable surface must receive exactly one explicit `CHANGE`, `NO_CHANGE_WITH_REASON` or `NOT_APPLICABLE` decision with evidence. The canonical coverage topology is `data/operations/synchronization-surfaces.json`, validated by `schemas/operations/synchronization-surfaces.schema.json`. That registry describes synchronization obligations only; it is not a second store of substantive project truth.

### 5.2 Propagation Closure

Every method 1.1.0 iteration declares state-transition subjects, prior/proposed states, changed dimensions, source references and a claim boundary. Required assessments are derived from the synchronization registry and follow its declared dependency/derivation relations until the closure has no missing decision.

Human-visible entrances are first-class project surfaces. Capability, identity, current-state, usage, handoff or rendering changes must assess `README.md`, `HUMAN-READING.md`, `KNOWLEDGE/`, the relevant `RESULTS/` pages, `docs/project-current-state.md`, `SUMMARY.md`, `docs/USAGE.md`, `docs/ai-assistant-usage-reference.md`, `CHANGELOG.md`, `docs/VERSIONING.md`, `AI-START-HERE.md`, `AI-HANDOFF.md`, `llms.txt` and relevant operation templates whenever the registry triggers them.

Derived and external surfaces remain distinct from repository sources. Current human result projections are repository files generated from declared machine sources and checked for freshness; external systems, if a future task introduces one, require a separate registry entry and evidence. Local validation never proves an undeclared live external state.

### 5.3 Completion Levels

- `implementation_complete`: the local artifact, schema, tool and test work exists and passes its relevant local checks.
- `repository_synchronization_complete`: every registry-required repository surface has a validated decision and evidence, and repository-derived surfaces have been built where required.
- `external_synchronization_required`: at least one applicable rendered/deployed surface requires external evidence.
- `external_synchronization_attested`: the required exact external evidence has been recorded by its declared authority.
- `project_synchronization_complete`: repository synchronization is complete and every required external synchronization has been attested.

Implementation completion alone cannot make a task ready, accepted, merged, current or closed. Lifecycle requirements are derived per triggered surface from its registry `blocks` field:

- `Ready for GPT verification` requires implementation complete, repository synchronization complete, exact candidate-head CI/build evidence, an inspectable derived artifact where required, Draft lifecycle, and no unresolved `ready` blocker.
- `Accepted` requires independent acceptance of that exact Ready HEAD after fresh PR/HEAD/review/CI/build re-fetch, plus satisfaction of every triggered `accepted` blocker. A `post_merge_external_render_attestation` surface that blocks only `current`/`closed` does not block acceptance.
- `Merged` requires the accepted exact HEAD to enter `main`, ancestry verification, and every triggered `merged` blocker. Merged is not automatically Current.
- `Current` and `Closed` require merged lifecycle, truthful post-merge repository closeout, no unresolved residue, and individual attestation of every triggered external surface whose `blocks` includes the evaluated gate. Task 101 declares no separate deployed reading surface; repository Markdown freshness and clean-clone execution are the current reading-layer gates.

Each triggered external surface has its own `external_attestations` entry with stage, status, authority and evidence-reference policy. One global boolean cannot substitute for missing or pending surface records. Repository-local validation always leaves live-state verification false. Exact deployment/run identifiers remain in the mutable PR body and independent 1111 receipt.

`project_synchronization_complete` is the all-required-Current/Closed condition, not a blanket pre-merge acceptance gate. If any applicable registered surface still describes the superseded state, lacks a validated no-change decision, or has a pending attestation for the evaluated Current/Closed gate, the iteration cannot be called current or closed.

### 5.4 Front-Door Synchronization Is a Required Propagation Surface (not memory-dependent)

`README.md`, `HUMAN-READING.md`, `KNOWLEDGE/`, `RESULTS/` and `docs/project-current-state.md` are first-class project surfaces, not optional polish. Whenever an iteration changes project form, a Current capability, the Current method, governance, a core boundary, a primary entry, or the externally-comprehensible state, these front doors MUST enter the propagation closure as `CHANGE` (or a validator-enforced `NO_CHANGE_WITH_REASON` / `NonImpactProof`). They must not rely on Agent memory or human diligence.

Hard invariants:

- `IMPLEMENTATION_COMPLETE ≠ PROJECT_STATE_SYNCHRONIZED`
- `MAIN_MERGED ≠ HOMEPAGE_CURRENT`
- `ITERATION_CLOSED → REQUIRED_FRONT_DOOR_SURFACES_SYNCHRONIZED`
- if project form changed but `README.md` / `docs/project-current-state.md` still project the superseded state, the iteration MUST NOT be judged `CLOSED`.

The front-door staleness check is fail-closed: `tools/validate_human_front_door.py` enforces the current method version, the Charter System R1 boundary and homepage/project-current-state consistency; it rejects a stale homepage even when every other surface is green. A change that legitimately does not touch a front door must present an explicit `NonImpactProof` (see `data/operations/front-door-nonimpact-proofs.json`); silent omission is not allowed. A governance-chain closeout (for example Charter System R1) does not by itself make the homepage current — that is a separate required surface.

### 5.5 Knowledge Experience Delta

Any meaningful new or changed conclusion, correction, article, experiment, audit or knowledge asset must declare its human destination, typed What's New entry, subject-map node, asset-card state, applicable layered reading, canonical title and aliases, supersession/current replacement, source, dependencies and reverse dependencies. `tools/governance/build_knowledge_experience.py` produces the paired machine/human projection and manifest; `validate_knowledge_experience.py` fails closed on missing/stale sources, broken links or anchors, orphan cards, missing long-form layers, incomplete search coverage, rebound aliases, hidden content and retired Pages residues. These checks establish repository synchronization only, not substantive truth.

## 6. Branch And Commit Discipline

Use an isolated branch and Draft PR unless the task is an exact-head merge closeout.

Commits should be atomic and semantic. Four commits are useful for many macro tasks, but not a dogma. Do not amend, rebase, squash or force-push after external review unless the task explicitly allows it.

## 7. Minimum State-Changing Action

Prefer the smallest action that produces a real next-state change:

- new information;
- new capability;
- new evidence;
- new failure;
- real external commitment;
- clearer option space.

The loss must be affordable across money, AI quota, time, attention, sleep, maintenance load, reputation risk and future lock-in. Each action must include stop, pivot, scale and rollback conditions.

## 8. Anti-Sycophancy And Adversarial Review

Completion claims must be attacked before publication:

- search for the strongest alternative explanation;
- test blank, malformed and boundary inputs;
- separate author expectation from artifact review;
- separate external source, repository artifact, test/CI, real-world response, human judgment and independent review;
- bind positive words such as `complete`, `correct`, `accepted`, `verified` and `green` to object, criterion, version, evidence and boundary.

Summaries are not proof.

## 9. Validation Ladder

Run the narrowest relevant ladder first, then expand:

1. schema and JSON/JSONL parse checks;
2. semantic and reference validators;
3. focused regression tests;
4. integration tests;
5. frozen-boundary, governance, license, secret, cache and whitespace checks;
6. exact-final-HEAD remote CI, attested externally after the commit exists.

No failed lower rung can be repaired by a higher-rung narrative.

For Draft knowledge-surface work, build and inspect the exact-head machine and human artifacts, including the knowledge-experience manifest, full search coverage and rendered Markdown shards. After merge, rerun them from current `main` and a clean clone; a repository-local pass still does not prove external substantive claims.

## 10. State Machine

- `Candidate`: implemented in a branch or Draft PR.
- `Ready for GPT verification`: candidate has local and remote validation evidence but awaits independent acceptance.
- `Accepted`: independent review accepted the exact candidate HEAD.
- `Merged`: accepted exact HEAD entered `main`.
- `Current`: merged state has been verified on current `main` and front-door/current-state surfaces are synchronized.

Open Draft work stays `Candidate` or `Ready for GPT verification`; it is not current capability.

## 11. Merge, Rollback And History

Merge only the accepted exact HEAD. Prefer merge commits when preserving review history matters.

After merge:

- verify the accepted HEAD is an ancestor of `main`;
- record the merge commit;
- run or inspect required main CI;
- update current-state surfaces if the change affects identity, capability, usage or handoff;
- preserve historical evidence and prior method versions.

Rollback must identify whether to revert the merge commit, disable a workflow, remove a generated artifact, downgrade a status or open a repair PR.

## 12. Handoff And Receipt Contract

Every handoff or receipt records:

- repository and worktree;
- command file and command commit;
- branch, PR, base, starting HEAD and final HEAD;
- exact commits added;
- files changed;
- local validation commands and results;
- remote CI run IDs and conclusions;
- blockers, limitations and claim ceiling;
- forbidden actions that were not taken;
- receipt location.

Git commit SHA values and their post-commit CI run IDs are not self-embeddable: adding either to a tracked file creates a new commit, a new HEAD and new CI runs. The repository-local manifest and seal therefore encode only deterministic artifact consistency, lifecycle, impact decisions and an external-attestation policy.

Exact-final-HEAD CI remains mandatory. After the final commit is pushed and both required workflows finish, the mutable PR body and independent 1111 receipt record the exact HEAD, run IDs and conclusions. Independent acceptance and merge must re-fetch that live GitHub state. A repository-local validator PASS means only `repository_local_consistency_only`; it never substitutes for remote-truth verification.

Method 1.1.0 receipts also record state-transition subjects and dimensions, registry-derived required surfaces, every decision and evidence reference, implementation and repository synchronization status, external obligations and attestations, unresolved synchronization residue, and why the iteration is or is not ready/current/closed. Green CI alone never closes propagation.

## 13. Method Self-Iteration

This method may change only through itself.

A method-change iteration must record:

- current method version;
- evidence that the method itself has a gap;
- diff and compatibility impact;
- migration and rollback path;
- validation evidence;
- changed templates, schemas, validators and front-door references;
- confirmation that §5.4 front-door synchronization obligations are preserved (homepage and project-current-state remain required propagation surfaces and the fail-closed staleness validator still runs).

Do not silently rewrite prior method history. Keep old receipts and reports auditable.

Method 1.0.0 manifests and seals remain historical valid inputs. Method 1.1.0 adds a declared `completion_seal_path`, structured state transition, registry-derived synchronization closure and completion state. Compatibility must not allow a historical task-specific path to validate a different task's seal.

## 14. Method 1.2.0 Current: Typed Change Propagation

Method 1.2.0 was proposed by 121Q32 and became Current after independent exact-HEAD acceptance (R4), merge and closeout (Q32T). 1.1.0 is retained as historical. The candidate adds an executable component-level closure before the existing synchronization and lifecycle gates.

Its authority chain is:

`changed paths / explicit component seeds → project-components registry → typed propagation topology → synchronization registry → fixpoint → decisions → system-map projection and delta → manifest closure hash`

The topology separates `substantive_causal_candidate`, `repository_dependency` and `synchronization_obligation`. Substantive causal candidates are informational only and never propagate repository change automatically. Repository reachability, Git diffs and visual edges remain declared operational relations, not causal identification.

A 1.2.0 manifest binds the request and four generated products, seed paths and components, resolved components, typed relation IDs, component and surface decisions, registry-derived surfaces, system-map impact, residue and closure hash. The validator recomputes the closure and projection; stale or hand-edited products fail.

`NO_CHANGE_WITH_REASON` remains valid when an assessed component has no capability, lifecycle, navigation, relation or display impact. A new visible component must enter the layout; a deliberately hidden operation component must declare its visible representation and machine-checkable reason. The complete contract and limits are in `docs/architecture/typed-change-propagation.md`.

Backward compatibility is explicit: historical 1.0.0 manifests remain valid, 1.1.0 manifests retain synchronization closure semantics, and only 1.2.0 manifests require the new `propagation_closure` binding.

## 15. Method 1.3.0 Historical: Incremental Execution

Q32I added a repository-only execution layer on top of Historical 1.2.0. It converts a validated propagation plan into structured component decisions, complete NonImpactProof objects, profile-registered argv execution, identity-bound local cache decisions, unified validation, rollback and recovery materials. Authority classification is independent of local execution capability; apply is authorized only after the unified fail-closed preflight, and rollback success requires exact repository byte/type/symlink/mode restoration. The authoritative contract is `docs/architecture/incremental-execution.md`.

Selective materialization is permitted only when registry, topology, profile, producer, validator, plan, authoritative-input and generated-output identities all match. Cache is a performance layer, never a second truth source. An affected component cannot claim no impact. Meta-authority changes, unresolved paths and missing fingerprint policy fail closed or require `FULL_REBUILD_REQUIRED`.

Q32I self-hosting changes the registry, topology, profiles, planner, executor, validator and synchronization surfaces, so its own final change request correctly produces `FULL_REBUILD_REQUIRED`. This result is a safety decision, not an implementation failure. Method 1.3.0 is candidate=false, accepted=true, merged=true and current=true; Q32I is Closed. Method 1.2.0 is Historical.

The Phase D deterministic report, Phase E manifest, completion seal and exact-head CI/artifact evidence are auditable inputs. They did not self-accept Q32I or use the closeout HEAD as their own validity premise; independent review, merge, final-main CI, production deployment and live verification remained external lifecycle evidence. They do not identify real-world causality.

## 16. Method 1.4.0 Current: Continuous Stage Snapshot Publication

The candidate adds a publication axis orthogonal to the unchanged capability lifecycle. It lets a verified public summary, exact source identity, explicit status and evidence entrance appear in a Main homepage projection without treating the candidate payload as accepted, current, activated or merged to Main.

The publication states are `UNPUBLISHED`, `PR_VISIBLE`, `PUBLISHED_SNAPSHOT`, `SUPERSEDED_SNAPSHOT`, `WITHDRAWN_SNAPSHOT` and `HISTORICAL_SNAPSHOT`. Every record explicitly carries Accepted, Current, Activated, formal-capability impact and practical-application booleans. Main visibility never infers any of them.

The authority chain is:

`stage snapshot request → independent remote/evidence check → stage-snapshot registry → fail-closed validator → deterministic repository Markdown projection → exact-head CI and external receipt`

The lightweight gate validates the snapshot claim and publication boundary, not the underlying candidate capability. It rejects identity drift, missing evidence, duplicate IDs, removed limitations, capability registration, privacy/secret exposure, disguised rejection, stale projections, broken succession and responsibility transfer. Final responsibility is a positive, reference-based contract: accountable fields contain only an `actor_ref` resolved to an ACTIVE `PERSON`/`ORGANIZATION` in the controlled actor registry, whose entry supplies stable identity and accountability/contact evidence. Both public Schemas derive their allowed references from that registry and runtime resolves the same source; either-surface disagreement blocks. Execution agents and workflows are separate technical records and can never substitute for final responsibility. Responsibility changes require a new snapshot revision and superseding responsibility record. Revision, supersession and withdrawal preserve history.

The normative candidate contract is `docs/operations/stage-snapshot-publication.md`. This section, its schemas, tools, tests, templates and front-door projection are governed under iteration method 1.4.0 (now Current; 1.3.0 is Historical). They cannot use 1.4.0 to self-accept or self-merge; 1.4.0 became Current only after independent exact-head acceptance, ordinary merge, final-main validation and required production synchronization (controlled sync R1-20260726).

## 合并后真相传播要求（任务 106 引入）

自任务 106 起，任何后续任务在达到 Ready 之前，必须随交付物提供以下传播闭合证据；缺任一项，fail-closed 验证器会在普通 PR 的 CI 中判红：

1. 一条 **iteration-ledger 候选记录**（`data/operations/merged-iteration-ledger.jsonl`，追加式，含控制提交、PR 号、base、exact reviewed head、普通合并提交、终端态与证据字段）。
2. **精确远端证据绑定**：预注册祖先、原始结果保留、有界修复、修复后结果、exact-head 复核、所需 CI、干净克隆回执。
3. **九维 impact 计算结果**（机器推导，声明与推导一致），`NO_IMPACT_JUSTIFIED` 必须命名受治理源集合并证明哈希未变。
4. 所需的 **公开表面更新** 或 **已验证的无影响决策**。
5. **编辑文章 stale/review 闭合**：若材料源变化，文章须离开 CURRENT 直至附审稿证据。
6. **系统图 impact 闭合**：受治理源变化须触发重生成，未变化须留机器可验证的 NO_MAP_IMPACT 证明。
7. **current-truth 投影无矛盾**，且两次连续生成字节一致（确定性定点）。
8. **干净克隆可复现计划**。

普通合并之后，终端 ledger 状态与合并后证据须定稿，但不得改写已审稿件的语义 lineage。

## Task 110：完成状态 reconciliation 与独立元数据复制

任务 110 保留任务 109 的原始排序，新增基于 candidate/claim/run/task/lifecycle
身份的完成状态 reconciliation。`C-01`（task 103）与 `C-04`（task 105）从 active
queue 排除；完成的 partial/null/invalid 也必须留在历史中，只有明确 owner 授权的新
协议才能 reopen。

`C-03` 使用正式预注册的 117 条 DOI 人口和 OpenAlex Works API 完成首轮独立复制。结果
为 116 条主分母中的 101 supported、8 partial、7 null/inconclusive、0 contradicted、
0 invalid。这个结果只覆盖 registry/Crossref 与 OpenAlex 之间的书目元数据一致性，
不覆盖论文内容或任何 Pointfire/MCF/PSD/ARN 物理主张。原始响应与哈希保留在 task-110
run 目录，传播与终端化继续由事件溯源链闭合。
