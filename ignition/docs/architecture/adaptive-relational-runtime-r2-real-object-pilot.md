# Adaptive Relational Runtime R2 — Real Object Pilot

**Task class:** high-risk stacked Draft / real-object read-only pilot
**Predecessor:** PR #120 `architecture/adaptive-relational-runtime-r1-scaffold` @ `a0d6c46`
**Base branch:** `architecture/adaptive-relational-runtime-r1-scaffold` (NOT Main)
**R2 branch:** `runtime/adaptive-relational-runtime-r2-real-object-pilot`
**Commit plan:** exactly six ordinary commits (no amend / rebase / force).

## 0. Scope and non-goals

R2 does **not** expand the overall R1 architecture. It proves the R1 scaffold can
process a small, genuinely heterogeneous set of **48 real objects** without:

- state pollution of caller-owned input objects,
- hidden second-executor creation,
- false causal promotion (generic → cause),
- false consensus (same-source derivatives),
- unauthorized PROMOTE / EVOLVE,
- privacy or copyright leakage.

R2 is **not** a WAIC summary and **not** the full 836-note corpus run. R3 (836-corpus)
requires separate external review and an explicit, independent authorization.

**Non-goals (from instruction §14):** do not run all 836 WAIC notes, summarize WAIC as
the result, copy private/full corpus content into the public repo, add L7, modify
Foundation or Ψ₀, replace ARN/MCF/PSD/Function OS, create a second executor, perform
real-world actions, auto-PROMOTE/auto-EVOLVE, promote formal assets, modify PR #109–#120,
merge / mark Ready / modify Main, or claim production/Current status.

## 1. Two R1 runtime gaps closed (hard problems §5)

### 1.1 Registry declaration must equal runtime behavior  →  ADR-R2-01

**R1 known limitation:** `anti_overstep_bindings` B1–B6 are loaded by
`ARRContract` but `_apply_anti_overstep()` in `runtime.py` enforces them through
hardcoded Python branches (`if decision.get("rule_id") == "R12" ...`) that are *not*
derived from the JSON declarations. Removing a JSON binding from
`projection-routes.json` does **not** change behavior; the registry is decorative.

**R2 decision (Preferred outcome — behaviorally registry-driven):**
Make `projection-routes.json.anti_overstep_bindings` the **sole behavioral source**.
`_apply_anti_overstep` is replaced by a generic interpreter that, for each binding in
the loaded registry, evaluates the binding's `condition` against the live `relation` +
`decision` and applies the binding's `effect` (reject with `effect.reject_code`, or
downgrade `claim_ceiling`). The interpreter is **fail-closed**:

- If `anti_overstep_bindings` is missing or empty in the registry → the engine raises
  `ContractValidationError` at construction (`registry-driven binding set is empty;
  overstep protection disabled → refuse to run`). This proves removal of B1–B6 fails
  closed, not silently.
- Each binding carries an explicit, machine-checkable `condition` (a small closed
  predicate language over `relation`/`decision` fields) and an `effect`. Mutating a
  binding's `condition`/`effect` changes the corresponding behavior; the R2 mutation
  suite proves this for every B1–B6.

No dead parameters, no hardcoded dual truth. The hardcoded `_apply_anti_overstep`
branch logic is deleted.

### 1.2 Caller-owned inputs must remain immutable  →  ADR-R2-02

**R1 known limitation:** `run()` reads caller-owned `source`/`observation` and the
known-limitation note records that lifecycle state writes could reach the caller dict.

**R2 decision:** `run()` performs a **deep structural copy** of both caller inputs at
entry and never assigns into the caller-provided objects. Every deterministic id,
validation, and lifecycle operation operates on the copies. The caller's `source` and
`observation` are byte/structure-identical before and after `run()` (proved by a
before/after `deepdiff`-style structural check, not only output equality).

Guarantees (proved by commit-5 tests):
- same input object instance can be replayed ≥3× with identical semantic results;
- identical inputs in different orders yield identical deterministic identities;
- a replay cannot fail merely because a prior call mutated the caller object;
- no duplicate lifecycle records created by replay.

### 1.3 Failure attribution must be explicit  →  ADR-R2-03

Every failed or partial pilot run lands in **exactly one primary failure class**
plus optional secondary factors. The nine classes (from the failure-classes registry)
are the only legal values: `SOURCE_FAILURE`, `EXTRACTION_FAILURE`,
`REPRESENTATION_FAILURE`, `ROUTING_FAILURE`, `MECHANISM_FAILURE`, `RUNTIME_FAILURE`,
`ARCHITECTURE_FAILURE`, `GOVERNANCE_REFUSAL`, `UNKNOWN`.

The runtime must not classify missing evidence as `ARCHITECTURE_FAILURE`, or a
model/extraction error as `MECHANISM_FAILURE`. One object failure must not produce an
EVOLVE candidate — the growth gate returns `SIGNAL_ONLY` / `NO_EVOLVE`, never
`EVOLVE_CANDIDATE` for a single-object failure.

## 2. Real-object sampling contract (§6)

Exactly **48** objects are selected **before** the first pilot execution and locked in
`REAL_OBJECT_SELECTION_MANIFEST.json` (immutable; replacements require a new run ID).
Distribution:

| # | Class | Source |
|---|-------|--------|
| 12 | real text / transcript sources | private 1111 WAIC corpus (no full private text in public repo) |
| 8 | Git / PR / CI chains | point-fire repos, exact ref identity |
| 8 | structured-data objects | registries / manifests / topology / map / schema-conformant project data |
| 8 | production-runtime receipts | RUN/PROMOTE/EVOLVE receipts or committed generation evidence (read-only) |
| 6 | temporal event sequences | declared repo/project histories (event/observation/ingestion times kept separate) |
| 6 | mechanism / system-state objects | Function OS capability records, mechanism contracts, execution profiles, snapshots |

Each manifest entry records: object ID, object class, private/public location,
content/ref digest, rights tier, source tier, event/publication/observation/ingestion
times, permitted formal representation, excluded content, expected routing target,
claim ceiling.

## 3. Privacy and publication boundary (§7)

Detailed private inputs/outputs belong in `Arvin-liu/1111` (evidence branch
`agent/adaptive-relational-runtime-r2-real-object-pilot-20260725`). The public formal
repo may contain only: strict schemas/validators, deterministic runner/adapters,
sanitized object reference records, hashes / typed remote references, original short
paraphrases written for testing, and aggregate counts that do not reconstruct private
text. Never copy full WAIC notes, bulk titles, audio transcripts, personal data, or
copyrighted articles into the public repo.

## 4. Required public capabilities (§8)

Immutable input handling; registry-driven B1–B6 behavior; 48-object selection-manifest
validation; read-only adapters (text-ref / Git-PR-CI / structured-data / receipts /
temporal / mechanism-state); deterministic pilot run IDs; per-object execution
receipts; failure attribution; replay/idempotency verification; capability coverage and
residue aggregation; explicit `NO_EVOLVE` when the gate is incomplete.

No second executor. Adapters read declared local files or already-fetched repo evidence
only; they perform no real-world actions.

## 5. Required outputs (§9)

Public: this doc, R2 pilot schema(s), adapter-capability registry updates, failure
attribution contract, deterministic pilot runner + validators, tests, CI.

Private (1111 evidence): `REAL_OBJECT_SELECTION_MANIFEST.json`,
`REAL_OBJECT_RUN_LEDGER.json`, `OBJECT_RECEIPTS/` (48), `CAPABILITY_COVERAGE_MATRIX.json`,
`FAILURE_ATTRIBUTION_LEDGER.json`, `REPRESENTATION_RESIDUE.json`, `ROUTING_RESIDUE.json`,
`REPLAY_IDEMPOTENCY_REPORT.json`, `FALSE_CONSENSUS_CASES.json`, `ENGINEERING_SIGNALS.json`,
`NO_EVOLVE_JUSTIFICATIONS.json`, `RIGHTS_AND_PRIVACY_AUDIT.md`, `REMOTE_IDENTITY_RECEIPT.json`,
`SUBAGENT_LEDGER.json`, `FINAL_EXTERNAL_REVIEW_REQUEST.md`.

## 6. Acceptance matrix (≥72 checks, §10)

Covers: B1–B6 each mutation proof; dead registry entries rejected; all caller inputs
byte/structure-identical before/after; same object replayed ≥3×; reordered equivalent
inputs → identical deterministic ids; no duplicate lifecycle records; every selected
object validates + produces one receipt + has explicit route or explicit rejection; no
silent disappearance; no private leak; repetition ≠ independent evidence; same-source
derivatives ≠ false consensus; event time ≠ note/download time; speaker claim ≠ verified
fact; interpreter reconstruction ≠ speaker belief; generic ≠ cause; decorative
probability rejected; Function OS adapter cannot call undeclared capabilities; ARR cannot
invoke PROMOTE/EVOLVE; real-world action count = 0; one failure ≠ EVOLVE candidate;
incomplete growth gate → engineering signal or `NO_EVOLVE`; R1 78 tests remain green;
production runtime tests green; ARR static gate zero violations; project-components /
topology / profiles / map / front-door zero new residue; `unmapped_path=[]` and
`ambiguous_path_mapping=[]`; PR #120 and frozen ancestors unchanged; Main unchanged.

## 7. Required counters (§13)

`FORMAL_NEW_BRANCHES=1`, `FORMAL_NEW_PRS=1`, `FORMAL_DRAFT_PRS=1`, `FORMAL_READY_PRS=0`,
`FORMAL_MERGES=0`, `MAIN_CHANGES=0`, `PREDECESSOR_PR_CHANGES=0`, `REAL_OBJECTS_SELECTED=48`,
`REAL_OBJECTS_RUN=48`, `WAIC_FULL_CORPUS_RUNS=0`, `FORMAL_ASSETS_PROMOTED=0`,
`AUTO_EVOLVE_STARTED=0`, `REAL_WORLD_ACTIONS=0`, `FORCE_PUSHES=0`, `HISTORY_REWRITES=0`,
`PRIVATE_CONTENT_PUBLICATION_EVENTS=0`, `EXTERNAL_ACCEPTANCE_CLAIMED=0`.

## 8. Final stopping condition (§15)

Continue autonomously through predecessor verification → architecture → build → private
pilot preparation → 48-object run → independent review → six-commit fixes → publication
→ live refetch. Stop only at
`ARR_R2_REAL_OBJECT_PILOT_DRAFT_AWAITING_EXTERNAL_REVIEW` or one precise blocker
(`ARR_R2_PREDECESSOR_GATE_BLOCKED`, `ARR_R2_REGISTRY_BEHAVIOR_BLOCKED`,
`ARR_R2_INPUT_IMMUTABILITY_BLOCKED`, `ARR_R2_PRIVACY_BOUNDARY_BLOCKED`,
`ARR_R2_REAL_OBJECT_REPLAY_BLOCKED`, `ARR_R2_PROPAGATION_SYNC_BLOCKED`,
`ARR_R2_REMOTE_PUBLICATION_BLOCKED`).

Do not claim merge readiness, deployment readiness, Current capability, or
`EXTERNAL_ACCEPTED`.
