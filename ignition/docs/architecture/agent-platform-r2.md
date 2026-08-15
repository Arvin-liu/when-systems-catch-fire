# Agent Platform R2 — Pack Registry and Bus R1

This architecture surface records the repository-scoped Agent Platform R2
spine. The Generic Kernel owns identity, state, capability contracts and
non-escalation. The Runtime owns declarative Pack discovery, validation,
loading, capability routing and typed proposals. A Pack manifest describes a
domain boundary; loading it does not import domain modules or execute hooks.

## Pack boundary

The current registered Packs are Knowledge, REOS LIGHT Research, 之元 Writing,
and bounded Repository Maintenance. Each declares its version, compatibility,
capabilities, object types, validator/action/planning hooks, human/machine
entries, requested permissions, load/unload policy, optional dependencies and
declarative health check.

Pack Bus routing returns a `ROUTED_PROPOSAL` with a deterministic payload digest.
It does not perform the action, grant permissions, select an executor, accept
an Owner decision, or establish truth. Runtime and Kernel boundaries remain
provider/model-neutral and offline in this R1 implementation.

## What this establishes

- Pack manifests are discoverable and validated from `packs/*/manifest.json`.
- Pack metadata can be loaded and unloaded with an active-run boundary.
- Declared capabilities have one deterministic route and unknown capabilities
  fail closed.
- Pack validators and hooks remain strings in a declaration; no import side
  effect is used as a loading mechanism.

## What this does not establish

This is not production plugin isolation, a live provider API, a daemon, a
network permission grant, a truth registry, or Owner acceptance. It does not
upgrade `EPISTEMICALLY_ACCEPTED=0`.
