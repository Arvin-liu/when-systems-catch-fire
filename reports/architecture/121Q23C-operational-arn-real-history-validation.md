# 121Q23C/121Q23D Operational ARN Real-History Validation

Status: `REAL_HISTORY_OPERATIONAL_PROOF_REGENERATED_WITH_VALIDATION_CONTRACT`

## Commit Pair

- Before ARN operational hardening: `1f3815538cf56d0f35cc06c6b2396fadf33a34a2`
- After ARN validation-contract closure: recorded in `data/architecture/adaptive-relational-network/real-history/deterministic-replay.json`

## Artifacts

- `before-projection.json`
- `after-projection.json`
- `network-diff.json`
- `pairwise-hyperrelation-projection.json`
- `embedding-summary.json`
- `deterministic-replay.json`
- `after-layer-architecture.md`
- `after-time-window.md`
- `after-timeline.md`

## Proof Boundary

The real-history projection is generated from declared repository source paths. It proves deterministic projection, rendering, Schema/semantic validator integration, topology-aware time-respecting graph-path checking, higher-order preservation, embedding-axis summarization and representation diffing across two repository states. It does not prove ontology, truth, value, causality, learning or a psychological mechanism.

## Checks

- The before projection is built from the real pre-ARN commit and has zero ARN operational source files.
- The after projection is built from the current PR #55 validation-closure head and contains declared ARN source files.
- `NetworkDiff` includes added nodes and relations from the actual repository source delta.
- The valid path is `rel-repo-1 -> rel-chain-1`, which is both topology-continuous and time-respecting under ARN model rules.
- The static-aggregation counterexample is `rel-repo-1 -> rel-repo-2`: it exists as a relation sequence and is temporally ordered, but it is not a graph path because the first relation's target does not connect to the second relation's source.
- The topology-only counterexample is `rel-repo-1 -> rel-backdated-1`: it is endpoint-continuous but temporally invalid.
- The HyperRelation pairwise projection records explicit information-loss residue.
- The embedding summary keeps availability, retrieval, judgment, action, transfer and stability axes separate.
- Repeated generation produces identical hashes.

## Deterministic Hashes

- Before projection hash: `b108f598999de7b208e2419013ef7ab221d05b39bb1cb00f166fdfd584c17837`
- After projection hash: `82981bdb3dc6bdb24e7ae34cfeacc773b25d6cf06bc031ce043cefe078aa8985`
- Network diff hash: `d732ef2609b60af0b4af7e1c87d3fdc08a1af476cb2be178efd9223b0023a1d7`
- Pairwise projection hash: `ad73fc5527efa17481dd9178b4fcdc593b7f4ec7d467e320b179ec00f6cb41ea`
- Embedding summary hash: `e7f0bb8541a011fed69cd1ab91e879ea1f7231c9a9da7c05ce7ceead73df167b`
