# Independent evaluation: what the sources do and do not separate

## Evaluation boundaries are different kinds of evidence

The MetaRSI paper provides the strongest proposed release architecture in this review: operator write surfaces are separated from an Anchor, held-out task set, release rule, and resource ledger. But for generated-data evaluation, it explicitly uses the same target model for Operator and blind Anchor roles, with input isolation. The paper's architecture distinguishes roles and writable surfaces; it does not establish an independent model identity for every evaluator path. This report does not reproduce the paper's evaluator or results.

Reflexion makes its reward path configurable by task. It reports exact-match evaluation for reasoning, hand-written heuristics for decision tasks, and a separate LLM instantiation for some Evaluator roles. Its self-reflection is a model-written memory update. In the AlfWorld setting it also reports heuristic/LLM self-evaluation and retains a bounded number of reflections. These are concrete choices, but they do not amount to a single sealed general-purpose authority.

Self-Refine's generation-feedback-refinement loop uses one model. Its paper separately reports a blinded human A/B comparison of outputs. Keeping those two layers distinct matters: the experiment uses human judgments as an outcome comparison, while the operating loop remains model-generated feedback. It does not test an inheriting model's evaluation method.

Voyager combines environment feedback with a model critic. The pinned default has the action and critic agents configured to GPT-4, while a human mode is an available option. Minecraft world state can check whether an in-domain task completed; a critic prompt cannot by itself validate a domain-neutral method. DSPy exposes a caller-provided metric and validation set. In the pinned MIPROv2 path, omitting `valset` splits the supplied trainset internally. This is useful candidate selection, but it does not establish an external holdout that the application cannot influence.

## Public benchmarks can be rigorous without being secret

AgentBench v0.2 offers Dev and Test splits, releases full data for both, and publishes test scores. The paper presents eight environments and test results. The benchmark supports repeatable task comparison, but public test data/results should not be described as a confidential holdout. The paper also reports human validation of its lateral-thinking-puzzle host and identifies metrics where automated judging was more tolerant than humans. That evidence is specific to those metrics, not a universal evaluator.

SWE-agent gives a useful positive evaluation pattern: interface search and tuning used a subset of the Dev split; final results were measured on the Test split with execution-based human-written unit tests. That makes outcome checks less dependent on the acting model's self-assessment. The benchmark data are released, however, and a benchmark result is still task/domain-specific. It is not evidence that a later model inherited a general improvement method.

## Implication for a candidate successor evaluation

A sound design must state what can write or inspect each data partition, who defines and runs the evaluator, whether the acting model and evaluator share a model/provider, which results are public, and what evidence authorizes a candidate transition. An environment checker, an LLM judge, a human audit, a public test split, and a protected release gate contribute different evidence. Results must not be promoted across these categories without an explicit protocol.

At Task181's pinned base, Pointfire's evaluation contract already types evidence and limits transitions to candidates; its claim-governance contract keeps candidate admission separate from accepted truth. Task186 inspected only those safe contracts. It did not run Successor/Evaluator, touch held-out payloads, or make any transition.

Detailed rows and fixed source IDs are in `independent-evaluation-external-map.jsonl` and `source-freeze.jsonl`. Primary locators: [MetaRSI v2](https://arxiv.org/html/2609.06396v2), [Reflexion v4](https://arxiv.org/html/2303.11366v4), [Self-Refine v2](https://arxiv.org/html/2303.17651v2), [AgentBench v3 paper](https://arxiv.org/html/2308.03688v3), [AgentBench v0.2 README](https://github.com/THUDM/AgentBench/blob/ed013ff9887b0c3d7864c56ae54d41eba54a99d8/README.md), [SWE-agent v3 paper](https://arxiv.org/html/2405.15793v3), [DSPy pinned MIPROv2 code](https://github.com/stanfordnlp/dspy/blob/2a4c921602730cb97d54b619ed65bf55cd3af8bb/dspy/teleprompt/mipro_optimizer_v2.py), and the [Task181 Pointfire evaluation contract](https://github.com/Arvin-liu/when-systems-catch-fire/blob/7cab7541895620d68d5bce2d16c46871ebd03ac0/ignition/evaluation/evaluation-plane-contract-r0.1.json).
