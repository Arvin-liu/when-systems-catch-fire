# Responsibility Domain Registry R1

**State:** isolated candidate, `CANDIDATE_NOT_EFFECTIVE`

**Work identifier:** `RESPONSIBILITY-DOMAIN-REGISTRY-IMPLEMENTATION-01` (ordinary work identifier; not a Formal Task ID or ordinal)

**Formal main baseline:** `509d49e0b26216ce5443d5c3677aed6c4da4ef4b`

**Draft responsibility matrix source:** PR #275 head `b188dbab54677484aaf914a134064903b8902a43`

This document describes [the candidate registry data](../../data/operations/responsibility-domain-registry-r1.json), its [schema](../../schemas/operations/responsibility-domain-registry-r1.schema.json), and its [validator](../../tools/operations/validate_responsibility_domain_registry.py). The candidate is not effective on Formal main. Owner acceptance of the domain boundaries does not make this branch, file, or any unaccepted component relation current.

## Registry scope

Responsibility domains describe component duties, boundaries, interfaces, consumers, dependencies, lifecycle, maturity, and supporting evidence. The domain set is open and has no numeric limit. IDs, names, and aliases must be unique after case folding. The validator reads each domain ID from the registry; it does not define a domain enum.

R/O/G definitions are copied exactly from the pinned #275 matrix:

- R: `Research discovery and evidence formation.`
- O: `Expression, operation, and presentation of typed R outputs.`
- G: `Cross-cutting constraints on sources, evidence, permissions, claim ceilings, and publication.`

The Owner has accepted these three definitions and the four following responsibility boundaries for this registry mechanism:

- `agent_execution_coordination`
- `formal_repository_change_coordination`
- `bounded_function_execution`
- `decision_support_mapping`

That acceptance is recorded at [#164 comment 7093080490](https://github.com/Arvin-liu/1111/issues/164#issuecomment-7093080490). The registry still remains an isolated candidate pending independent review and a later Owner decision about publication and Formal lifecycle.

`decision_support_mapping` covers manually curated, source-marked, versioned map projections for declared observers and decision questions. It does not establish a mature automated decision engine. The current snapshot freshness and actual external decision benefit remain unverified.

## Source layers and relationship states

The registry keeps three separate layers:

1. **Component identity snapshot.** All 106 component IDs and their `canonical_target`, `component_type`, and `lifecycle` values come from the fixed Formal main Project Component Registry. The validator resolves each source row and checks those fields against the pinned commit.
2. **Raw #275 matrix snapshot.** The complete matrix document is retained with its PR head, path, and Git blob SHA-1. Its 18 `SINGLE_DOMAIN_PRIMARY`, 2 `SHARED_CROSS_DOMAIN`, and 86 `UNRESOLVED` records, including each original primary and participating/interface fields, are source facts. The validator checks the snapshot against the pinned Git object when available and checks every relationship decision against the exact raw status and primary.
3. **Relationship decisions.** A concrete component/domain/type decision is `source_declared`, `proposed`, or `owner_accepted`. Where no relation is supported, an explicit `unresolved` assessment has null domain and relationship fields.

Current decision counts are derived from the data, not used as a limit:

- 28 source-declared relations: 20 primary declarations, 4 non-primary participating declarations, and 4 shared-interface declarations from the matrix.
- 107 candidate proposals remain `proposed`.
- Only Q14's `decision_support_mapping` primary and G shared-interface relations are `owner_accepted` by comment 7093080490.
- 2 components with no proposed relationship remain explicitly unresolved.

The exact 86 matrix rows remain `UNRESOLVED`, even where this candidate proposes one or more component relations. The source matrix's `participating_domains` array is copied unchanged; its non-primary entries are represented as source-declared `participating` relations, while its primary domain is not duplicated as a participant. The original source row remains available for inspection.

The earlier R0.1 audit commit (`f34438c…`) and prior candidate commit (`a30ac9c…`) are local unpublished inputs. The prior candidate's source catalog entry says so explicitly; this registry does not assume either object is remotely visible. PR #275 is also a Draft source snapshot, not an accepted current matrix.

## Relationship kinds and derived views

Relationship kinds are `primary`, `participating`, and `shared_interface`:

- `primary` describes the component's main responsibility in a domain.
- `participating` describes a supporting contribution without primary responsibility.
- `shared_interface` describes an evidenced boundary at one or more domains. It does not establish primary ownership.

The validator's `derive_domain_views` function derives:

- `core_components` from primary relations;
- `participating_components` from participating relations;
- `interfaces` from shared-interface records at each evidenced endpoint.

The three views can overlap. `interfaces` is a view of interface evidence, not a fourth exclusive membership kind. Counts should be made from relation decisions and should not add overlapping views together.

An external consumer is recorded in `external_consumer_interfaces`, with a source domain, consumer ID, interface type, component IDs, evidence, and status. It does not require or invent a target responsibility domain. The Toolbox Function OS evaluator relation remains proposed and is typed `offline_candidate_bundle_evaluation`.

## Q14 boundary

The raw #275 row for `q14` remains `UNRESOLVED` with `primary_responsibility_domain: null`. The Owner has accepted the candidate relationship rule that Q14 is primary in `decision_support_mapping` and has a G shared/interface relation. This relation decision does not rewrite the matrix snapshot.

The accepted mapping describes a manually curated, versioned projection that is marked with sources and claim limits. It does not establish current snapshot freshness or a verified external decision benefit. It does not own Charter permissions, acceptance, publication, or the Formal system-map generation chain.

The validator bounds `owner_accepted` component relations to the two exact Q14 relations in the cited ruling. The remaining prior-candidate relations are kept `proposed`; none becomes accepted merely because it appears in a domain record or derived view.

## Validation Map separation

The responsibility-domain registry and the Validation Map are different sets with different purposes. The current Validation Map schema has a closed `R/O/G` route-domain enum, and its route domains identify validation consumers and targets. They do not define complete component ownership.

`validation_domain_associations` is empty. Adding a responsibility domain creates no Validation Map route, target, test group, executor, reviewer, publisher, or permission. An eventual association must identify an existing component, responsibility domain, current Validation Map route domain, and target already declared for that component; it must have evidence and a separate explicit Owner migration authorization. Comment 7093080490 does not grant that migration authorization.

Other closed vocabularies keep their own meanings, including `component_type`, topology `relation_domain`, and change classifications. This registry does not change their schemas, values, or consumers.

## Adding a domain or relation

To propose a domain:

1. Add a stable unique ID, non-colliding name/aliases, explicit included and excluded responsibilities, inputs, outputs, consumers, dependencies, lifecycle, and maturity.
2. Add source evidence with a catalogued repository/comment, exact commit where applicable, path, JSON pointer or evidence key, and blob SHA-1 when available.
3. Mark it `proposed` until a matching explicit Owner acceptance record supports `owner_accepted`.
4. Run the schema, semantic validator, and focused tests. There is no maximum domain count or ID list to edit.

To add a component relation, reference an existing component and domain, choose one relation kind, state its decision status, and include resolvable evidence. Preserve the raw matrix row and its status even when proposing a different or additional relation. A new relationship never creates a Validation Map association by itself.

## Focused checks

From the `ignition/` directory:

```sh
python3 tools/operations/validate_responsibility_domain_registry.py --check
python3 -m unittest tests.test_responsibility_domain_registry
python3 -m py_compile tools/operations/validate_responsibility_domain_registry.py tests/test_responsibility_domain_registry.py
git diff --check
```

These checks validate this candidate only. They do not establish independent scientific review, Foundation status, Formal main acceptance, route migration, production maturity, or external execution behavior.
