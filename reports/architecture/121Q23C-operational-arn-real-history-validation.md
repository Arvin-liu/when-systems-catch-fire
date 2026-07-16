# 121Q23C Operational ARN Real-History Validation

Status: `REAL_HISTORY_OPERATIONAL_PROOF_COMPLETE`

## Commit Pair

- Before ARN operational hardening: `1f3815538cf56d0f35cc06c6b2396fadf33a34a2`
- After ARN operational hardening: recorded in `data/architecture/adaptive-relational-network/real-history/deterministic-replay.json`

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

The real-history projection is generated from declared repository source paths. It proves deterministic projection, rendering, time-respecting path checking, higher-order preservation, embedding-axis summarization and representation diffing across two repository states. It does not prove ontology, truth, value, causality, learning or a psychological mechanism.

## Checks

- The before projection is built from the real pre-ARN commit and has zero ARN operational source files.
- The after projection is built from the current PR #55 head and contains declared ARN source files.
- `NetworkDiff` includes added nodes and relations from the actual repository source delta.
- The valid path is time-respecting.
- The negative path exists under static aggregation but fails temporal ordering.
- The HyperRelation pairwise projection records explicit information-loss residue.
- The embedding summary keeps availability, retrieval, judgment, action, transfer and stability axes separate.
- Repeated generation produces identical hashes.
