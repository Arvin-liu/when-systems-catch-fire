# REPL-CASE-03 — Shadow-map fold

Synthetic source facts. All names, cells, ticks, and observations in this case
are invented for bounded experimental preparation. No external knowledge is
required.

## System record

The synthetic map has a primary cell `P`, a shadow cell `S`, an update marker,
and an immediate-read channel. A fold command changes the recorded value of a
cell. A reset returns both cells to their recorded starting values.

## Recorded observations

1. Before the fold, `P=6`, `S=6`, update marker `u0`, and immediate-read
   channel returned `6`.
2. Command `fold=2` was applied once at tick 7.
3. At tick 8, the primary cell was `P=8`, the shadow cell remained `S=6`, and
   the update marker was `u1`.
4. The immediate-read channel returned `6` at tick 8.
5. At tick 11, the immediate-read channel returned `8` while the recorded
   primary and shadow values remained `P=8` and `S=6`.
6. After reset, command `fold=2` was applied once at tick 7 and the same
   `P=8`, `S=6`, and `u1` state was recorded at tick 8.

## Record gaps

The record contains no direct read of the immediate-read channel's source cell
between ticks 8 and 11.
