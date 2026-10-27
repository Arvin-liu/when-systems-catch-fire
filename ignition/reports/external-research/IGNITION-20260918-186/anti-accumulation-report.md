# Anti-accumulation mechanisms and their limits

## Four different controls

A **size cap** limits active storage or prompt growth. Reflexion's last-three-reflections setting, Letta Code's character/depth constraints, Pointfire's budgets, and bounded context capsules are examples. They do not identify which content is true or worth retaining.

A **retrieval policy** changes which stored items are likely to be shown. Generative Agents uses recency alongside relevance and importance. Older material can become less visible without being removed.

A **compression/eviction policy** changes the active context representation. MemGPT summarizes an evicted queue while retaining the original messages in recall storage. Letta Code's local compaction summarizes conversation context for continued interaction. These operations do not by themselves reduce the durable memory store.

A **retirement/deletion policy** decides that an item should no longer be active. Letta Code exposes explicit patch operations including deletion, with reason, validation, commit history, and bounded structural constraints. Pointfire has typed forget/expire tombstones and supersession. MetaRSI's v2 paper claims semantic consolidation, deduplication, complexity control, and removal of harness scaffolding after internalization, but the reviewed public RSI-Harness code does not implement that full mechanism.

## What external systems show

- Reflexion bounds the prompt-visible reflection buffer in the cited AlfWorld experiment; this is last-N retention, not semantic pruning.
- Voyager replaces an active skill on duplicate name and saves prior code under a versioned filename. This prevents duplicate active names but preserves old files and does not validate whether the replacement is better.
- Generative Agents' recency-weighted retrieval and `expiration` field are not proof of expiration or deletion. The inspected code path can store `None`.
- MemGPT's queue can shrink while its recall database retains the evicted messages indefinitely, according to the paper.
- Letta Code combines explicit mutation with Git history and size/depth caps. The inspected paths do not show automatic semantic deduplication or a TTL for capability claims.
- DSPy can select a candidate prompt/demo program using the caller metric. Candidate selection is not general knowledge retirement or recursive method evolution.
- Pointfire already supports typed expiry/forget/supersession and bounded context output. The Task181 source does not establish semantic deletion for a skill or improvement procedure.

The operational lesson is to report active-context size, durable-store size, retrieval likelihood, and retirement state separately. A record can be old yet useful, recent yet false, summarized yet still stored, or deleted from retrieval while retained in history. Any future retirement study would need provenance, an explicit evaluator, reversible state, and a predeclared failure condition; this task only documents candidates and does not run them.

Rows and exact pinned locators are in `anti-accumulation-mechanisms.jsonl`. See [MetaRSI v2](https://arxiv.org/html/2609.06396v2), [Reflexion v4](https://arxiv.org/html/2303.11366v4), [Generative Agents v2](https://arxiv.org/html/2304.03442v2), [MemGPT v2](https://arxiv.org/html/2310.08560v2), and the pinned [Letta Code memory patch](https://github.com/letta-ai/letta-code/blob/7e3689268908a7e14a61f0805b48e193a5bcecd8/src/tools/impl/memory-apply-patch.ts), [memory constraints](https://github.com/letta-ai/letta-code/blob/7e3689268908a7e14a61f0805b48e193a5bcecd8/src/agent/memory-constraints.ts), [Voyager skill manager](https://github.com/MineDojo/Voyager/blob/55e45a880755d0c8c66ca7fb5fe7962ac8974f89/voyager/agents/skill.py), and Task181 [Pointfire R2 runtime](https://github.com/Arvin-liu/when-systems-catch-fire/blob/7cab7541895620d68d5bce2d16c46871ebd03ac0/ignition/agent_runtime/README.md).
