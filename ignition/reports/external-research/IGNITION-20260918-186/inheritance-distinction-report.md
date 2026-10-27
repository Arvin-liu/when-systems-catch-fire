# Inheritance distinctions and evidence ratings

## Five different outcomes

**Capability progress** is a measurable change in success on a declared task family under a named model, harness, and evaluator. A higher benchmark score can show performance under that protocol; it does not identify which component changed or prove that an improvement method was inherited.

**Memory inheritance** means a later run can retrieve persistent experience and use it to condition behavior. It explains continuity, not necessarily competence or truth.

**Skill inheritance** means a later task can retrieve or compose a reusable executable/procedural skill. Voyager is direct evidence within Minecraft. It is a narrower outcome than transferring a general problem-solving method.

**Method inheritance** requires evidence that a later run or successor uses a transferred procedure for selecting, creating, validating, and revising improvements. The result must be separated from transferred facts, prompts, skills, and the successor model's base capability.

**Meta-cognitive evolution** requires a change to the procedure that monitors capability, routes improvement actions, evaluates candidates, or retires methods. It also requires an evaluator the system cannot write and a predeclared measure of the procedural change itself.

The framework JSON gives the full operational definitions, rating policy, and per-system judgments. “Supported by evidence” is scoped to the paper or code cited; it does not mean independently reproduced here. “Not shown” refers only to the frozen snapshots and inspection scope.

## What the comparison supports

Several systems show bounded improvement or persistence: Reflexion reports cross-trial improvements from verbal reflection memory; Voyager reports reuse of a skill library for novel Minecraft tasks in a new world; DSPy compiles prompts and demonstrations against a caller metric; MemGPT reports long-context retrieval outcomes; SWE-agent reports execution-based benchmark outcomes after researcher-designed interface changes. These are useful mechanisms in their own scopes.

MetaRSI is the most direct architecture-level proposal for changing an improvement procedure: it separates data, harness, and model operators, and adds horizontal/vertical scheduling. Its v2 paper reports benchmark-bound results and claims this architecture. The reviewed sources do not establish a general transfer of that method to a successor model, across providers, or across domains. RSI-Harness's pinned public implementation is materially narrower than the paper and contains no benchmark, training, or evaluation loop.

The evidence supports a hierarchy of increasingly strong but non-equivalent claims:

1. A system can produce a better answer in a fixed task.
2. It can reuse stored experience or skill in later tasks.
3. A measured capability change persists under a declared setup.
4. A successor inherits the procedure that creates and validates improvements.
5. The procedure itself evolves safely under independent evaluation.

Evidence for one level does not establish the next. In particular, a stored reflection, a successful skill library, prompt compilation, long-context recall, or a public benchmark result does not by itself establish levels 4 or 5.

## Claim ceiling

For this source set, no primary paper or pinned implementation establishes general cross-model cognitive-method inheritance. MetaRSI proposes the closest method-evolution architecture, while the other systems mostly demonstrate task-level answer refinement, memory continuity, skill reuse, program/harness optimization, or benchmark measurement. This conclusion is a scoped literature/code finding, not a claim that such inheritance is impossible.

Primary sources include [MetaRSI v2](https://arxiv.org/html/2609.06396v2), [Reflexion v4](https://arxiv.org/html/2303.11366v4), [Self-Refine v2](https://arxiv.org/html/2303.17651v2), [Voyager v2](https://arxiv.org/html/2305.16291v2), [DSPy v1](https://arxiv.org/html/2310.03714v1), [Generative Agents v2](https://arxiv.org/html/2304.03442v2), [MemGPT v2](https://arxiv.org/html/2310.08560v2), [SWE-agent v3](https://arxiv.org/html/2405.15793v3), and [AgentBench v3](https://arxiv.org/html/2308.03688v3). Code/document details are in the prior numbered artifacts and `source-freeze.jsonl`.
