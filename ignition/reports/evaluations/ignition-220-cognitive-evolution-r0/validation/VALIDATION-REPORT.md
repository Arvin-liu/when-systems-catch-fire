# IGNITION-220 R0 preparation validation

Task220 prepares a bounded synthetic design for studying evidence-triggered method revision and later successor transfer. It has not launched revision agents, transfer successors, or evaluators, and it has not selected a model, runtime, provider, reasoning effort, or speed mode.

## Step07 freeze status

- Formal base: `1f7286515768347a2a3a131dd0f6de87f631676c`.
- Three fresh synthetic families are frozen: boundary narrowing, split/coexistence, and bounded retire/replace.
- Each family has one M0, one source-bound E1 packet, one sealed revision target, and three held-out cases.
- Six future revision manifests each expose only four hashed inputs: that family's M0 and E1, the shared neutral prompt, and the shared output schema. Held-out cases, sealed targets, transfer materials, evaluator criteria, and sibling outputs are excluded.
- The transfer template fixes three matched conditions across six revision lineages (18 future conversations); no final 18 packets are instantiated.
- The condition-neutral revision, transfer, and chain endpoints and categorical outcome rule are frozen before outputs.
- The task-local validator checks the protocol, input hashes, target/held-out isolation, output absence, branch ancestry, Task217 subtree integrity, freeze inventory, and sidecar binding.

## Repository closure

Step08 will run only existing repository generators, record their exact outputs and SHA-256 values in the Task220 freeze, and verify repository path accounting plus the legacy Task172 R0 compatibility boundary. The Task217 frozen subtree remains unchanged. Exact-head GitHub CI is checked after the final Step08 push and reported separately from this artifact so no workflow result is mistaken for evidence about a later commit.

Current status: protocol validation is intended to pass; repository projection closure and exact-head CI are pending Step08.
