# Research questions — IGNITION-20260918-186

## Decision-neutral questions

1. What persistent object does each system expose to inheritance: weights, data, prompt/harness, memory, skills, tool policy, evaluator, self-model, task traces, or the improvement procedure?
2. Does a system change its improvement method across episodes, or only retry, reflect, accumulate memory, optimize prompts/programs, or tune to a benchmark?
3. What primary-source evidence supports transfer across model/provider versions? Which components are model-bound?
4. Which evaluator, task set, release rule, and resource policy are outside the write authority of the candidate being evaluated?
5. What concrete write, retrieval, deletion, compression, retirement, replay, and rollback mechanisms constrain accumulation?
6. Is any profile of the system’s own capability explicitly invalidated or revalidated after behavior, model, tool, or harness changes?
7. What would separate reusable method from copied answer, traces, benchmark exposure, or task-specific skill?
8. Which exact Task181 mechanisms already cover the same boundary, and where does a bounded gap remain?
9. What is the smallest reversible experiment that can distinguish the leading explanations without model training or external integration?

## Falsification discipline

For each positive claim, record the primary source and the object it actually observes. For each negative claim, bound it to the frozen source paths and explain the search surface. Treat authors’ evaluation and mechanism statements as `PAPER_CLAIM` or `DOC_CLAIM`; treat static implementation details as `CODE_OBSERVED`; reserve `OUR_INFERENCE` for cross-system and Pointfire comparisons. Keep capability, memory, skill, method, and meta-method change as separate hypotheses.
