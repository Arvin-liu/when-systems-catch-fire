# Discovery, domain responsibility, and execution boundaries R1

This document explains three discovery projections. The machine assets link to
their exact registries and source blobs; those registries and source files
remain authoritative.

## Task-intent discovery

[`task-intent-index-r1.json`](../../data/operations/task-intent-index-r1.json)
contains 16 intent entries drawn only from operations that are both Current and
publicly callable. A caller must supply an independently checked input type;
the router filters against each operation's `accepted_input_types` before
matching the Chinese and English phrase lists. A unique phrase match returns
`CANDIDATE`, multiple matches return `UNRESOLVED`, and no match returns
`UNSUPPORTED`. It does not score, invoke, or authorize an operation. The full
operation registry remains the authority for permissions, modes, limits,
required reads and claim ceilings.

## Component responsibility

[`component-domain-responsibilities-r1.json`](../../data/operations/component-domain-responsibilities-r1.json)
classifies components only where direct responsibility evidence exists:

- **R** — research discovery and evidence formation.
- **O** — expression, operation, and presentation of typed R outputs.
- **G** — cross-cutting constraints on sources, evidence, permissions, claim
  ceilings, and publication.

The current projection assigns 1 component primarily to R, 5 to O, and 12 to
G; 2 are explicitly shared and 86 remain `UNRESOLVED`. The shared entries name
their primary domain, participants, and evidenced interface. Of the 46
components absent from the prior validation map, 10 now have direct
responsibility evidence and 36 remain unresolved. The machine asset records a
separate disposition and reason for every one of those 46 IDs.

The validation map is a different surface: its `domains` and `evidence` express
declared validation associations, while `validation_targets` express consumers.
Neither alone proves responsibility or ownership. The responsibility asset
preserves these fields as a separate projection and does not modify the
validation map.

## Capability, implementation, and execution

[`capability-execution-boundary-map-r1.json`](../../data/operations/capability-execution-boundary-map-r1.json)
maps all 20 registered operations, four Pack manifests, and 77 optional
Experimental catalog entries. It distinguishes discoverability, registration,
Pack metadata loading, proposal routing, opt-in experimental state, and exact
implementation/executor evidence. All operation-to-runtime implementation
bindings remain `UNRESOLVED`: the operation registry does not name an exact
implementation entrypoint and executor pair.

The repository does contain a generic typed local action executor, Runtime
coordinator, Kernel contracts, and executor admission checks. Their existence
does not bind them to a registered domain operation. Pack-aware routing loads
declarative metadata and emits proposals; it does not execute Pack hooks.
The boundary map also cites the Current identity resolver, object-collision
validator/renderer, and operation read-plan generator as related tooling. Those
refs document resolver, validation, and planning behavior; they do not bind an
operation to an action executor.
Optional catalog entries remain Experimental and default off. No execution,
external action, validation result, permission, or Owner decision is inferred
by these projections.

## Lifecycle boundary

This Draft changes discovery projections and navigation only. It does not
change Formal Task identity, ordinal, Current, claim, M/E, permissions,
validation-map semantics, or governance records. `STATE-CHANGELOG.md`,
`docs/project-current-state.md`, and the generated Current Snapshot remain
unchanged because no Current-state or lifecycle transition is authorized or
claimed here. Draft PR status is not Owner acceptance, publication, or
epistemic acceptance.
