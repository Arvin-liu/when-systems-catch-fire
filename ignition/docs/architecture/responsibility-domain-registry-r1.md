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

## Owner decision binding

The validator treats two exact #164 records as separate anchors. Comment 7093080490 binds the domain set and the four new domain definitions and responsibility boundaries. Comment 7094188476 binds the exact status of the two accepted component relations. The source records identify `Arvin-liu/1111`, issue 164, comment ID, Owner login, a fixed SHA-256 of the retrieved comment body, and a concise summary of the decision content.

For each of the four new domains, the acceptance record stores a canonical SHA-256 over `domain_id`, `name_zh`, `definition`, `responsibility_boundary.included`, and `responsibility_boundary.excluded`. The validator pins each digest and its exact JSON Pointer into the prior candidate at `a30ac9ce110820252523e16019827bdaa941c802`, with the source path and blob SHA-1. The candidate includes [`ignition/data/operations/responsibility-domain-registry-r1-source-snapshot.json.gz`](../../data/operations/responsibility-domain-registry-r1-source-snapshot.json.gz), a compressed, self-contained snapshot of the exact `f34438c…` identity-audit blob and `a30ac9c…` prior-candidate blob. The validator pins each commit/path/blob tuple in code, recomputes each Git blob SHA-1 from the snapshot bytes, and cross-checks against the Git blob object when it is present. It then compares the registry domain, acceptance record, and resolved source object. The source comment hash, Owner identity, accepted domain set, and exact two relation tuples are pinned in validator code, so editing only the registry cannot expand or rewrite acceptance.

This is a local integrity check against the pinned GitHub records and source blob contents; it does not call GitHub at validation time or add a signature system. The snapshot removes reliance on unreachable Git objects in a shallow CI checkout while preserving the original commit IDs, paths, and blob SHA-1 values. The validator code and its pinned constants remain part of the review boundary. The candidate does not claim cryptographic protection against an authorized change to the validator itself.

The global `claim_ceiling` is a structured candidate-state boundary. Its candidate status is fixed to `CANDIDATE_NOT_EFFECTIVE`, and its Formal current/merge, additional relationship, route, execution, review, publication, and external-action authority fields are pinned false by both schema and semantic validator. Replacing the object with permissive prose or changing any field fails validation.

The Q14 maturity limit is a separate `owner_claim_constraints` record, bound to the same exact #164 comment identity and body hash. It is not added to the four accepted-domain boundary fingerprints. The `decision_support_mapping` maturity must remain a manually curated, source-marked, versioned map projection; snapshot freshness and actual external decision benefit are unverified; it is not a mature automated decision engine. Both the structured limits and the Q14 display description are pinned by the validator.

## Source layers and relationship states

The registry keeps three separate layers:

1. **Component identity snapshot.** All 106 component IDs and their `canonical_target`, `component_type`, and `lifecycle` values come from the fixed Formal main Project Component Registry. The validator resolves each source row and checks those fields against the pinned commit.
2. **Raw #275 matrix snapshot.** The complete matrix document is retained with its PR head, path, and Git blob SHA-1. Its 18 `SINGLE_DOMAIN_PRIMARY`, 2 `SHARED_CROSS_DOMAIN`, and 86 `UNRESOLVED` records, including each original primary and participating/interface fields, are source facts. The validator checks the snapshot against the pinned Git object when available and checks every relationship decision against the exact raw status and primary.
3. **Relationship decisions.** A concrete component/domain/type decision is `source_declared`, `proposed`, or `owner_accepted`. Where no relation is supported, an explicit `unresolved` assessment has null domain and relationship fields.

Current decision counts are derived from the data, not used as a limit:

- 28 source-declared relations: 20 primary declarations, 4 non-primary participating declarations, and 4 shared-interface declarations from the matrix.
- 107 candidate proposals remain `proposed`.
- Only Q14's `decision_support_mapping` primary and G shared-interface relations are `owner_accepted` by the exact status recorded in comment 7094188476. Comment 7093080490 accepts the Q14 architecture attribution principle; it does not promote other component relations.
- 2 components with no proposed relationship remain explicitly unresolved.

The exact 86 matrix rows remain `UNRESOLVED`, even where this candidate proposes one or more component relations. The source matrix's `participating_domains` array is copied unchanged; its non-primary entries are represented as source-declared `participating` relations, while its primary domain is not duplicated as a participant. The original source row remains available for inspection.

The earlier R0.1 audit commit (`f34438c…`) and prior candidate commit (`a30ac9c…`) remain the recorded provenance identifiers. Their exact source blobs are carried in the compressed provenance snapshot so validation does not depend on those commits being reachable from a remote ref. PR #275 is also a Draft source snapshot, not an accepted current matrix.

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

The raw #275 row for `q14` remains `UNRESOLVED` with `primary_responsibility_domain: null`. Comment 7093080490 accepts the Q14 architecture attribution principle. Comment 7094188476 records the exact accepted relation statuses: Q14 is primary in `decision_support_mapping` and has a G `shared_interface` relation. This relation decision does not rewrite the matrix snapshot.

The accepted Q14/G `shared_interface` relation has exactly the two endpoints `G` and `decision_support_mapping`; the validator rejects a missing, additional, duplicate, or substituted endpoint. The accepted mapping describes a manually curated, versioned projection that is marked with sources and claim limits. It does not establish current snapshot freshness or a verified external decision benefit. It does not own Charter permissions, acceptance, publication, or the Formal system-map generation chain.

The validator binds those two `owner_accepted` component relations to comment 7094188476 and their specific component, domain, and relationship type. It also requires the actual `owner_accepted` relation set to equal that exact recorded set in both directions: an unaccepted relation cannot be promoted, and either accepted relation cannot be silently demoted or detached from its record. The remaining prior-candidate relations are kept `proposed`; none becomes accepted merely because it appears in a domain record or derived view.

The G → `decision_support_mapping` `governance_boundary` record in `inter_domain_interactions` remains `proposed`. Comment 7093080490 accepts the Q14 attribution principle and its claim limits, but does not accept that interaction's complete from/to, interaction type, component set, and content tuple. An interaction cannot inherit `owner_accepted` from the Q14 component relations or merely by including `q14`; no complete interaction tuple is Owner-accepted by the pinned records.

## Evidence subject binding

Evidence references retain the exact source commit, path, and blob SHA-1 checks. For JSON Pointers attached to a component record, the validator resolves the target object and requires its component ID or explicit component endpoint to match the component under review. Prior-candidate relationship pointers must land on the matching component mapping and exact domain/relation entry; participant pointers must land on the matching component's participant list. Identity-audit evidence keys must resolve to the numbered row that names the same component.

External-consumer interfaces name a `target_type` of `external_consumer`, a separate consumer ID, and an explicit direction. A consumer ID cannot reuse a responsibility-domain ID. An `owner_accepted` interface must match an exact tuple in an anchored acceptance record, including source domain, consumer target, direction, interface type, components, and interaction. Neither current Owner record accepts external-consumer interfaces, so the Toolbox Function OS interface remains `proposed`.

## Validation Map separation

The responsibility-domain registry and the Validation Map are different sets with different purposes. The current Validation Map schema has a closed `R/O/G` route-domain enum, and its route domains identify validation consumers and targets. They do not define complete component ownership.

`validation_domain_associations` is empty, and both the schema and semantic Validator require it to stay empty while the pinned claim ceiling denies Validation Map routes. No current Owner record grants a separate migration authorization. The guard applies even if a source row's free-form `availability` value is changed or the row points to an existing component, route domain, and target. Comment 7093080490 does not grant that migration authorization, and comment 7094188476 records component-relation statuses only.

A future migration requires a separate Owner decision whose repository, issue/comment identity, Owner identity, content hash, and exact migration object are pinned by the Validator. The object binding must identify the component, responsibility domain, Validation Map route domain, and target. Updating `availability` or adding an unbound comment reference is not authorization; the schema and Validator must be deliberately updated against the new pinned decision before any crosswalk can be represented.

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
