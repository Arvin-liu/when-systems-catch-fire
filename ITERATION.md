# 点火迭代操作法 / Ignition Iteration Method

Current method version: `1.1.0`

Current: `1.2.0` (typed declared change-propagation closure; 121Q32T closeout complete)

Historical: `1.1.0` (synchronization registry closure; superseded by 1.2.0)

Status: canonical operation method. This method governs how 点火 changes itself. It is not a truth layer, proof system, value charter, causal model or substitute for external evidence.

Current lifecycle: method 1.1.0 entered `main` through the independently accepted PR #57 and Q25D whole-project synchronization closeout.

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

Human-visible entrances are first-class project surfaces. Capability, identity, current-state, usage, handoff or deployment changes must assess `README.md`, the GitHub Pages source/workflow and rendered homepage, `docs/project-current-state.md`, `SUMMARY.md`, `docs/USAGE.md`, `docs/ai-assistant-usage-reference.md`, `CHANGELOG.md`, `docs/VERSIONING.md`, `AI-START-HERE.md`, `AI-HANDOFF.md`, `llms.txt` and relevant operation templates whenever the registry triggers them.

Derived and external surfaces remain distinct from repository sources. GitHub Pages is derived from `README.md` through `.github/workflows/pages.yml`, but its built artifact and production rendering require their own evidence. A local validator may require an external policy; it must always report that live external truth was not locally verified.

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
- `Current` and `Closed` require merged lifecycle, truthful post-merge repository closeout, no unresolved residue, and individual attestation of every triggered external surface whose `blocks` includes the evaluated gate. For Pages this means a main-sourced deployment and live rendered-homepage fetch.

Each triggered external surface has its own `external_attestations` entry with stage, status, authority and evidence-reference policy. One global boolean cannot substitute for missing or pending surface records. Repository-local validation always leaves live-state verification false. Exact deployment/run identifiers remain in the mutable PR body and independent 1111 receipt.

`project_synchronization_complete` is the all-required-Current/Closed condition, not a blanket pre-merge acceptance gate. If any applicable registered surface still describes the superseded state, lacks a validated no-change decision, or has a pending attestation for the evaluated Current/Closed gate, the iteration cannot be called current or closed.

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

For Draft Pages work, build and inspect the exact-head artifact without deploying the unmerged branch to the production homepage. Production Pages deployment and live fetch are post-merge external synchronization obligations.

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
- changed templates, schemas, validators and front-door references.

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
