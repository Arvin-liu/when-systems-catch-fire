# Reflexion and Self-Refine crosswalk

## Reflexion: feedback memory across trials

Reflexion converts task feedback into text that conditions later actions without updating model weights. The paper distinguishes recent trajectory context from long-term verbal reflections. It usually bounds the reflection buffer to one to three experiences. Its Evaluator may be exact match, a hand-written task heuristic, generated tests, or an LLM instance. The paper acknowledges that self-evaluation and heuristics do not provide a formal guarantee. In coding, the authors also report that generated tests can produce false positives or false negatives.

The pinned programming runner keeps `reflections`, implementations, and feedback local to each dataset item, retries under explicit iteration/pass bounds, and writes per-item logs. That supports task-level error learning and an episodic memory mechanism. The inspected path does not revise the actor's improvement procedure, evaluator, or method artifact across tasks or models.

## Self-Refine: output feedback inside one task

Self-Refine uses one model for initial generation, feedback, and refinement. It keeps the draft and feedback history within an input-specific loop, then returns the refined output. The paper evaluates the procedure across seven generation tasks and uses external human/automatic research evaluation, but those measurements are not the same as the run-time same-model feedback step. A task's answer can change; the paper does not show the feedback/refinement procedure itself being inherited or revised across tasks.

## Answer revision versus method revision

The distinction is not whether a system improves a result. Both systems can improve results, and Reflexion explicitly lets a bounded reflection memory change later behavior. The distinction is whether the system leaves behind and independently validates a durable change to how it selects evidence, diagnoses failures, chooses a verifier, or revises its own improvement method. The inspected sources do not establish that stronger claim. They support output-level revision and, for Reflexion, within-task episodic memory; they do not establish general cognitive-method inheritance or cross-provider transfer.

Full evidence, source locators, and scope limits are recorded in `reflection-family-crosswalk.jsonl`.
