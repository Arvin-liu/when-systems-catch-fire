# Step06 — Independent Method-Use Trace R0 Verdict

Repository: `Arvin-liu/when-systems-catch-fire`  
Exact base: `65862bf1f5a4e6880ac16698fc059d522350457b`  
Successor evidence freeze: `c87ba4d94d04a5ee443b45cfa28eef167dbb01b4`  
Evaluation input freeze: `8b90854dc20a58415dfbf5e0984aa596450db5ea`

## Verdicts

- Reconstruction: `METHOD_USE_RECONSTRUCTION_SUPPORTED`
- Bounded transfer: `BOUNDED_METHOD_TRANSFER_SUPPORTED`
- Ablation: `DESCRIPTIVE_CONDITION_CONTRAST` only
- Negative controls: all ten `NOT_TRIGGERED`

The reconstruction result is bounded: all four synthetic TRACE cases passed the five sealed reconstruction criteria. Complete chains were recovered where present; TRACE-03 and TRACE-04 retained missing selection/use/provenance rather than filling gaps.

The transfer result is bounded: the METHOD_TRACE condition passed source-bound selection, application lineage, non-template reasoning, and claim-ceiling criteria. FACTS_ONLY correctly selected no method. A case-manifest source-hash declaration mismatch is disclosed as an input metadata anomaly; exact-base file bytes and Git blob lineage were independently checked.

The three ablation conditions show a descriptive structural contrast in these single executions: FACTS_ONLY reports facts and unknowns, METHOD_TRACE supplies a source-bound chain and bounded application design, and BROKEN_METHOD_TRACE_CONTROL preserves missing links. The conditions were non-randomized, single-run, and not repeated. No causal effect, effect size, probability, or general superiority is claimed.

Evidence validity is clean at the protocol boundary: six bundles are frozen, copied bytes match, read manifests are within their governing allowlists, no contamination or invalid frozen evidence was found, and no Successor commit/push exists. The disclosed input metadata anomaly is not silently repaired or promoted.

## Fixed ceiling

`GENERAL_COGNITIVE_INHERITANCE_NOT_ESTABLISHED`  
`R1_NOT_AUTHORIZED_BY_EVALUATOR`  
`CROSS_MODEL_TRANSFER_NOT_RUN`  
`OWNER_GPT_ADJUDICATION_NOT_RUN`  
`NO_CANONICAL_PROMOTION`

No Owner/GPT adjudication, external MetaRSI integration, Model-RSI, training, or canonical claim promotion was run or authorized. This PR remains Open, Draft, and unmerged.
