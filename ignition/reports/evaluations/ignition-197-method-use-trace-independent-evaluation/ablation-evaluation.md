# Step03 — Ablation Condition Contrast

Input freeze: `8b90854dc20a58415dfbf5e0984aa596450db5ea`  
Criteria: Task190 sealed `method-use-trace-evaluator-r0`

This is a descriptive contrast across three independent, single, non-randomized, non-repeated executions. It is not a causal ablation result; no effect size, probability, or general superiority is inferred.

| Condition | A-FACTS-ONLY-BOUNDARY | A-BROKEN-TRACE-BOUNDARY | A-METHOD-TRACE-STRUCTURE | A-SOURCE-BOUND-USE |
| --- | --- | --- | --- | --- |
| FACTS_ONLY (192) | PASS | NOT_APPLICABLE | NOT_APPLICABLE | NOT_APPLICABLE |
| METHOD_TRACE (193) | NOT_APPLICABLE | NOT_APPLICABLE | PASS | PASS |
| BROKEN_METHOD_TRACE_CONTROL (194) | NOT_APPLICABLE | PASS | NOT_APPLICABLE | NOT_APPLICABLE |

FACTS_ONLY reports the four-row synthetic facts, separates interpretation from observation, keeps Row D’s review missing, and states that no method history is supported by input.

METHOD_TRACE recovers the candidate → selection → context → use → outcome → revision structure from the supplied positive-a source, then applies only the recorded contrastive-probe slot as a bounded design. It does not claim that the new probe ran or that the method caused anything.

BROKEN_METHOD_TRACE_CONTROL preserves the candidate and outcome as separate source-backed observations, marks selection and use missing, and rejects candidate-plus-outcome completion.

The observed structural contrast is compatible with an observable aid from the supplied method trace in this bounded synthetic setup. Because each condition ran once without randomization or repetition, that observation cannot establish that the trace caused an improvement or that METHOD_TRACE is generally superior.

Fixed ceilings remain `GENERAL_COGNITIVE_INHERITANCE_NOT_ESTABLISHED`, `R1_NOT_AUTHORIZED_BY_EVALUATOR`, `CROSS_MODEL_TRANSFER_NOT_RUN`, and `NO_CANONICAL_PROMOTION`.
