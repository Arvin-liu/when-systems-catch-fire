# Repository Maintenance Pack

This is the smallest maintenance pack for bounded offline repository upkeep.
It can describe validation and declared maintenance proposals; it cannot
silently mutate Git remotes, permissions, Owner decisions, or truth claims.

The R2 night-shift fixture under
`data/agent-runtime/pilots/r2-offline-repository-maintenance/` is an observed,
disposable local episode: audit → approved repair → validation, with a
persisted crash checkpoint, executor-instance handoff, bounded operational
memory and independent adversarial failures. Its receipt explicitly records
`network_allowed=false`, `remote_mutation=false` and `git_push_invoked=false`.
