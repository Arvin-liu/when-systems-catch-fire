# IGNITION-20261001-229-R2 result

**Terminal status:** `TASK229_R2_SANITIZER_CONTRACT_NOT_ESTABLISHED`

**Classification:** `SECONDARY_SALVAGE_ANALYSIS_OF_PREEXISTING_R1_FROZEN_SUCCESSOR_DATASET`

**R1 primary status remains:** `STOPPED_PROTOCOL_DEVIATION_NO_SCIENTIFIC_RESULT`

R2 stopped at the Phase 03 pre-exposure gate. The independently authored builder and checker disagreed on the set of metadata keys to remove. All three synthetic fixtures passed output, determinism, checker, and zero-token-leak checks, but the frozen contract comparison failed. The candidates were not frozen for real data and were not applied to any R1 response.

## Verified work before stop

- Locked `Arvin-liu/1111@bcb8e640b48bd9d2d0c0b34fc8e61923ee50f0a9`; recursive machine-state scan found `IGNITION-20261001-229-R2` as the sole nonterminal `CURRENT_CONTROL`.
- Verified R1 receipt `172746ff9711e25db5aec86cfc0325d6e9e21f1f`, PR #240 OPEN + DRAFT + UNMERGED at `d7c4715d0cdc23b8d2b0bf4c5285ce0ac6d5041b`, the raw freeze manifest `fcdd4b742ffd0cd7860d2ea583ea39c14ee1aa11fd832c0ab4388a3c5dd97bc0`, and all 73 listed file lengths/hashes.
- Verified the original 19-file preregistration bundle at `961603c2cb8b6cd1aac14ff72ecd946e26828aa5` (19/19) and the historical input-map SHA-256 `b2d44d56aa602e429a8f3ddded61e0b3524b16700a4d35232126a5e264ffa057`. The map was hash-bound only; its semantic contents were not opened.
- Quarantine inventory used path/byte-length/SHA-256 only. No R1 evaluator, key, packet, score, or sanitization-audit content was decoded or reused.
- The official inherited-drift repair changed only the four authorized generated files in commit `e2f94951f4263fc3b6850dd97dfa5516fa1629fc`; second generator check passed and foundation validation passed 63/63.
- Phase 02 protocol package froze at `d1875fec0e78231a184161048fe646be19dc402a`; `freeze-manifest.json` SHA-256 is `7963ede143e38a01f102cbf53ef0dbddd1c9cd110c6f3e2b9297045d70f862f3`. A/B seeds were derived mechanically and frozen.
- Two isolated H1 ephemeral authoring processes used distinct threads `01a0f651-f967-73c1-b517-d86aa55432f7` and `01a0f655-0d66-73c3-b701-7aa518b2ea7f`. Both source/outbound/stdin hashes matched, each workspace was empty and read-only, and neither process invoked tools.

## Synthetic gate and stop reason

The builder produced byte-identical repeated outputs for all three fixtures; the independent checker passed all three; each packet had zero matches across the frozen deny-token list. However, the builder and checker metadata-key sets differ. The complete set delta is in `run/authoring/metadata-contract-delta.json`. Since the contract is not independently established, the hard stop applies even though the current fixtures pass. No implementation or fixture was edited after authoring.

## Exposure and lifecycle boundary

- New successor sessions: **0**.
- Fresh evaluator sessions: **0**.
- Real R1 response/case/target content opened: **no**.
- Fixed map semantics opened: **no**.
- R1 evaluator artifacts reused: **no**.
- Analysis input/recomputation/scientific result: **none**.
- Task230: **not started**.

The candidate builder/checker remain unfrozen and must not be applied to real data. R2 is terminal at this gate; write this receipt to 1111 and await Owner/GPT.
