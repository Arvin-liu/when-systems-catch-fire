# 类型化变更传播闭包 / Typed Change-Propagation Closure

Status: `121Q32T_HISTORICAL`. Iteration method 1.3.0 and interactive system map 0.3.0 are Historical after the 0727 homepage/usage/charter-system-map sync closeout made system map 0.4.0 Current; method 1.2.0 and map 0.2.0 are Historical, map 0.1.0 earlier Historical. Q32I retains this typed-propagation authority.

## The missing executable layer

The synchronization registry can derive which entrances and rendered surfaces require a decision. It does not identify every project component that changed, the typed declared relations along which an assessment must travel, or the map projection that follows. This candidate adds that computation without turning repository reachability into scientific causal identification.

The authority chain is:

`change seeds → canonical project component registry → typed propagation topology + synchronization registry → deterministic fixpoint → component/surface decisions → system-map impact delta + residue → manifest closure binding`

## Three relation domains

The topology keeps three authorities separate:

1. `substantive_causal_candidate` represents a bounded MCF-style hypothesis about real or theoretical objects. It is always informational in repository propagation and cannot automatically mark a file or component changed.
2. `repository_dependency` represents declared generation, derivation, validation, publication, deployment, documentation or version dependencies. It can be traversed according to its declared propagation mode and triggers.
3. `synchronization_obligation` represents project-governance duties. It decides what must be assessed, not what is true in the world.

A Git diff, path match, dependency, graph edge, visual position or traversal result is not evidence of real-world causality. `CausalFabricDiff` supplies useful language for typed differences and residue; it does not license the calculator to identify a mechanism.

## Canonical assets

- Component identity, canonical target, lifecycle source and path resolution: `data/operations/project-components.json`
- Declared relation classes and propagation topology: `data/operations/change-propagation-topology.json`
- Human/AI/Agent/machine/deployment synchronization obligations: `data/operations/synchronization-surfaces.json`
- Display-only geometry, grouping, color and order: `data/architecture/interactive-system-map-layout.json`
- Request and closure products: `data/operations/propagation/`
- Calculator: `tools/operations/compute_change_propagation.py`
- Schemas: `schemas/operations/project-components.schema.json`, `change-propagation-topology.schema.json`, `change-propagation-request.schema.json` and `change-propagation-closure.schema.json`

The component registry and topology are declared project authorities, not an ontologically complete catalog. Missing mappings, unknown components and cycles remain explicit blocking residue.

## Fixpoint contract

Each request supplies changed paths, optional explicit component seeds, state-transition subjects, changed dimensions, change classifications, component decisions, surface decisions and a system-map decision.

The calculator then:

1. resolves paths to canonical components;
2. traverses only declared, triggered, non-informational relations;
3. unions that closure with synchronization-registry obligations;
4. repeats until no new component or surface appears;
5. requires one `CHANGE`, `NO_CHANGE_WITH_REASON` or `NOT_APPLICABLE` decision for every required item;
6. derives the candidate system map and compares it with the declared base revision;
7. emits a machine closure, a human impact report, a map delta and unresolved residue;
8. binds their deterministic closure hash into the iteration manifest and seal.

`NO_CHANGE_WITH_REASON` is first-class. A historical spelling correction can resolve to a component while producing no capability, lifecycle, navigation, relation or display change. Conversely, a new formal component must either enter the visible layout or carry a machine-validated hidden representation target and reason. This prevents both all-repository fan-out and invisible architecture drift.

## System-map projection

Historical 0.3.0 and 0.2.0 replaced the materialized map JSON as hand-maintained authority; Current 0.4.0 retains the chain:

`project-components.json + change-propagation-topology.json + interactive-system-map-layout.json → generate_interactive_system_map.py → interactive-system-map.json + SVG + README/Pages`

Layout remains an editorial overlay. Node identity, canonical target, lifecycle status and visible relation metadata come from the registries. Generator `--check` fails when the projection or SVG is stale, when a visible component is missing, or when a hidden new component lacks a declared representation and no-change reason.

The compatible baseline remains 9 groups, 41 visible nodes, 35 visible edges and L0–L6. The new propagation infrastructure is represented by the existing iteration/synchronization/map components; it does not justify a decorative node, L7 or new truth layer.

## 121Q32 closure

The candidate's own closure is recorded at:

- `data/operations/propagation/121Q32-request.json`
- `data/operations/propagation/121Q32-closure.json`
- `reports/operations/121Q32-change-propagation-impact.md`
- `data/operations/propagation/121Q32-system-map-delta.json`
- `data/operations/propagation/121Q32-residue.json`

Its zero residue means only that all declared mappings and obligations received a decision at this revision. It does not prove that the registries are complete, the project has no unknown dependency, or any substantive causal claim is correct.
