# REPL-CASE-02 — Windowed acknowledgement spool

Synthetic source facts. All names, batches, ticks, and observations in this
case are invented for bounded experimental preparation. No external knowledge
is required.

## System record

The synthetic spool has a payload queue, a delivery counter, an acknowledgement
register, and a four-tick watchdog. A reset clears the queue and register. The
same scripted batch can be placed into the queue after a reset.

## Recorded observations

1. Before run one, the queue contained batch `B3` with three payload items and
   the acknowledgement register was `empty`.
2. Run one recorded three payload deliveries by tick 2.
3. Run one recorded acknowledgement `green` at tick 3.
4. The system was reset; the same batch `B3` was placed into the empty queue.
5. Run two recorded three payload deliveries by tick 2.
6. Run two recorded acknowledgement register `empty` at tick 4.
7. The watchdog state changed to `expired` at tick 4, and no later
   acknowledgement event was recorded for run two.

## Record gaps

The record does not identify whether the missing acknowledgement was blocked
before register write or after register write. No additional event is inferred.
