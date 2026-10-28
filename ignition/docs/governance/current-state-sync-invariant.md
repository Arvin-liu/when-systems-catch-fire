# CURRENT_STATE_SYNC_INVARIANT

## Purpose

`CURRENT_STATE_SYNC_INVARIANT` makes the current architecture identity and its
current-state synchronization obligations machine-checkable. It closes the
failure mode in which an architecture iteration changes the canonical machine
projection while a Current State, home page, AI handoff or map still describes
an older identity.

The canonical contract is
`ignition/data/architecture/current-system-identity.json`. It is the only
machine identity contract for the current architecture. Its current facts are
derived from declared repository sources by JSON-pointer recipes; the contract
does not become a second manually maintained count registry. Historical
snapshots remain historical and may retain the facts that were true at their
own boundary.

## Impact handshake

Each iteration that touches identity, current-state prose, architecture
meaning, map identity or a declared handoff surface records one of:

- `NONE`: no synchronization obligation applies, with a reason.
- `PRESENTATION_ONLY`: explanation or navigation changes without changing the
  identity epoch, ownership, core relations, runtime model or current map
  identity. It must not claim full surface synchronization.
- `ARCHITECTURE_CHANGED`: the current architecture identity changed. The
  receipt must mark every applicable declared surface `CHANGE`, include
  evidence, synchronize the derived map and append the state delta in the same
  iteration.

The receipt is
`ignition/data/operations/iterations/<iteration>/current-state-sync-receipt.json`.
It carries the claim ceiling and synchronization decisions. Exact Git SHAs
are recorded in the operation ledger and release receipt, not copied into the
identity contract.

## Merge gate

From the `ignition/` directory, run:

```bash
python3 tools/validate_current_state_sync.py --check
```

The validator checks the schemas, source-path safety, current method and map
identity, derived metrics, open-obligation sources, receipt handshake and the
fixture manifest. For `ARCHITECTURE_CHANGED` it additionally checks Current
State stale counts, front-door identity duplication, map-version coherence
and the required bounded concepts on each declared surface.

This gate proves repository synchronization evidence only. It does not prove
external truth, Owner acceptance, production safety, live external invocation,
causality, general intelligence or `EPISTEMICALLY_ACCEPTED`.

## Current boundary

The current identity remains bounded: Ignition is the driver and
orchestration-governance layer; OpenClaw, Hermes and Codex are replaceable
external executors; Knowledge is the first large Domain Pack; and the local
execution layer is frozen as `REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR /
FALLBACK_MINIMAL`. `CURRENT_WITH_OPEN_OBLIGATIONS` remains distinct from
`EPISTEMICALLY_ACCEPTED=0`.
