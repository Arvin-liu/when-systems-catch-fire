# 121Q36-INT repair-r1 architecture decision

Status: `LOCAL BUILDER REPAIR CANDIDATE / NOT REVIEWED / NOT CURRENT`

## Locked scope and parent

This repair addresses blocker `B05` without changing original PR #68, its branch, frozen head `02a87221b86cf39217f8c6b3c63e0737a0e2de98`, receipt or history. The branch began at that exact head and incorporated direct predecessor Q36-OBS repair-r1 through ordinary two-parent merge commit `0c43b8c866851123486c4c9648f998275676bf98`.

Only Q36-INT intervention/failure contracts, canonical predecessor and evidence bindings, validator, pilot, attacks, tests and necessary propagation surfaces may change. Every operation remains repository-local and request-only; no real-world action is executed.

## Original blocker reproduction

The unmodified real CLI accepts `data/intervention/fixtures/24-placeholder-digests-self-declared-authority.json` with `GATE_PASS` / exit `0`. The bundle uses repeated `1` through `5` placeholder SHA-256 values, embeds its own grant, supplies no content-bound Q36-OBS record and does not resolve its action, actor or evidence from canonical repository bytes.

## Minimal repair contract

1. Resolve the Q34 claim, Q35 actor/grant/action trajectory and Q36-OBS observation from canonical predecessor artifacts.
2. Require repository-contained paths, existing exact commit/blob Git objects and recomputed SHA-256 over actual bytes.
3. Reject null, empty, zero, repeated-character and placeholder digests before semantic evaluation.
4. Bind pre-state, output, failure and rollback evidence to actual repository bytes; embedded grants or self-reported authority never confer permission.
5. Preserve request-only high-risk behavior and enforce stop/rollback state from parseable records, without executing any intervention.
