# Task185 Step07 — Asset Structure: Tag → Relation → Method-Use Audit

## Scope and reproducible sample

The audit is anchored at the frozen Task181 tree `7cab7541895620d68d5bce2d16c46871ebd03ac0`. It uses the Task172 route index stored at that tree (`ignition/data/research/task172-routing-r1/step07-routing-index.json`, blob `3f9eb38581681b67b1b90c9638cd87d17a844932`); the index itself declares source head `03a2b33cced830418cc310a59b519fca8d10f2fa`, so it is a versioned derived snapshot, not a live canonical registry.

[asset-structure-audit.jsonl](./asset-structure-audit.jsonl) contains 450 unique sampled route records: 150 `FUNCTION_ASSET` and 300 `NONFUNCTION_CLAIM`. The deterministic sample is stratified by function census identity / nonfunction claim class and crosswalked to 13 mechanism families already named in the Step02 atlas. This family assignment is an analysis aid, not a native tag or semantic-equivalence claim. Within each stratum, IDs are lexically sorted and evenly spaced; the JSONL manifest records each stratum and count.

For every sampled row, the route index's `source_record_sha` matched the `record_sha256` of its Task181 function identity-card or nonfunction claim-registry record: **450/450**. This verifies the sampled authority links, not all 24,161 route annotations. No claim text, source payload, held-out subtree, Task182-R1 branch/worktree/output, or Task186 report is in the sample.

## What the tags can do

At the frozen tree, the route index has 24,161 canonical-ID candidates (6,158 function records and 18,003 nonfunction records). Each route row carries `asset_role`, `collision_use`, classification state, topic, UNESCO field/discipline codes, routing confidence, and a source-record fingerprint. The projection is for candidate retrieval and collision-use narrowing; selected IDs must be checked against the authority registry. It is not truth, evidence, maturity, priority, or permission to call a method. The route contract sets default `top_k=120`, max `top_k=1000`, requires explicit fallback reasons, and lists one-hop dependency expansion as a future bounded operation.

The two tag facets must not be conflated. `asset_role` labels describe a record's assigned role; `collision_use` labels say what kind of retrieval/review the candidate may support. Equal strings across facets are separate fields with different counts. For example, `ANALOGY_SOURCE` and `METHOD_TRANSFER` occur as roles (1,538 and 1,393 records) but have zero `collision_use` records. Conversely, the documented collision-use counts are:

| `collision_use` | Count |
| --- | ---: |
| `EXPLAIN` | 4,567 |
| `COMPARE` | 1,538 |
| `MECHANISM_TEST` | 1,562 |
| `CAUSAL_CHALLENGE` | 1,562 |
| `COUNTEREXAMPLE` | 16,333 |
| `EVIDENCE_CHECK` | 16,494 |
| `BOUNDARY_TEST` | 2,931 |
| `HISTORICAL_CONTEXT` | 14,771 |
| `ANALOGY_SOURCE`, `METHOD_TRANSFER`, `NORMATIVE_CHECK`, `NARRATIVE_CASE` | 0 each |

The role counts are `ANALOGY_SOURCE=1,538`, `EVIDENCE_CHECK=3,285`, `HISTORICAL_CONTEXT=14,771`, `METHOD_TRANSFER=1,393`, and `NARRATIVE_CASE=3,174`. These are overlapping-use or role projections, not disjoint populations. The index has 19 UNESCO field values but zero topic values and zero four-digit discipline values; it can provide bounded field routing, not a deep, populated mechanism ontology.

## Sample results across mechanism families

The sample covers 13 Step02 families. Counts below are sample-row counts (an asset is assigned one research stratum, not multiple native tags):

| Mechanism family | Sample rows |
| --- | ---: |
| `EXECUTION_ORCHESTRATION` | 16 |
| `CLAIM_BOUNDING` | 46 |
| `DECISION_INTEGRITY` | 18 |
| `METHOD_SELECTION` | 46 |
| `STRUCTURALIZATION` | 46 |
| `EVIDENCE_BINDING` | 46 |
| `PROVENANCE` | 16 |
| `OBSERVATION_CALIBRATION` | 46 |
| `COUNTEREXAMPLE` | 46 |
| `ANALOGY_TRANSFER` | 34 |
| `OBJECT_IDENTIFICATION` | 30 |
| `GOVERNANCE_AUTHORITY` | 30 |
| `UNKNOWN_PRESERVATION` | 30 |

Function identity/candidate classification is not itself method readiness: the function census records 6,158 deduplicated discoveries, including 5,537 `INVALID_OR_PSEUDO_FUNCTION` entries. Its summary separately reports `queued_for_human_review=6,146` and `registered_assets=622`; those counters are not treated as a disjoint partition because their sum exceeds the 6,158 census. The README explicitly limits automatic census output to candidates and human-review routing. The route index's 6,158 function rows must not be read as 6,158 validated or callable cognitive methods.

The nonfunction registry has 18,003 canonical claim records with separate claim class, evidence/source references, disposition, claim ceiling and dependency metadata. The closure reports 5,616 records in the `UNRESOLVED_CLAIM` class and 7,467 `HISTORICAL_ONLY` dispositions; these are different axes and are not added together. These claims can supply governed evidence, boundary, counterexample, or context material; their presence in a route index does not turn a claim into an executable method.

## Relations already present, and where they are not surfaced

- Function assets have a separate dependency-edge registry: 1,923 edges, 541 assets with dependencies in the census summary. In the sample, 120/150 function rows had at least one incoming or outgoing dependency edge.
- Nonfunction claims have dependency/evidence/source and supersession lineage. The closure reports 5,643 dependency edges and 50 explicitly unresolved edges. In the sample, 67/300 claims had a dependency edge; 9/300 carried an explicit `FUNCTION_ASSET_AUTHORITY` evidence reference.
- Those relations are not all on the same retrieval surface. Task172 routing returns IDs and facets; its contract leaves one-hop dependency expansion for a future bounded operation. The function and nonfunction relation registries remain separate, with different edge semantics and authorities.
- A broader candidate navigation layer does exist: the Knowledge Experience projection reports 24,773 search records and is generated from source ledgers, function identity cards, and nonfunction claims. Its own contract says the search/cards are derived projections and do not re-adjudicate assets. It is a unified discovery surface, not a unified canonical method-use graph.
- Adaptive Relational Network projections and the corpus-relation graph are derived views with declared sources and claim ceilings. Their existence does not promote graph adjacency, similarity, or embedding distance to truth or method use. The older `function_dependency_map.md` is an audit index/draft; it explicitly says merges/deletions/upgrades were not executed.

## Relation to method-use

The sampled route/authority rows expose identity or claim classification, tags, fingerprints, dependency/evidence/source relations, and disposition. They do **not** encode a typed edge of the form `asset → method selected → method used in context → observed result / failure`. A route role named `METHOD_TRANSFER` is a retrieval role, not evidence that any successor retrieved, understood, or transferred that method. The Task179 R0 method slots are observable contracts but, in the inspected package surface, are not linked to these 450 IDs.

Potential method-material candidates are therefore narrower than the inventory: a function/workflow, heuristic, gate, or decision-rule record with a recoverable operation, typed inputs/outputs, dependencies, allowed-use boundary, provenance, and failure conditions could be manually reviewed as a method candidate. Nonfunction claims are reference/evidence material unless a separate method record supplies a procedure. Auto-candidates, unresolved identities, historical-only claims, or records without recoverable semantics remain inventory/review material—not callable cognitive structure. This is a repository-surface classification only; no Successor was run.

## Derived interpretation and next evidence

There is already useful **candidate retrieval** across both registries and explicit relations inside each registry, but no demonstrated end-to-end `tag → typed relation traversal → method-use event` chain. A minimal future, separately authorized experiment would freeze a small query set, resolve every returned ID to its current fingerprint, follow only declared typed relations, then record method selection/use and outcome in a new noncanonical event contract. Task185 did not implement or execute that experiment.

**Step07 status:** read-only research sample and report only. No bulk asset edits, registry changes, canonical promotion, Successor/Evaluator execution, or authority changes.

## Evidence refs

- `ignition/KNOWLEDGE/TAGS.md@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/data/research/task172-routing-r1/step07-routing-index.json@7cab7541895620d68d5bce2d16c46871ebd03ac0` (embedded source head `03a2b33cced830418cc310a59b519fca8d10f2fa`)
- `ignition/data/foundation/function-assets/README.md@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/data/foundation/function-assets/census-summary.json@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/data/foundation/function-assets/dependencies.jsonl@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/data/foundation/nonfunction-claims/closure-summary.json@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/data/foundation/nonfunction-claims/dependency-graph.jsonl@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/data/governance/knowledge-experience/manifest.json@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/docs/governance/knowledge-experience-layer.md@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/docs/architecture/adaptive-relational-network.md@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/docs/function_dependency_map.md@7cab7541895620d68d5bce2d16c46871ebd03ac0`
- `ignition/agent_runtime/cognitive_inheritance_r0/` schemas and package records at `12e133c6d58a5e22437e42bb75fd912607bb4540`
