# IGNITION-138 Step 13 — Targeted regression and preflight

## Result

`PASS`: the exact Task138 targeted suite completed naturally with **333 tests,
0 failures, 0 errors, and 0 skips** in `128.180s`.

The suite covered the live bridge and runtime-scratch boundary, Codex and
federation dispatch, residual and Current-state gates, release/lifecycle
bindings, human-surface and privacy gates, repository path accounting, and
Foundation generator reconciliation. No new real Codex child invocation was
started in this step. The task still has exactly one real Codex attempt and no
structured result.

## Deterministic repair trail

The first post-Step12 run exposed four genuine stale-projection/accounting
failures. Step12 prose had changed generator inputs, so the canonical
nonfunction claim outputs, material human source fingerprints, and repository
path manifest were stale or incomplete. The canonical nonfunction adjudicator,
human claim browser builder, and repository path classification generator were
run to fixed point.

The following run then exposed three Current Facts failures. The regenerated
nonfunction registry changed the declared Current Facts inputs. Current Facts,
Current Snapshot, and all seven compiler-owned Current Snapshot blocks were
regenerated. The final natural run passed all 333 tests.

## Preflight evidence

- Current volatile registry: `PASS facts=19 surfaces=7`.
- Dispatch reconciliation: `PASS`; durable dispatch, receipt-before-validation,
  ACK-loss side-effect handling, and validated-terminal checks passed.
- Residual ledger: `PASS entries=6 inherited_unchanged=3 resolved=3`.
- Residual adversarial matrix: `PASS cases=18 passed=18`.
- Durability projection hygiene: `PASS`; no Foundation/Knowledge, human-machine,
  or fire-seed backflow was found.
- Repository path classification: `PASS tracked=3225 manifest=3225 checks=10/10`.
- Current State Sync and semantic gates: `PASS`; identity epoch remains
  `os-control-plane-r5-live-executor-federation-r2`, with `PRESENTATION_ONLY`
  impact.
- Execution contract and Current task lineage: `PASS` for Task138.
- Lifecycle: `PASS content_phase=RUNNING`, publication authority remains
  `REMOTE_REF_OBSERVATION`, and no embedded publication assertion exists.
- Owner-observation privacy: `PASS public_safe=true private_content=false`.
- Human front door and contract: `PASS`; 25 human surfaces, 14 machine-human
  pairs, 20 two-click destinations, 48 human entries, 95 components, 83 visible
  graph nodes, and 88 typed graph edges.
- Current Facts, Current Snapshot, and the ten-output in-memory projection
  determinism gate: `PASS`.
- `git diff --check`: `PASS`.

## Boundary and claim ceiling

The task workspace remains `DISPOSABLE_READ_ONLY`; only isolated,
attempt-ephemeral executor runtime scratch is writable; auth/config remains a
read-only reference. The prior fixture workspace digest remained
`40ab9b327e6bf1044e3f57e00aaf483fe6d7f2f77a3bcddc4c414d1825556fba`; no secret,
config, or billing mutation was observed.

The first Codex startup failure remains classified as a known no-effect
pre-inference failure. Because no structured result exists and the auth-source
boundary forbids a second real invocation, `LIVE_EXTERNAL_INVOCATION` remains
open at `LIVE_BRIDGE_IMPLEMENTED / LIVE_COMPLETION_NOT_OBSERVED`.

This receipt proves targeted repository-local regression and deterministic
preflight only. It does not infer validated live completion, external truth,
production readiness, Owner acceptance, publication, or epistemic acceptance.

Next: Step 14 exact-candidate natural offline full regression.
