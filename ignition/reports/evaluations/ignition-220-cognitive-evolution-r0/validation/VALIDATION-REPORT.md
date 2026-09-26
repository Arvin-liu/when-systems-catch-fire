# IGNITION-220 R0 preparation validation

Task220 prepares a bounded synthetic design for studying evidence-triggered method revision and later successor transfer. It has not launched revision agents, transfer successors, or evaluators, and it has not selected a model, runtime, provider, reasoning effort, or speed mode.

## Frozen protocol

- Formal base: `1f7286515768347a2a3a131dd0f6de87f631676c`.
- Three fresh synthetic families are frozen: boundary narrowing, split/coexistence, and bounded retire/replace.
- Each family has one M0, one source-bound E1 packet, one sealed revision target, and three held-out cases.
- Six future revision manifests each expose only four hashed inputs: that family's M0 and E1, the shared neutral prompt, and the shared output schema. Held-out cases, sealed targets, transfer materials, evaluator criteria, and sibling outputs are excluded.
- The transfer template fixes three matched conditions across six revision lineages (18 future conversations); no final 18 packets are instantiated.
- The condition-neutral revision, transfer, and chain endpoints and categorical outcome rule are frozen before outputs.
- The task-local validator checks the protocol, input hashes, target/held-out isolation, output absence, branch ancestry, Task217 subtree integrity, freeze inventory, and sidecar binding.

## Repository closure

Step08 ran the repository's existing generators from the full-history clone and froze their output paths and hashes in the Task220 manifest. Local checks passed:

- Human-results generation and check: `HUMAN_RESULTS_OK records=786`.
- Full-history source-first-seen registry: 786 entries.
- Knowledge Experience build/check: 834 cards, 727 changes, 755 layered readings, 24,916 search records.
- Knowledge Experience audit: 1,715 aliases, 29,810 links, eight two-click pages.
- Repository path accounting: 10/10; all Task220 artifact paths are classified as `EVALUATION_EVIDENCE`.
- Nonfunction generation: deterministic across 14 outputs; closure validation 54/54; discovery covers 6,811/6,811 tracked files. The canonical claim registry remains at 18,003 records.
- Self-correction check: 717 deltas and 10 rules.
- Fire Seeds census validation: 64 entries, 821 sources, 755 Knowledge Experience origins; no human Fire Seeds entry changed.
- Human visibility, claim-browser, architecture projection, and full Foundation validations passed; Foundation reported 63/63.

The legacy Task172 R0 changed-path gate now accepts regenerated Knowledge Experience and Fire Seeds files only when each exact path and current SHA-256 appears in the sidecar-bound Task220 freeze. Its prior Task217 inventory remains intact, with no changes under the frozen Task217 subtree. A focused regression case covers an exact Task220 hash replacement and rejects an unlisted or modified projection. The final local R0 gate invocation and exact-head GitHub CI are checked against the Step08 commit before reporting prepared.
