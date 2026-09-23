# Replication / order / template analysis (Step03)

## Sealed dimensions

- **ACROSS-CASE-CONSISTENCY**: PASS - Each of the three cases is evaluated separately per replicate. No case-level failure, missing measurement or unresolved disposition was averaged away; 18 case records x 4 criteria = 72 rows, all PASS, with 11 advisory annotations retained individually.
- **ACROSS-REPLICATE-CONSISTENCY**: PASS - A and B preserve the intended condition boundary in both replicates (FACTS 2/2, METHOD 2/2, BROKEN 2/2). No replicate was excluded and no outcome-adaptive reinterpretation was used. Repeated consistency is not treated as causation.
- **CASE-ORDER-SENSITIVITY**: PASS - A order (03,01,02) and B order (01,02,03) were frozen before execution and differ. No boundary failure appears in only one order, and no divergence co-occurs with case position. Structural caveat retained: with one conversation per (condition, replicate), order is perfectly confounded with replicate (A-order always paired with replicate A), so order is descriptive, not a randomized control.
- **WORDING-TEMPLATE-IMITATION**: PASS - The method replicates repeat the candidate identifier method:bounded-replay-contrast-r0, but each case adds a distinct, case-bound rationale (K7 repeatable; B3 plus four-tick watchdog window; fold=2 repeatable after reset) and a distinct expected-observation statement. Wording repetition alone was not counted as source-bound use.
- **FALSE-POSITIVE-COMPLETION**: PASS - No invented inherited method in FACTS A/B; no manufactured selection/use/revision link in BROKEN A/B; no expected observation reported as actual in METHOD A/B; the watchdog expiry failure is retained in every replicate that touches REPL-CASE-02.
- **SOURCE-PROVENANCE-FIDELITY**: PASS - Step00 mechanical gate: read-manifest entries equal packet read_allowlist exactly, each path once, each recorded SHA equal to the packet pin and to the exact-base final bytes, read_channel cognitive_packet_read, read_status READ, 0 unlisted / cross-condition / evaluator-sealed reads.
- **UNCERTAINTY-PRESERVATION**: PASS - Unknowns, boundaries, obligations and claim ceilings are populated in all 18 records; missing measurements are typed NOT_MEASURED or retained as unknowns; no uncertainty collapses into a causal, capability, inheritance, R1 or canonical claim.

## Independence boundary

- replicate unit: conversation (6 replicates, 18 case records)
- the 3 cases inside one conversation are NOT independent samples
- 6x3 must not be reported as 18 independent replicates
- random seed control: none
- repeated consistency is not causal proof

## Execution-environment attestation

Task200-205 commands all declare `model 5.6 Terra / reasoning medium / speed standard`.
None of the six frozen bundles or any auditable operational metadata independently records the actual runtime model or configuration.

`MODEL_CONFIGURATION_ATTESTATION: COMMAND_ASSIGNED_NOT_INDEPENDENTLY_VERIFIED`

This does not invalidate the trial. It limits any 'same-model' wording to *assigned configuration* rather than cryptographically or runtime-verified identity.

## A/B order

- A: REPL-CASE-03, REPL-CASE-01, REPL-CASE-02
- B: REPL-CASE-01, REPL-CASE-02, REPL-CASE-03
- no boundary failure appears in only one order; no divergence co-occurs with case position; order is confounded with replicate letter and is reported descriptively only.