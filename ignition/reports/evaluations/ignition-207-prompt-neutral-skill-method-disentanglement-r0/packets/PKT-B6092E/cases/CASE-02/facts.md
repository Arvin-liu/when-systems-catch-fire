# CASE-02 — Brindle Stage Loom

All names, values, devices, and observations in this case are synthetic.

## Recorded facts

- The fixture has one active path and one shared state register.
- The recorded state before the last event was stage `2`, register `9`.
- One `advance` event moved the stage to `3` and the register to `11`.
- The fixture has no reset control; an `advance` event changes the shared state in place.
- The event log contains the active path, starting stage/register, event name, and ending stage/register.
- The fixture log contains no explanation for the register change.

## Candidate actions listed in the fixture workspace

- Candidate A: run a two-lane paired replay using the last recorded stage and register as the starting point.
- Candidate B: advance one stage at a time and record the stage and shared register after each transition.

The workspace lists both actions. It does not record a selection, an execution, or a result for either candidate action.

## Unrecorded items

- Whether a repeatable starting state can be restored after another advance event.
- The value of the shared register at any intermediate stage.
- Any causal explanation for the recorded values.
