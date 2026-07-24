# Adaptive Relational Runtime R2 — Architecture Decision Records

## ADR-R2-01 — B1–B6 bindings become the sole behavioral source

**Status:** accepted (preferred: behaviorally registry-driven)

**Context.** In R1, `projection-routes.json.anti_overstep_bindings` B1–B6 are loaded by
`ARRContract` but `_apply_anti_overstep()` in `runtime.py` enforces them through
hardcoded Python branches. The JSON declarations are decorative: removing a binding does
not change behavior. This is the documented R1 known limitation (registry-loaded
anti-overstep bindings unused inside the function body; overclaim enforcement runs via a
hardcoded gate path — dual truth).

**Decision.** Make `anti_overstep_bindings` the single behavioral source for overstep
protection.

- `runtime.py` gains a generic binding interpreter. For each binding `b` in the loaded
  registry, it evaluates `b.condition` (a closed predicate language over `relation` and
  `decision` fields) against the live call; on match it applies `b.effect`
  (`reject` → set `decision.target=REJECT` + `decision.reject_code=b.effect.reject_code`,
  or `downgrade_ceiling` → lower `claim_ceiling`).
- The hardcoded `_apply_anti_overstep` branch logic is **deleted** — no surviving dual
  truth.
- **Fail-closed:** if `anti_overstep_bindings` is missing or an empty list in the
  registry, `ARRContract`/`ARRRuntime` construction raises `ContractValidationError`
  (`registry-driven binding set is empty; overstep protection disabled → refuse to run`).
  This proves that *removing* B1–B6 fails closed rather than silently disabling
  protection.
- Each B1–B6 entry obtains an explicit machine-checkable `condition` and `effect`,
  replacing the free-text `value_template`.

**Consequences.**
- Mutation tests (commit 5) prove: editing `b.condition`/`b.effect` changes the
  corresponding behavior; deleting a binding either fails closed or removes the
  protection for that specific overstep (and a dedicated test asserts the changed
  outcome).
- No dead parameters remain. The registry is no longer illustrative data.

**Alternatives considered.** Remove the redundant registry and make the remaining
canonical contract explicit in code. Rejected: it would hide the contract in code and
make it un-auditable by non-code reviewers; the instruction prefers behaviorally
registry-driven, and it keeps the contract in the same reviewable artifact (JSON).

## ADR-R2-02 — Caller-owned inputs are immutable across `run()`

**Status:** accepted

**Context.** R1 `run()` reads caller-owned `source`/`observation` dicts; the known
limitation records that lifecycle state writes could reach the caller objects, and that
re-running the same input dict would re-enter lifecycle state.

**Decision.**
- `run()` deep-copies both inputs at entry; all schema validation, id computation, and
  lifecycle writes operate on the copies.
- The caller's `source`/`observation` are never assigned into.
- A commit-5 test performs a before/after **deep structural** comparison (not merely
  output equality) on the caller objects and asserts identity.

**Consequences.** Same object instance replayed ≥3×; input reordering does not change
deterministic identity; replay never fails because a prior call mutated the caller;
no duplicate lifecycle records.

## ADR-R2-03 — Explicit single-primary failure attribution

**Status:** accepted

**Context.** R1 had no per-object failure attribution. Mis-classification (missing
evidence → architecture failure; extraction error → mechanism failure) would corrupt
the pilot conclusions and could spuriously generate EVOLVE candidates.

**Decision.** A `FailureAttributor` maps each failed/partial run to exactly one primary
class from the nine-value `failure-classes` registry, plus ordered secondary factors.
Constraints enforced by tests:
- missing evidence → `SOURCE_FAILURE`/`REPRESENTATION_FAILURE`, never `ARCHITECTURE_FAILURE`;
- model/extraction error → `EXTRACTION_FAILURE`/`REPRESENTATION_FAILURE`, never
  `MECHANISM_FAILURE`;
- a single object failure never yields an `EVOLVE_CANDIDATE`; the growth gate returns
  `NO_EVOLVE` with a justification when the gate is incomplete.

## ADR-R2-04 — Privacy boundary: no private corpus content in the public repo

**Status:** accepted

**Context.** The 48 objects include private 1111 WAIC notes. The instruction forbids
copying full notes, bulk titles, audio transcripts, personal data, or copyrighted text
into the public formal repo.

**Decision.** Detailed inputs/outputs are written only to the 1111 evidence branch.
The public repo stores sanitized reference records (typed private references, digests,
short original paraphrases, aggregate counts). A `RIGHTS_AND_PRIVACY_AUDIT.md` and an
automated check assert zero `PRIVATE_CONTENT_PUBLICATION_EVENTS`.

## ADR-R2-05 — No second executor; adapters are read-only

**Status:** accepted

**Context.** R1 static gate enforces a single executor (no subprocess/network/write
paths). R2 adapters must read declared local files or already-fetched repo evidence only.

**Decision.** All six adapter families are read-only over declared references. None
performs a real-world action, network call, or external write. The static gate
(commit 6) re-verifies zero violations on the R2 code.
