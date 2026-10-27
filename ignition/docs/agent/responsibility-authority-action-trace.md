# Responsibility, Authority & Action Trace (Q35)

> Normative governance document for the Q35 responsibility–authority–action-trace closed loop.
> Status: Draft candidate (build-first campaign checkpoint 2). Not reviewed, not merged, not Current.

## What this is

A repository-native, auditable, fail-closed contract that lets 点火 distinguish: **who proposes** an action, **who authorizes** it, **who executes** it, **who verifies** it, and **who bears in-repo governance responsibility** — and whether an action exceeds its committed conclusion, its authority scope, or its evidence boundary.

This is **not** a determination of real-world legal, moral, or organizational responsibility. Internal duty/authority records are repository governance artifacts, not legal judgments.

## Objects

- **Actor / role** — stable id, type (human/model/agent/tool/organization/deterministic_verifier), declared role, **resolvable authority source** (never a bare model name), scope, expiry, conflict-of-duty, revocation.
- **Authority grant** — grantor/grantee, allowed action types, resource scope, required commitment state, required review level, risk tier, preconditions, expiry/revocation, claim ceiling, delegation, separation-of-duty. **Fail closed by default.**
- **Action** — intent → authorization decision → execution → observed outcome → verification → rollback, each bound to initiator/authorizer/executor/verifier, a grant, a Q34 committed claim, exact command, digests, exact head and claim ceiling.
- **Append-only trajectory** — stable ordered, hash-linked (prev_digest + event_digest), exact-head/artifact bound; correction via new events, never silent rewrite.
- **Responsibility attribution** — initiator / authorization / execution / verification / governance-owner / unresolved-many-hands.

## What the gate blocks (fail-closed)

- self-awarded authority (grantor == grantee)
- bare model name as authority source
- expired / revoked / suspended grant
- action outside grant scope
- broken or forbidden delegation
- relying on a non-committed (hypothesis) claim
- action exceeding the claim ceiling
- separation-of-duty violation (self propose/authorize/execute/verify where independence required, or reused parties on high/critical risk)
- stale exact head
- broken hash chain / reorder / delete / backfill / tamper
- silent rollback that erases failure history
- Q35 authorizing publication of Q33-rejected material
- forcing an unresolved many-hands into a single fake owner

## Relationship to Q34 / Q33 / Q36

```
Q34 committed claim → Q35 action intent → authority/duty gate (Q35) → execution trajectory → outcome/verification/responsibility → Q36 intervention feedback
```

- **Q34**: may the project commit this conclusion?
- **Q35**: given a committed conclusion, who may act on it, within what authority?
- **Q33**: even if committable and authorized, do we have rights to (re)publish?
- **Q36**: consumes Q35 intervention/outcome/rollback as governed actions.

## Pilot

A controlled repository operation on the Q34 Draft PR with separated roles (initiator / human authorizer / executor / deterministic verifier) validates `GATE_PASS / AUTHORIZE` — without claiming the Q34 candidate is Main-accepted. See `data/agent/pilot-q34-pr-controlled-op.json`.

## Provenance

Inspired by (not certified by) the preserved legacy LAB `lab/121q35-agent-duty-night` (tag `legacy-lab-q35-agent-duty-night-12026-07-17`). Thin schema, hardcoded SHAs, self-attesting tests, `requires_human_decision`-as-authority and hash-chain-less traces were rejected. See `q35-legacy-lab-salvage-matrix.json`.
