# Isolated V1 G1 work order — Research Goal intake and lineage read-only adapter

Status: `DRAFT_PARALLEL_WORK_NOT_CURRENT`  
Created: 2026-10-10  
Owner objective: Build one usable V1 Goal-admission and completion-boundary preflight while Stage08 M/V/P/X runs independently.

## Why this can run in parallel

Stage08 active workspace/repository: `Arvin-liu/ignition-architecture-workbench`, stage-08 `overnight/research-os-stage08-20261010`, its frozen original execution instruction `Arvin-liu/1111@9ae38e6670cef6f802b2e68be3a26de3977a11ff`.

This work order touches **only a new public-repo Draft branch and new path prefix** `ignition/research_os_v1/g1_goal_intake/`, plus one or more **new** tests under `ignition/tests/test_research_os_v1_g1_*.py`. It does not request any revision to Stage08 or its result and does not presume Stage08 succeeds.

Public repo: `Arvin-liu/when-systems-catch-fire`. Start from this Draft branch's parent main SHA recorded by the PR. Work from a **separate git clone/worktree and a separate Codex session**, never from Stage08's active directory. A collision, ancestor mismatch or changed Current assertion blocks only this G1 stream.

## Frozen design anchors (read-only)

- The V1 G1 definition is a proposal (not Current): `Arvin-liu/ignition-architecture-workbench@ccdb169112de49adad46483931defb55ef820644`, `milestones/ignition-research-os-v1-definition-of-done-2026-10-10.md` and `milestones/ignition-research-os-v1-acceptance-plan-r0.json`, Draft PR #18.
- The public authoritative Steering contract is `ignition/docs/architecture/os-steering-intent-r1.md`.
- Existing implementation: `ignition/agent_runtime/steering.py` (`IntentRecord`, `GoalRecord`, `CompletionContract`, `GoalEpisodeBinder`, `GoalDriftGuard`, `evaluate_completion`).
- Existing regression examples: `ignition/tests/test_steering_episode_binding.py`, `ignition/tests/test_steering_completion.py`.
- Existing generated Current facts are read-only; do not treat their dated numbers as today's mutable authority without new source checks.
- This adds **no second Goal Registry**, no new canonical Steering identity and no new authority granted by user-submitted JSON.

## Product to build

A local, dependency-light, read-only **V1 Goal preflight adapter and report** that consumes user-authored synthetic/proposal input and points to existing runtime types, without registering the Goal or claiming the user has been authenticated as Owner.

Capabilities:

1. **Input:** one closed, versioned candidate `ResearchEpisodeRequest` envelope with research question, declared origin/provenance (untrusted input, never self-attestation), bounded deliverables, proposed success predicates, allowed source kinds, branch and review budget envelopes, allowed executor names, stop conditions, claim ceiling and parent/goal bindings. Preserve exact raw request digest. Never include secrets.
2. **Derivation (read only):** load/reference existing `IntentRecord` and `GoalRecord` snapshots provided as synthetic fixture bytes; reuse existing `GoalRecord.objective_digest()` semantics instead of inventing one. Require explicit stable Intent ID/version and Goal ID/version/contract ID bindings; any missing binding is `UNBOUND`, not silently generated as an authorized fact.
3. **Preflight checks:** reject malformed, unknown-field, missing, stale/superseded, wrong version, conflicting objective digest, detached parent, policy expansion, unchecked/invalid budget, executor outside allowlist, contradictory stop conditions, missing CompletionContract, forbidden `RUN_PASS -> GOAL_COMPLETE` inference. Fail-closed when read-only lookup can't establish trusted ownership/currentness.
4. **Outcome:** machine-readable `CANDIDATE_STRUCTURALLY_VALID_PROPOSAL_ONLY`, `REQUIRES_OWNER_AUTHORITY`, `BLOCKED_STALE_OR_UNBOUND` or `INVALID_INPUT`. These labels are *preflight observations*; only the existing canonical Owner/Goal lifecycle may authorize actual activation. The adapter must never produce `GOAL_ACTIVE`, `SATISFIED`, a real ApprovalReceipt or runnable task dispatch.
5. **Human brief:** a short report showing the exact goal/lineage bindings, evidence/claim limits, proposed budget, missing decisions, parent-goal attachment, source refs, and action `Owner review required` versus `fix malformed input`.
6. **CLI:** simple `python -m ... --input <local synthetic JSON> --report-dir <temporary output>` producing a JSON admission report and one concise Markdown summary; offline only; no network/provider, no credential reads, no Git/API write. Use explicit path allowlist and deterministic output bytes except clearly separated observation timestamps.
7. **Reproducibility:** example synthetic fixture(s), minimal `README`, captured exact command/input/output digest and a `dry-run only` semantic compatibility table to existing Current Steering types. Provide a later integration plan, not an actual runtime integration.

Avoid hard-coding a new policy authority, generating Owner authentication tokens, or treating a declaration `OWNER_DECLARED` inside candidate JSON as proven.

## Bounded execution plan

- A1: re-check parent repo head and V1 Draft source; inventory exact existing Steering input/output definitions and lock source anchors.
- A2: design minimal closed envelope and report schema with explicit inherited-vs-new fields; independent quick review of the authority boundary before running new input loaders.
- A3: implement pure read-only validator/projection and CLI, confined to newly created path prefix.
- A4: create >=20 deterministic synthetic/negative tests covering the cases above; no external network or privileged process. Reuse standard Python / already available declared dependencies; no installs/secret access.
- A5: run focused new test suite and the existing `test_steering_episode_binding.py` and `test_steering_completion.py` if feasible; unrelated full-repo failures become documented carry-forward, not reason to change other components.
- A6: independent code/evidence review by another worker/context; allow at most 2 causally distinct source fixes for any failure family. Keep original failures, don't alter acceptance oracle post hoc.
- A7: finalize the **same Draft PR** branch with diff proof, compact human report, exact tests and hashes. No merge/Ready or main write.

Use `BOUNDED_BACKLOG_UNBOUNDED_WALL_CLOCK`; may use up to two independent workers if helpful. Do not wait for Stage08 completion or consume Stage08's reviewers/worktree. When queue finishes or is genuinely blocked, stop; do not invent work to fill the night.

## Explicit non-interference and no-go

- Do not modify `Arvin-liu/ignition-architecture-workbench` or any Stage08 branch, worktree, `overnight/research-os-stage08/` artifact, review receipt, baseline code, or design decision.
- Do not edit `Arvin-liu/1111` main/receipt or Stage08 instructions. A separate read-only instruction pointer may live in 1111 on its own branch.
- Do not modify existing files `ignition/agent_runtime/steering.py`, existing Steering tests/fixtures/schemas, `ignition/data/operations/`, `ignition/docs/architecture/current-facts.md`, generated Current, Task229 R4, AB-19, PR #250, Task230 or any historical evidence.
- No dispatcher, external execution, authenticated provider, Internet retrieval, actual Owner identity, real trust signer, merge, Ready, public Current mutation or new scientific claim.
- No Codex GUI Computer Use or blocked sandbox-exec route, and no credential/keychain reads. Observe standard platform restrictions and quota stops.
- No second authoritative Intent/Goal source. Any proposed extension is a **noncanonical adapter** until a later post-Stage08 Owner/Chat review.

## Acceptance and exit

The bounded G1 adapter is **candidate**-complete only when:

- CLI actually runs on local synthetic fixtures;
- >=20 unique negative/positive tests actually run with source-independent expected values and correct specific outcomes;
- exact input objective and lineage discrepancies are reported without creating authoritative records;
- `RUN_PASS` does not produce Goal completion, and a forged Owner declaration is not accepted as authentic;
- owner review, unresolved source-trust and future integration remain visible;
- independent source and output review completed and Draft PR published.

Terminal: `V1_G1_READ_ONLY_ADAPTER_CANDIDATE_READY_FOR_OWNER_REVIEW`, `V1_G1_READ_ONLY_ADAPTER_PARTIAL`, or `V1_G1_READ_ONLY_ADAPTER_BLOCKED`.

**Never label G1 PASSED from this one candidate alone.** G1 pass requires subsequent independent end-to-end integration against real authorized episode contracts under the V1 acceptance plan. Preserve zero authority increase.
