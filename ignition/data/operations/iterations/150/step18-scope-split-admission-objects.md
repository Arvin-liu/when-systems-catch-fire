# Task150 Step18 — Scope-split admission objects

Result: `TASK150_STEP18_SCOPE_SPLIT_ADMISSION_OBJECTS_RECORDED`

The Owner reopen is implemented as an object decomposition. Step14's
combined-scope `DEFER` and Step15's Draft-only closeout remain historical
truth; neither receipt is rewritten. The new contract is a candidate
definition, not a Current Registry write.

## Base operation

`visualization.render_derived_system_view` is the provider-neutral base
operation. Its declared flow is:

`CANONICAL/AUTHORED_SOURCE -> ARCHIFY_COMPATIBLE_PROVIDER_ADAPTER -> STANDALONE_DERIVED_VISUALIZATION_ARTIFACT`

The operation remains Ignition-owned, `READ_ONLY_RUN`, repository-mutation
forbidden, and bounded to visual representation of authored topology. Archify
is recorded only as a tested optional provider implementation. Its current
upstream observation is `06dd052602dd9a369e4d034e24faef0917b5a60c`, but Step22
must independently establish compatibility before this observation can enter
an admission envelope.

The base object has its own gates for canonical provenance, node/edge fidelity,
zero topology mutation, standalone viewport containment, fail-closed provider
failure, canonical-source preservation, environment/no-auto-install policy,
immutable compatibility, artifact/provenance receipts, provider-local policy
isolation, no default renderer and no architecture-truth escalation. These
gates are pending their fresh exact-head evidence where indicated; this step
does not turn pending gates into pass.

## Experimental Delta extension

Architecture Delta / Before–Delta–After is a separate
`EXPERIMENTAL_EXTENSION_DEFERRED`, not a Current operation. It retains the
28/28 semantic Delta result and the three `viewer/viewport-overflow` failures
from the fixed upstream wrapper. The Delta gate remains
`delta_viewport_containment_zero_failure = FAIL_DEFERRED`.

The split has two fail-closed directions: Delta failure cannot contaminate a
semantically independent base operation, and base success cannot promote the
Delta extension. A future Delta admission requires its own explicit gate and
review.

## Functional visual use versus aesthetic endorsement

Functional visual admission may proceed to fresh gate revalidation for
declared technical use. Owner aesthetic endorsement is `NOT_GRANTED` and
`NOT_CLAIMED`; it is not silently changed to rejection or acceptance and is
not required for this base scope. Homepage, publication-hero or branded-asset
use would require a separate visual acceptance gate.

The Current Capability Registry remains at 19 operations in Step18. No Delta
entry, provider-specific operation ID, default renderer, Agent Reach change,
authentication change or live invocation is introduced.

Exact next action: `TASK150_STEP19_GATE_TOPOLOGY_REGRESSION`.
