# Adaptive Relational Network / 自适应关系网络

Status: candidate derived representation.

Adaptive Relational Network (ARN) represents heterogeneous, non-causal, multilayer, temporally activated and higher-order relations plus their perturbation and reconfiguration episodes. It is not a new truth layer and does not replace Foundation, Atlas, MCF, PSD, Function OS, Q12-Q14 or Charter Gate.

## Boundary Rules

- Network representation is not ontology.
- Adjacency, similarity, centrality, community or embedding distance is not truth, value, importance or causality.
- Causal claims delegate to MCF.
- Retrieval, repetition, activation and diffusion are not proof of integration.
- Behavior change is not proof of a specific internal cognitive mechanism.
- Static aggregation cannot create time-impossible paths.
- A graph path must be topology-continuous under the declared edge direction and time-respecting under ARN's model rule; a merely ordered relation sequence is not a path.
- Higher-order relations cannot be silently reduced to pairs.
- Network boundaries, layers and resolution are model choices unless independently established.
- Cognitive examples are non-clinical and non-diagnostic.

## Core Objects

- `NetworkSpec`: model purpose, source, canonical authority boundary and claim ceiling.
- `NetworkNode`: typed entity with provenance, layer membership and uncertainty.
- `TypedRelation`: directed or undirected relation with sign, weight, conditions, layer and temporal bounds.
- `HyperRelation`: group relation that must not be collapsed into pairs without residue.
- `NetworkLayer` and `InterlayerCoupling`: multilayer relation structure.
- `TemporalActivation`: activation window for nodes or relations.
- `NetworkState`: versioned active/inactive/unknown state of nodes and relations.
- `PerturbationInput`: new information, action, evidence, failure or resource change entering the network.
- `IntegrationResponse`: surface assimilation, boundary rejection, local reconfiguration, partial integration, context-gated, compartmentalized, deferred update or unknown response.
- `ReconfigurationEpisode`: changed and unchanged nodes/relations, delay, oscillation and residue.
- `AttractorOrOscillationRecord`: repeated loops, attractor candidates and non-diagnostic boundaries.
- `CascadeOrSpilloverRecord`: local or cross-layer propagation without assuming causality.
- `EmbeddingEvidenceRecord`: independent evidence axes for external availability, retrieval, linkage, conflict exposure, judgment change, action change, transfer and delayed stability.
- `NetworkProjection`: derived view with omitted dimensions and claim ceiling.
- `NetworkDiff`: versioned representation diff only.
- `UnmappedRelationalResidue`: relation uncertainty, boundary ambiguity, higher-order loss, missing bridge or unverified integration.

## Integration

Foundation remains authoritative for object, evidence and claim status. Atlas may render ARN projections. MCF is the causally typed specialization. PSD supplies system and stochastic semantics. Function OS may execute ARN build/probe/diff steps without runtime change. Q12 may choose state-changing actions. Q13 controls attractors, rumination and pseudo-compression. Charter remains the highest normative boundary.

## Operational Surface

The current operational ARN toolchain is intentionally narrow and deterministic:

- `projector.py` builds derived ARN projections only from explicitly declared repository source paths and commits.
- `temporal.py` checks declared numeric activation intervals and detects static-aggregation false positives.
- `renderer.py` renders JSON and Markdown projections by layer, time window and relation class.
- `diff.py` compares nodes, relations, attributes, hyper-relations, temporal activations, integration responses, embedding-evidence axes, residue and deterministic hashes.
- `embedding.py` summarizes availability, retrieval, linkage, conflict, judgment, action, transfer and delayed stability as separate axes.
- `validator.py` validates examples and remains a compatibility entrypoint.

These tools do not discover hidden reality, mind-read integration, infer clinical states, or create a second canonical truth store. They operate on declared repository sources and preserve residue for unknown or unsupported fields.

## Validation Contract

The executable validation chain has two layers:

- Draft 2020-12 JSON Schema validation for every complete ARN instance in `data/architecture/adaptive-relational-network/examples/`.
- Semantic validation for duplicate IDs, reference integrity, non-empty provenance/uncertainty/alternatives/claim ceilings/residue, higher-order preservation, topology-aware temporal paths and overclaim boundaries.

`embedding-probe.json` is not excluded as an unexplained special file. It has an independent strict object contract at `schemas/architecture/adaptive-relational-network-embedding-probe.schema.json`.

Stable interoperability objects are strict: undeclared fields are rejected. Future extensions should use an explicit schema change or a controlled extension namespace rather than silent acceptance.

## Temporal Model Rule

ARN distinguishes three things:

- `time_respecting_sequence`: every relation exists and its interval starts after the prior relation ends.
- `path_continuous`: relation endpoints connect under direction rules with stateful reachable-orientation propagation.
- `time_respecting_graph_path`: both of the above are true.

Direction behavior is explicit:

- `directed`: prior target must match the next relation's source.
- `undirected` and `bidirectional`: either endpoint direction may connect.
- `unknown`: not accepted as a graph-path edge.

This is a local ARN validation rule for avoiding projection errors. It is not a universal theorem about temporal networks.

For multi-edge paths, ARN does not merely check whether each adjacent pair appears connectable. It carries the reachable arrival nodes forward. If an undirected or bidirectional edge must be traversed in one orientation to connect with the previous edge, only that traversal's arrival is available to the next edge.

`TemporalActivation.target_ref` is limited to `node_id` and `relation_id`. Layers, states, perturbations, embedding evidence and network IDs are not activation targets under the current ARN contract.

`NetworkDiff.from_ref` and `NetworkDiff.to_ref` must reference a local `network_id`, `state_id`, `projection_id` or a declared `external_refs.ref_id`. External commit references are allowed only when typed explicitly, such as `ref_type: git_commit`, and remain external version references rather than canonical ARN objects.
