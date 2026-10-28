# Discovery–Commitment Boundary & Verifiable Commitment Gate (Q34)

> Normative governance document for the Q34 discovery–commitment boundary.
> Status: Draft candidate (build-first campaign checkpoint 1). Not reviewed, not merged, not Current.

## What this is

A repository-native boundary that separates two different acts:

- **Discovery** — noticing or generating a *candidate* claim (an idea, observation, hypothesis, analogy, or in-repo fact).
- **Commitment** — deciding the project is allowed to treat that claim as a **current conclusion**.

Discovering is cheap and encouraged. Committing is gated. The boundary is enforced by a **deterministic, fail-closed validator** (`tools/discovery/validate_commitment_gate.py`) — never by model free text.

This document does **not** claim any project conclusion is true in the real world. There is no L7, no truth layer, and no automatic reality arbiter.

## The state machine

A claim moves through explicit states. It may never jump straight from discovery to commitment.

```
discovered → hypothesis → evidence_bound_candidate → validated_within_scope
            → commitment_candidate → committed_current
any non-committed state → deferred | rejected
committed_current → retracted | superseded
```

- `committed_current` is the **only** state that may appear on a Current/Accepted surface.
- `deferred` / `rejected` are **retained** (history + search path) but never surface on Current.
- `retracted` / `superseded` preserve the prior claim's history; nothing is silently overwritten.
- Every transition records: actor, decision, required evidence, allowed conclusion, failure state, and how history is kept.

## Commitment decisions

The gate yields one of:

- `COMMIT` — evidence independent/deterministic, exact-head bound, ceiling covers the text.
- `DEFER` — keep as candidate; do not surface.
- `REJECT` — discard as a conclusion (retain record).
- `DOWNGRADE_SCOPE` — reduce the claim to fit its evidence/ceiling.
- `REQUIRE_INDEPENDENT_REVIEW` — a reviewer independent of the discoverer must sign off.
- `RETRACT_OR_SUPERSEDE` — new evidence overturns a prior committed claim.

A claim may **not** be committed by the same model/agent that generated it (no self-approval). Deterministic proof/tests count as direct evidence, but their applicability still must be written into the claim ceiling.

## What the gate blocks (fail-closed)

- **Premature commitment** — model text with no evidence.
- **Circular self-certification** — a claim citing its own receipt as sole evidence.
- **Claim-ceiling breach** — e.g. "repository governance verified" inflated into "global legal compliance proven".
- **Analogy-as-mechanism** — a `STRUCTURAL_ANALOGY` rewritten as a causal mechanism.
- **Stale exact head** — evidence bound to an old/different HEAD.
- **Selective reporting** — keeping only successful candidates with no search/elimination record.
- **External-world without attestation** — real-world claims require a valid external attestation.
- **Lifecycle inconsistency** — committed state that disagrees with the iteration lifecycle.
- **History violation** — supersession/retraction that silently overwrites, or an uncommitted candidate leaking onto a Current surface.

## Relationship to Q33 (rights / publication gate)

Different questions, different gates, deliberate order:

```
discover candidate → bind evidence → validate scope → COMMITMENT GATE (Q34)
   → rights / publication gate (Q33) → L6 / Current surface
```

- **Q34** asks: *may this claim become a project conclusion at all?*
- **Q33** asks: *even if commitable, do we have the rights to (re)publish this material?*

A claim can pass one gate and fail the other. They are not merged.

## Pilot (proof, not just prose)

- **Allowed:** "The seven Q33 copyright governance components are Current in Main" — bound to manifest/seal/merge/components evidence, ceiling = repository governance state. → `COMMIT`.
- **Blocked:** "Q33 has proven global copyright compliance" — exceeds the repository-scoped ceiling. → `CLAIM_CEILING_BREACH`.

See `data/discovery/claims/` (committable pilot) and `data/discovery/fixtures/` (attack fixtures, each with an expected fail-closed exit code).

## Provenance

Inspired by (not certified by) the preserved legacy LAB prototype `lab/121q34-discovery-commitment-night`. Q33-superseded rights assets were not reintroduced; the dual-plane/promotion-demotion-residue ideas were reimplemented against current Main. See `docs/discovery/q34-legacy-lab-salvage-matrix.json`.
