# CASE-01 — Aster Table

All names, values, devices, and observations in this case are synthetic.

## Recorded facts

- The fixture has two independent lanes, A and B, with separate reset controls.
- Before the recorded run, both lane counters were `4`.
- The same input token `T-4` was sent once to each lane during the same fixture cycle.
- Lane A ended at counter `5` with marker `amber`.
- Lane B ended at counter `8` with marker `blue`.
- The input token, starting counter, cycle identifier, ending counter, and marker are all present in the fixture log.
- The fixture log contains no explanation for the difference between the two lane records.

## Candidate actions listed in the fixture workspace

- Candidate A: reset both lanes to the recorded start counter, repeat the same token on each, and record the paired start/end counters and markers.
- Candidate B: read each lane's selector register before another token is sent.

The workspace lists both actions. It does not record a selection, an execution, or a result for either candidate action.

## Unrecorded items

- Whether either selector register changed during the recorded cycle.
- Whether the paired difference persists in another fixture cycle.
- Any causal explanation for the recorded values.
