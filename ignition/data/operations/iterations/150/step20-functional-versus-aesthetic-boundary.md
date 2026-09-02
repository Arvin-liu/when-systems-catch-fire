# Task150 Step20 — Functional visual admission versus aesthetic endorsement

Result: `TASK150_STEP20_FUNCTIONAL_VERSUS_AESTHETIC_BOUNDARY_PASS`

Step20 records a boundary, not a visual acceptance decision. The Owner's
scope-split decision allows the provider-neutral base operation to proceed to
a fresh standalone evidence run. It does not grant aesthetic endorsement and
does not turn the operation into a Current capability.

## Functional visual admission

For `visualization.render_derived_system_view`, functional visual admission is
about declared technical use:

- readability for the declared technical purpose;
- viewport containment;
- topology fidelity;
- label and edge collision behavior;
- source/provider/artifact provenance;
- deterministic, bounded generation; and
- fail-closed behavior when a provider or input is unavailable.

Step20 marks these criteria as requiring the fresh exact-head Step21 run. The
decision `ALLOWED_TO_PROCEED` means the run may be attempted; it is not a
claim that the visual evidence has already passed. The current state remains
`NOT_ADMITTED_PENDING_STEP21`.

## Owner aesthetic endorsement

Owner aesthetic endorsement is a separate question covering official Ignition
visual style, homepage or publication suitability, branded-asset suitability
and explicit aesthetic endorsement. Its current state is `NOT_GRANTED` and
`NOT_CLAIMED`. Step20 deliberately records neither `OWNER_REJECTED_VISUAL`
nor `OWNER_VISUAL_ACCEPTED` as a decision.

A future homepage, publication-hero or branded-asset request requires its own
aesthetic acceptance gate. Aesthetic endorsement, if later granted, would not
substitute for functional evidence; functional evidence, if admitted, would
not silently create aesthetic endorsement.

## Split-scope consequences

The matrix in the machine receipt makes both independence directions explicit:
functional evidence can make the base candidate eligible for declared bounded
technical use while aesthetic endorsement is absent, whereas aesthetic
endorsement without functional evidence cannot create functional admission.
Future public or branded use is unavailable from this step alone.

Architecture Delta remains `EXPERIMENTAL_EXTENSION_DEFERRED` with its retained
`FAIL_DEFERRED` viewport gate. The Current Capability Registry remains at 19
operations; there is no registry write, default renderer, Agent Reach,
authentication or live-invocation change, and Task151 remains forbidden.

Exact next action: `TASK150_STEP21_FRESH_STANDALONE_EVIDENCE`.
