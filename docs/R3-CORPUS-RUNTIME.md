# R3 Corpus-Scale Runtime — Architecture & Run Contract

**Scope:** `tools/adaptive_relational_runtime/corpus/` — a generic layer over ARR R2
for corpus-scale pressure testing (IGNITION R3 WAIC CORPUS SCALE RUN R1).

**Status:** Measurement-only (baseline-before-repair). No PROMOTE, no EVOLVE, no
real-world action, no architectural/semantic repair during the run (IGNITION §13).

---

## 1. Why a layer, not a second ARR

The runtime reuses existing ARR R2 surfaces:

- `tools.adaptive_relational_runtime.canonical` — deterministic identity, NFC
  normalization, `sha256_hex`, `deterministic_id`, `canonical_json`.
- `tools.adaptive_relational_runtime.adapter_protocol` — registry-driven dispatch
  (typed reference only).
- `tools.adaptive_relational_runtime.production_receipt_adapter` — read-only
  receipt transcription (never writes, never calls a write path).

It does **not** introduce a second executor. Every receipt carries
`real_world_action=False`, `promote=False`, `evolve=False`.

## 2. Pipeline

```
corpus root
   │
   ├─ Stage A (deterministic mechanical pass) ──→ identity, frontmatter audit,
   │                                              note_id audit, encoding/parse
   │                                              errors, immutable manifest
   │
   ├─ Shard plan (deterministic by identity hash, plan digest)
   │
   ├─ Stage B (bounded semantic ARR pass, per shard, checkpointed)
   │     └─ corpus envelope + final receipt; epistemic ceilings enforced
   │
   ├─ Analysis (dedup, temporal, source-independence, false-consensus)
   │
   └─ Aggregate metrics (counts/rates ONLY) ──→ published to public repo
                                                per-note detail ──→ private evidence
```

## 3. Determinism contract

- Object identity = `note_id` (or path digest when absent) + `byte_sha256` +
  `normalized_text_digest`.
- `run_id` is deterministic from `(corpus_ref, object_count, plan_digest)` — never
  the wall clock.
- Shard membership is derived from the frozen identity; reordering inputs yields
  the identical plan digest.
- Every committed artifact is content-addressed; replay of a completed run
  reproduces identical authoritative records (idempotent, exact-once).

## 4. Epistemic ceilings (IGNITION §7–§8)

- `INDEPENDENTLY_VERIFIED` is **forbidden** unless the corpus itself carries
  explicit independent primary evidence with an explicit linkage. No online
  verification is authorized.
- A speaker/company claim is recorded as `SPEAKER_CLAIM` / `COMPANY_SELF_REPORT`,
  never elevated to `INDEPENDENTLY_VERIFIED`.
- Every inferred premise is labeled as `inference`, never as the speaker's known
  belief; generic relations never self-upgrade to cause.
- Time: `event_time` is never inferred from folder name, never replaced by note
  `created_at`. Conflicting or missing signals stay `UNKNOWN` and lower the claim
  ceiling.

## 5. Outcome taxonomy (IGNITION §11)

`SUCCESS` / `EXPECTED_UNKNOWN` / `EXPECTED_QUARANTINE` / `FAILURE` /
`RETRY_EXHAUSTED`. A receipt existing does **not** mean successful semantic
processing — only that the object was accounted for.

## 6. Crash safety & recovery (IGNITION §10)

- Checkpoint after each committed object (or a documented atomic batch equivalent).
- Post-crash state contains only committed old/new outcomes — never partial
  authoritative objects.
- Restart from any checkpoint; bounded retry with explicit terminal quarantine.
- Mandatory demos: clean full run; ≥10% interrupt + resume; ~50% interrupt +
  resume; final-shard interrupt + resume; idempotent replay (no duplicate);
  changed-note selective rerun (isolated fixture, never modifies the frozen source).

## 7. Public / private boundary (IGNITION §12)

| Public formal repo                         | Private 1111 evidence branch            |
|--------------------------------------------|-----------------------------------------|
| generic schemas                            | per-note receipts (836)                 |
| generic runtime code                       | manifest / inventory / ledgers          |
| synthetic fixtures                         | duplicate / source / temporal artifacts |
| validators & tests                         | crash / replay / incremental reports    |
| non-reconstructive aggregate metrics       | rights & privacy audit                  |
| hashes + typed private references          | subagent ledger / review request        |

The public repo contains **no** full note, long excerpt, audio transcript, bulk
title, PII, or anything sufficient to reconstruct private content.

## 8. Commit plan (IGNITION §16)

1. architecture / run contract / schemas
2. deterministic inventory / manifest / shard planner
3. checkpoint / resume / crash safety / run state
4. semantic ARR batch adapter / receipts / private-reference export
5. synthetic tests / 120+ acceptance matrix / scale-run hooks
6. propagation / docs / system-map / current-state / CI sync / final aggregates

## 9. Stop state

`ARR_R3_WAIC_CORPUS_SCALE_RUN_DRAFT_AWAITING_EXTERNAL_REVIEW`. No R4, PROMOTE,
EVOLVE, Ready, merge, Main change, or force push.

## 10. Non-private aggregate (public, IGNITION §12 / §16(6))

The public repo carries only non-reconstructive aggregates. The authoritative
artifact is `data/r3-corpus-scale/public-aggregate.json`; it records public-facing
counts and guarantees and never contains full notes, bulk titles, audio
transcripts, or anything sufficient to reconstruct private content. The 836-note
scale-run per-note receipts, manifests, ledgers and analyses live only in the
private 1111 evidence branch.

Public guarantees (verified by the 42-test acceptance matrix and the ARR static
gate):

- `public_private_content_leaks = 0`
- `promote_calls = 0`, `evolve_calls = 0`, `real_world_actions = 0`
- `silent_disappearances = 0` (synthetic fixture: 29 notes + 1 index)
- deterministic `run_id` (no wall-clock dependence); completed-run replay is
  idempotent (exact-once, no duplicate receipts)
- crash-safe resume across ≥10% / ~50% / final-shard interrupts
- changed-note selective rerun touches only the changed object (isolated copy)

The frozen-scale count `836` is the IGNITION spec constant and is published only
as a count; no private note, digest set, or title list is exposed in the public
repo.
