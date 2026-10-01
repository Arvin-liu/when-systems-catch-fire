# IGNITION-20261001-229-R2 protocol freeze

## Identity and fixed interpretation

- `EXPERIMENT_ID=IGNITION-20261001-229-R2`
- `ANALYSIS_CLASS=SECONDARY_SALVAGE_ANALYSIS_OF_PREEXISTING_R1_FROZEN_SUCCESSOR_DATASET`
- `R1_PRIMARY_STATUS_REMAINS=STOPPED_PROTOCOL_DEVIATION_NO_SCIENTIFIC_RESULT`
- `NEW_SUCCESSOR_SESSIONS=0`
- R1 receipt head: `172746ff9711e25db5aec86cfc0325d6e9e21f1f`.
- R1 formal frozen head: `d7c4715d0cdc23b8d2b0bf4c5285ce0ac6d5041b`; PR #240 remains OPEN + DRAFT + UNMERGED.
- The only raw dataset eligible here is the exact 18-session R1 freeze with manifest SHA-256 `fcdd4b742ffd0cd7860d2ea583ea39c14ee1aa11fd832c0ab4388a3c5dd97bc0`.
- The only `case_inputs_by_lineage` source is the byte-identical historical file at commit `4ee132e8d50e8805c466cb5d681aaa18c34c9f68`, path `ignition/reports/evaluations/ignition-229-clean-transfer-interface-r0/run/case-input-values-and-route-expectations.json`, SHA-256 `b2d44d56aa602e429a8f3ddded61e0b3524b16700a4d35232126a5e264ffa057`.

## Phase gates

1. Verify exact command snapshot, sole nonterminal `CURRENT_CONTROL`, R1 receipt/PR/freeze, all listed raw-file hashes, the original 19-file source bundle, exact historical map hash, and quarantine path/hash inventory. Any mismatch stops as `TASK229_R2_PREFLIGHT_CONFLICT`.
2. At exact R1 formal head run the official knowledge-experience generator check. Repair only the four authorized generated outputs if and only if the first check reproduces precisely that drift; require a byte-stable second check and complete foundation validation. Any extra path stops as `TASK229_R2_CI_REPAIR_SCOPE_CONFLICT`.
3. Freeze this target-blind protocol package before any packet construction. This phase-two freeze-manifest hash is the fixed seed derivation anchor. The seed contract is a derived record and cannot be self-included in that hash anchor.
4. Author one deterministic builder and one independent checker in separate fresh H1-qualified ephemeral CLI processes. Each process receives only the synthetic authoring package below; neither receives target/case content, real raw responses, policy content, condition-to-outcome results, or R1 evaluator artifacts. Run the entire synthetic gate, freeze both code byte streams and hashes, and stop as `TASK229_R2_SANITIZER_CONTRACT_NOT_ESTABLISHED` if contract or fixture results disagree.
5. Only after the builder/checker freeze may R2 bind real R1 raw data, the exact fixed map, and frozen Task228 policies. Do not reconstruct or recode the map.
6. Apply the frozen builder to one matching response/case/criteria pair at a time. The independent frozen checker must pass each pair. Freeze the complete new packet corpus and response-ID key before any evaluator receives a packet. Any failure stops as `TASK229_R2_PACKET_SANITIZATION_FAILURE`; do not patch or tune.
7. Assemble two evaluator prompts from the original frozen rubric/schema and exact frozen target/evaluator criteria. Use deterministic orders from the two seeds in `evaluator-seed-contract.json`; freeze both prompts before dispatch. Use two distinct fresh H1-qualified ephemeral CLI processes, model `gpt-6-astra`, effort `medium`, no tools or external sources, and no R1 evaluator history. No reconciliation or third evaluator.
8. Build a new analysis input with only the frozen R1 18 responses, the exact historical map, and the two fresh R2 sheets/keys. Run original Task229 `tools/recompute.py` byte-identically twice over immutable inputs. Any byte mismatch stops as `TASK229_R2_RECOMPUTE_MISMATCH`.
9. Write results, exact hashes, CI, and receipts; keep both PRs OPEN + DRAFT + UNMERGED. Terminal chat marker is `1111_RELAY_UPDATED`; then stop and await Owner/GPT. Do not launch Task230.

## Authoring isolation and immutability

The `builder-authoring-package/` contains only the four byte-identical original schemas/procedure, metadata-only deny-token manifest, synthetic fixtures, and the generic authoring requirements. No real case, target, raw response, policy, evaluator prompt/key/sheet, condition-to-outcome map, or R1 packet-builder/scanner source is present. Builder/checker bytes, deny tokens, rubric, thresholds, prompt/order rules and recomputation source are immutable after real data is first opened.

## Seed derivation

Let `F` be the lowercase hexadecimal SHA-256 of the frozen `freeze-manifest.json` bytes. For label `L`, derive `seed = SHA256((F || L).encode("ascii"))`, where `||` is literal concatenation and output is lowercase hex. Packet order is the ascending lexical order of `SHA256((seed || "\0" || response_id).encode("utf-8"))`, with `response_id` as the final tie-breaker. No interactive ordering is permitted.
