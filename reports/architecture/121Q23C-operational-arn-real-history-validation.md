# 121Q23C/121Q23D/121Q23E Operational ARN Real-History Validation

Status: `REAL_HISTORY_OPERATIONAL_PROOF_REGENERATED_WITH_PATH_STATE_AND_REFERENCE_CONTRACT`

## Commit Pair

- Before ARN operational hardening: `1f3815538cf56d0f35cc06c6b2396fadf33a34a2`
- After ARN path-state and reference closure: recorded in `data/architecture/adaptive-relational-network/real-history/deterministic-replay.json`

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

The real-history projection is generated from declared repository source paths. It proves deterministic projection, rendering, Schema/semantic validator integration, stateful topology-aware time-respecting graph-path checking, higher-order preservation, embedding-axis summarization and representation diffing across two repository states. It does not prove ontology, truth, value, causality, learning or a psychological mechanism.

## Checks

- The before projection is built from the real pre-ARN commit and has zero ARN operational source files.
- The after projection is built from the current PR #55 path-state/reference-closure head and contains declared ARN source files.
- `NetworkDiff` includes added nodes and relations from the actual repository source delta.
- `NetworkDiff` carries typed `external_refs` for git commit references; commit strings are not silently accepted as arbitrary local refs.
- The valid path is `rel-repo-1 -> rel-chain-1`, which is both topology-continuous and time-respecting under ARN model rules.
- The static-aggregation counterexample is `rel-repo-1 -> rel-repo-2`: it exists as a relation sequence and is temporally ordered, but it is not a graph path because the first relation's target does not connect to the second relation's source.
- The topology-only counterexample is `rel-repo-1 -> rel-backdated-1`: it is endpoint-continuous but temporally invalid.
- The HyperRelation pairwise projection records explicit information-loss residue.
- The embedding summary keeps availability, retrieval, judgment, action, transfer and stability axes separate.
- Repeated generation produces identical hashes.

## Deterministic Hashes

- Before projection hash: `b108f598999de7b208e2419013ef7ab221d05b39bb1cb00f166fdfd584c17837`
- After projection hash: `d2de2410b48824fb68ff72634719eb12813514f8b0f3404c353abbc748177ae2`
- Network diff hash: `45da9d322e98d7b582f3694f0d11714a7e3c0135219df09f059de818e90f85cb`
- Pairwise projection hash: `ad73fc5527efa17481dd9178b4fcdc593b7f4ec7d467e320b179ec00f6cb41ea`
- Embedding summary hash: `80b47b94ee60bf074ebcc8f6912cb1075bd28b2261b34e313da5dddc64121313`

Hash change explanation: 121Q23E changed `NetworkDiff` semantics by adding explicit typed `external_refs`, and regenerated the after projection at the 121Q23E repair commit.
