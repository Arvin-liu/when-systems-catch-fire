# REPL-CASE-01 — Mirror-latch relay

Synthetic source facts. All names, tokens, counters, and observations in this
case are invented for bounded experimental preparation. No external knowledge
is required.

## System record

The synthetic relay has two lanes, `L` and `R`, a selector marker, and a
single-token input slot. A tick is one step in the local record. The relay was
reset before the observations below.

## Recorded observations

1. At tick 10, lane `L` counter was `4`.
2. The lane `R` counter at the corresponding pre-input tick was not recorded.
3. At tick 11, selector marker was `amber` and input slot was empty.
4. At tick 12, token `K7` was placed in the input slot once.
5. At tick 13, lane `L` counter was `5`, lane `R` counter was `8`, and the
   selector marker was still `amber`.
6. At tick 18, lane `L` counter was `5` and lane `R` counter was `8`.
7. The record contains no independent read of the selector's internal route
   decision at ticks 12–13.

## Record gaps

The pre-input `R` counter and the internal route-decision read are absent. No
value is supplied for either gap.
