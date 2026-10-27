# DSPy and harness/prompt optimization

## What DSPy optimizes

DSPy expresses LM work as signatures and composable modules, then compiles a declared program against user-provided examples and a metric. In the pinned repository, `BootstrapFewShot` runs a teacher over training examples and accepts traces according to the caller's metric/threshold. `MIPROv2` searches instruction and few-shot candidates and scores a candidate program using an `Evaluate` object over a validation set. The caller can provide distinct prompt/task models, but the implementation can use a configured model for both.

This is a local program/harness optimization primitive: the output being compiled can include instructions, demonstrations, and module configuration. The optimizer, candidate-generation algorithm, and metric are still defined by the framework/application. Nothing in this mechanism alone demonstrates that the improver changes how it improves, revises its metric, or inherits a new method-selection rule. Calling it a Harness-RSI instance is an `OUR_INFERENCE` analogy, not a factual system identity.

## Metric and validation boundary

The metric is supplied by the caller and controls trace acceptance and candidate scoring. At the pinned 2026 commit, MIPROv2 requires a trainset; if valset is omitted, it splits a subset from that supplied trainset for validation. That version-specific fallback is an internal train/validation split, not a sealed external holdout. A distinct protected test set, contamination controls, metric integrity, and release authority remain the application owner's responsibility.

This also corrects a broader Step00 source note: for this pinned MIPROv2 path, omitted `valset` does not mean direct reuse of every training example as validation; the code slices the supplied trainset. The remaining risk is that this split is not an external, non-writable evaluation authority and can still reflect the same source distribution.

## Portability and evidence ceiling

The pinned code exposes model/provider adapters and separate prompt/task model parameters. That is API-level configurability, not evidence that an optimized method transfers behaviorally between providers or model versions. The v1 paper and current main snapshot are different vintages; the report's code findings are pinned to commit `2a4c921602730cb97d54b619ed65bf55cd3af8bb` and should not be projected onto every release.

The research conclusion is narrow: DSPy demonstrates declarative program compilation and metric-directed prompt/demo optimization. It does not establish recursive self-modification of the improvement procedure, cross-model cognitive-method inheritance, or an evaluator boundary that the optimized system cannot influence. Detailed evidence and paths are in `dspy-harness-optimization-crosswalk.jsonl`.
