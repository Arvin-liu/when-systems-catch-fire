# Distribution And Decision Collapse Control Plane

Status: `121Q13_CONTROL_OVERLAY`

This control plane treats AI and human judgments on open-ended questions as context-conditioned samples, not as final answers or fact evidence.

## SampleEnvelope

A sample records:

- model and model version when available;
- prompt and context hashes;
- sampling conditions such as role, memory state, temperature, and ordering when available;
- output hash;
- proposed mechanism;
- proposed action;
- uncertainty;
- order sensitivity;
- stance sensitivity;
- provenance class.

The same model answering the same prompt multiple times provides a response distribution sample. It is not independent external evidence.

## HypothesisDistribution

A distribution keeps candidate hypotheses, weights or rankings, support, counterevidence, sensitivity, and unresolved items.

Weights are not truth probabilities unless separately justified. They are local decision aids under recorded context.

## DecisionCollapseRecord

Sometimes a deadline, cost limit, or reversibility condition forces action before the hypothesis distribution converges. This is decision collapse, not truth collapse.

A collapse record preserves:

- pre-collapse candidates;
- ranking or weight basis;
- trigger;
- dissent;
- unresolved items;
- rollback conditions;
- threshold used.

Later narrative must not overwrite the real pre-collapse uncertainty.

## Three Thresholds

### Action Threshold

Low-risk, reversible, affordable-loss actions may proceed with lower certainty when Charter Gate passes and rollback exists.

### Claim Threshold

Claims that a mechanism is supported require discriminating evidence, alternative mechanism review, and a bounded claim ceiling.

### Scale Threshold

Scale, irreversible intervention, commercial deployment, or effects on silent subjects require stronger evidence, Charter Gate review, sustainability analysis, and explicit refusal or rollback conditions.

## Sensitivity Tests

For open-ended judgment tasks, record whether conclusions change under:

- reversed order of candidate presentation;
- stance-blind input;
- independent context resampling.

Stability across samples only says something about output sensitivity. It does not prove external facts, mathematical claims, or empirical causality.
