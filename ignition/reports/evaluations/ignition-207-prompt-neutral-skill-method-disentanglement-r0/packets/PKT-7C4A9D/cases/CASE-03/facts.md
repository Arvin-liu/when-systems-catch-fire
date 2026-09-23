# CASE-03 — Cinder Index Bridge

All names, values, devices, and observations in this case are synthetic.

## Recorded facts

- The fixture routes a token through an upstream counter and a downstream bridge counter.
- For token `V-2`, the recorded downstream values are lane A `14` and lane B `17`.
- The baseline anchor `A0` needed to compare the two bridge offsets is marked `NOT_RECORDED` in the source log.
- The source log contains no reset checksum for the two lanes.
- The fixture lists two possible next actions but records neither as selected or executed.

## Candidate actions listed in the fixture workspace

- Candidate A: obtain a fresh `A0` anchor and reset checksum, then capture both lane values in one fixture cycle.
- Candidate B: read the downstream mirror register for each lane before deciding whether to collect another pair.

The workspace lists both actions. It contains no baseline anchor, reset checksum, selection rationale, or follow-up observation.

## Unrecorded items

- The baseline value `A0`.
- Whether the recorded lane values share the same reset state.
- The bridge offset for either lane.
- Any causal explanation for the recorded values.
