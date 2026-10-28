# Q35-I1R Architecture Decision — Responsibility, Authority & Action Trace

- task_id: `121Q35-I1R` (build-first campaign, **checkpoint 2**)
- executor: Hy3 — BUILDER_ONLY (no independent review in this session)
- trusted_main_base: `81edff4039619b8343a82cb1b84785c8a9f6a990`
- immediate_parent_checkpoint: `06749dd118df7ade715b53f360e8177b09cdab49` (Q34, Draft PR #65)
- legacy LAB: `lab/121q35-agent-duty-night` (tip `1be68d94`), preserved via tag `legacy-lab-q35-agent-duty-night-12026-07-17`; selectively reimplemented, NOT merged/cherry-picked.
- status: Draft candidate (not reviewed, not merged, not Current)

## 1. Purpose

Build a minimal but complete **responsibility–authority–action-trace** closed loop so 点火 can distinguish: who proposes an action, who authorizes it, who executes it, who verifies it, who bears in-repo governance responsibility — and whether an action exceeds its committed conclusion, its authority scope, or its evidence boundary.

This is **not** a proof that real-world legal, moral, or organizational responsibility has been automatically adjudicated. Internal duty/authority records are repository governance artifacts, not legal judgments.

## 2. Repo-native forensics (what is reused)

| Existing capability (reused, not duplicated) | Where | Role in Q35 |
|---|---|---|
| Q34 claim / commitment decision / claim ceiling / independent review / exact-head binding | `schemas/discovery/*`, `tools/discovery/validate_commitment_gate.py` | Q35 actions must reference a Q34 `committed_current` claim (or a legitimate DEFER/REJECT basis) and never widen its claim ceiling |
| Q33 source rights & publication gate | `tools/governance/fail_closed_publication_gate.py`, `data/governance/*` | Q35 authorization never bypasses the Q33 rights/publication gate |
| Function OS execution roles & capability boundary | `function-os-candidate/`, execution profiles | Q35 actor roles map onto existing execution-capability kinds (manual/automatic/external) |
| iteration manifest / completion seal / external attestation | `tools/validate_iteration_sync.py`, `data/operations/iterations/` | Q35 registers as an iteration manifest + seal; lifecycle consistency enforced |
| generated-output authority / typed change propagation / system map | `tools/operations/*` | Q35 components + generated outputs registered; propagation closure derived |
| existing agent/review/handoff/receipt/audit structures | `docs/`, `agent-results` | Q35 reuses the actor-kind vocabulary (`human/model/agent/tool/process/deterministic_validator`) |

## 3. Q35 vs Q34 vs Q33 boundaries

- **Q34** decides: *may the project commit this claim as a conclusion?* (evidence, independence, ceiling, self-certification).
- **Q35** decides: *given a committed conclusion, who may initiate / authorize / execute / verify which action, within what authority?* (actor, grant, trajectory, responsibility).
- **Q33** decides: *even if committable and authorized, do we have the rights to (re)publish this material?*

Call order:

```
Q34 committed claim → Q35 action intent → authority/duty gate (Q35) → execution trajectory → outcome/verification/responsibility → Q36 intervention feedback
```

Q35 authorization is fail-closed and never substitutes for the Q33 rights/publication gate.

## 4. Why internal responsibility records ≠ real-world legal/moral judgment

The validator only decides whether an action is **repository-governance-conformant**: bound to a valid grant, scope, committed claim, and an immutable trajectory. It never outputs "legal responsibility determined" or "moral responsibility proven." Multi-actor situations that cannot be uniquely attributed are honestly reported as `UNRESOLVED_MANY_HANDS`, not forced into a single fake owner.

## 5. What is genuinely new in Q35 (the gap)

1. **Actor/role record** with authority source, scope, expiry, conflict-of-duty, revocation.
2. **Authority grant** (grantor/grantee, allowed actions, scope, required commitment state, review level, risk tier, preconditions, expiry/revocation, claim ceiling, delegation, separation-of-duty).
3. **Action intent / authorization decision / execution event / outcome / verification / rollback** as typed objects.
4. **Append-only hash-linked action trajectory** (previous-event hash + event digest + exact-head binding; correction via new events, never silent rewrite).
5. **Responsibility attribution** (initiator/authorization/execution/verification/governance-owner/unresolved-many-hands).
6. **Fail-closed validator/CLI** enforcing all of the above with stable exit codes.

## 6. How Q35 serves Q36

Q36 (observation/prediction/intervention/failure dynamics) consumes the Q35 **intervention request / outcome / rollback** interface: a Q36 intervention is a governed action with an authority grant, an execution trajectory, and a responsibility attribution. Q35 provides the stable typed contract + deterministic validator Q36 builds on.

## 7. Provenance

Inspired by (not certified by) the preserved legacy LAB `lab/121q35-agent-duty-night`. Duty/state-machine/permission/trace ideas were selectively reimplemented; thin schema, hardcoded SHAs, self-attesting tests, `requires_human_decision`-as-authority, and hash-chain-less traces were rejected. See `q35-legacy-lab-salvage-matrix.json`.
