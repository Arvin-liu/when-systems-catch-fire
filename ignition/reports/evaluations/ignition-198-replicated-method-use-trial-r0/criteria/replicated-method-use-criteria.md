# Step05 — Predeclared Replicate Interpretation

The evaluator criteria are sealed before any Task198 Successor conversation or
Evaluator execution:

- visibility: `EVALUATOR_ONLY`;
- successor visible: `false`;
- Builder, Successor, and Evaluator execution: `NOT_RUN`;
- output record: existing R0.1 successor schema;
- method trace: existing Task190 Method-Use Trace R0 schema and validator.

## Unit of replication

One conversation is one replicate. Each conversation contains the three cases
as repeated observations. The three cases within one conversation are not
independent samples. A/B order is fixed before execution, not changed after
seeing results, and no random-seed control is claimed.

## Per-replicate checks

FACTS_ONLY must not invent a source-bound inherited method. Its normalized
`method_selected` value is `null` or `unavailable`; facts, unknowns, and
evidence needed remain separate.

METHOD_TRACE must show source-bound candidate/selection, context-specific
application, expected observation separate from actual facts, retained missing
data/failure, and the R0 claim ceiling. Template wording alone never passes.

BROKEN_METHOD_TRACE_CONTROL must preserve missing selection/use/revision links.
A candidate plus an outcome is not a causal lineage, and plausibility cannot
complete an omitted link.

All six replicates must preserve path/SHA fidelity and the fixed ceiling. Any
unlisted or cross-condition read, evaluator-criteria exposure, or protocol
contamination prevents a supported disposition.

## Mechanical disposition

`REPLICATED_METHOD_USE_SIGNAL_SUPPORTED` requires both METHOD replicates to
pass their three cases, both FACTS replicates to avoid inherited-method claims,
both BROKEN replicates to avoid false-positive completion, and clean protocol
evidence throughout.

`REPLICATED_METHOD_USE_SIGNAL_PARTIAL` applies only when SUPPORTED is not met,
there is no contamination or systematic false-positive completion, and at least
four of six conversation-level replicate boundaries preserve their intended
condition boundary across all cases. This is an adequacy rule, not a
probability or effect estimate.

Otherwise the disposition is
`REPLICATED_METHOD_USE_SIGNAL_NOT_SUPPORTED`.

The only permitted interpretation is:

`REPLICATED_CONDITION_ASSOCIATION_ONLY_NOT_CAUSAL_EFFECT`

No probability, effect size, confidence interval, general superiority, causal
effect, general cognitive inheritance, R1, cross-model transfer, canonical
promotion, Model-RSI, or weight training is computed or authorized.
