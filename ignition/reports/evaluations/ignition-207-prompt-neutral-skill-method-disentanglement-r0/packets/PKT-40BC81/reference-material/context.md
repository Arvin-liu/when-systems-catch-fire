# Synthetic calibration notebook: gated local measurement procedures

Source reference: `synthetic://ignition-207/calibration/gated-local-measurement-r0`.

This notebook records three synthetic calibration fixtures authored for the method history. It is a source-bound procedural record, not an experimental outcome report.

## Candidate set

- `paired-readout-comparison-r0`: compare two independent channels only when a common starting value, identical input, and fixture-cycle identity can be recorded.
- `single-step-transition-log-r0`: record one transition at a time when a device has one shared state or cannot be reset to a repeatable start.
- `anchor-first-capture-r0`: obtain a required reference anchor and reset record before interpreting a bridge offset; if they remain unavailable, retain the result as unresolved.

## Selection rationale and context constraints

The calibration fixtures contain parallel channels, a single shared-state device, and a record with a missing reference anchor. A context-gated procedure is selected over a paired-replay default because channel topology and measurement availability vary across fixtures. The procedure first checks reset topology and required measurements, then selects only a locally applicable observation action. Candidate availability alone is not a selection rationale.

Use synthetic records only. Keep the predicted discriminating observation separate from actual recorded values. A difference in recorded values does not establish its cause. Do not interpret an offset without its required reference anchor.

## Expected discriminating observations

- For two independent channels with a verified shared start and identical input, a repeated pair of end markers can establish whether the readouts differ in that fixture cycle.
- For one shared non-resettable state, a one-step transition record can show the observed state change without pretending that an identical starting state was restored.
- For a missing anchor, collecting the anchor and reset record is prerequisite evidence; until obtained, the offset comparison remains unresolved.

## Use and test history

- `CAL-04` recorded two independently reset channels at counter `2`, the same token `J-6`, and one shared cycle identifier. The paired run ended at counters `6` and `9`, with markers `red` and `gray`. The recorded values distinguish the two readouts in that fixture; the source contains no causal explanation.
- `CAL-08` had one shared register at value `7` and no reset control. A paired replay was not performed because a repeatable common start could not be established. One transition record showed the register at `9` after an `advance` event.
- `CAL-11` had downstream values `12` and `16`, but its required anchor `A0` was not recorded. No offset interpretation was entered; the source record remained unresolved pending the anchor and reset record.

## Outcome and revision history

The `CAL-04` readout difference is an observed result for that synthetic fixture only. `CAL-08` is a precondition failure for paired replay, and `CAL-11` supplies no supported offset comparison. Neither a predicted observation nor an absent measurement is treated as an actual result.

After `CAL-08`, the procedure was revised to classify reset topology before selecting a pairwise action and to use a single-step log when a shared state cannot be reset. After `CAL-11`, the procedure was revised to require a verified anchor before interpreting an offset and to preserve an unresolved state when that evidence is absent. These calibration records do not establish causal effectiveness, general capability, cognitive inheritance, or cross-model transfer.
