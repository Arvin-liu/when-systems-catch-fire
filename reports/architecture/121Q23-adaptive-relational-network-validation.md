# 121Q23 Adaptive Relational Network Validation

Status: `121Q23E_READY_AS_ADVERSARIALLY_CLOSED_OPERATIONAL_ARN_CANDIDATE`

ARN is a derived representation for heterogeneous, non-causal, multilayer and temporally activated relations. It does not add a truth layer.

Validator and tool coverage:

- Draft 2020-12 JSON Schema validation for each complete ARN example;
- independent strict schema validation for `embedding-probe.json`;
- strict nested object contracts with no silent undeclared fields;
- duplicate ID detection without set-based hiding;
- node, relation, layer, hyperrelation, coupling, activation, state, perturbation, integration-response, reconfiguration, cascade, embedding, projection, diff and residue reference integrity;
- temporal activation target domain restricted to node IDs and relation IDs;
- every ID-bearing ARN collection audited, including attractor and cascade `record_id` namespaces;
- NetworkDiff `from_ref` and `to_ref` restricted to local network/state/projection IDs or declared typed external refs;
- interval validation with `start <= end`;
- topology-aware temporal graph-path validation separated from merely ordered relation sequences;
- stateful reachable-orientation propagation for multi-edge directed, undirected and bidirectional paths;
- provenance, uncertainty, temporal bounds and claim ceiling;
- relation-to-causality overclaim;
- centrality/similarity/community/adjacency as truth;
- static temporal fallacy;
- silent higher-order collapse;
- projection replacing canonical source;
- retrieval or self-report mislabeled as integration/behavior proof;
- missing alternatives and residue;
- deterministic repository-source projection;
- layer/time/relation rendering;
- full NetworkDiff over real repository states;
- higher-order pairwise projection with explicit information-loss residue;
- independent embedding-evidence axis summary.

Real-history proof: `reports/architecture/121Q23C-operational-arn-real-history-validation.md` and `data/architecture/adaptive-relational-network/real-history/`.

121Q23D closure details:

- old false path claim removed;
- valid graph path is now `rel-repo-1 -> rel-chain-1`;
- static aggregation false-positive remains `rel-repo-1 -> rel-repo-2`, which is temporally ordered but topologically disconnected;
- topology-continuous but temporally invalid counterexample is `rel-repo-1 -> rel-backdated-1`;
- deterministic diff hash after regeneration: `d732ef2609b60af0b4af7e1c87d3fdc08a1af476cb2be178efd9223b0023a1d7`.

121Q23E closure details:

- global pairwise endpoint intersection was replaced with stateful reachable-orientation propagation;
- adversarial sequence `A -> B`, `B -- C`, `B -> D` is rejected because edge 2 must arrive at `C`, so edge 3 cannot depart from `B`;
- empty paths are invalid; valid single declared relations with valid intervals are accepted;
- `TemporalActivation.target_ref` now rejects layer, state, perturbation, evidence and network IDs;
- attractor and cascade `record_id` namespaces are duplicate-checked and require non-empty semantic content;
- diff reference integrity now requires local network/state/projection references or typed external refs;
- deterministic diff hash after 121Q23E regeneration: `45da9d322e98d7b582f3694f0d11714a7e3c0135219df09f059de818e90f85cb`.

Integration boundaries:

- Foundation remains authoritative;
- Function OS runtime is unchanged;
- Atlas may render ARN projections;
- MCF handles causally typed specialization;
- PSD supplies system/state/probabilistic semantics;
- Q12/Q13 guide action and anti-attractor controls;
- Charter remains highest normative boundary.
