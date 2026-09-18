# Voyager skill inheritance report

## What is inherited

Voyager stores executable JavaScript functions that perform multi-step Minecraft behaviors. It indexes descriptions with embeddings, retrieves up to five relevant skills, and includes those programs with Mineflayer control primitives when generating new code. The automatic curriculum uses current world state plus completed/failed tasks; the iterative prompting loop observes execution, uses interpreter errors and critique, and commits a skill after the critic reports success. The paper reports that a stored library helps in a new Minecraft world on novel tasks.

This is strong evidence for skill inheritance inside a defined environment. It is more persistent than a single-task answer revision: a programmatic behavior can be retrieved and composed later. It is still a set of Minecraft/Mineflayer-bound behaviors. It does not show inheritance of a domain-neutral method for identifying objects, preserving uncertainty, choosing evaluators, or revising the method that produces skills.

## Retrieval and evaluation boundary

At the pinned code snapshot, `SkillManager` persists `skills.json`, code/description files, and a Chroma vector store. It checks store consistency on resume, generates descriptions, and retrieves top-k skills. `CriticAgent` is a separately prompted object, but the paper and default code configure ActionAgent and CriticAgent to GPT-4; separate role or instance does not prove a separate model or independent source of truth. The paper itself uses model-based self-verification rather than a task-specific external oracle.

## Failure memory, retirement, and lock-in

The curriculum's completed/failed-task lists persist and feed later task selection. A duplicate skill name causes a concrete replacement: the active vector entry is deleted and the in-memory skill is overwritten, while the prior code is saved under a versioned filename. The inspected path does not show replay-gated retirement, semantic deletion, stale skill invalidation after API changes, or a method for pruning the overall library. This replacement behavior is distinct from an anti-accumulation policy.

The model/provider and action API are coupled to GPT/OpenAI-compatible calls and Minecraft/Mineflayer semantics in the frozen implementation. The paper's new-world result is useful evidence for in-domain reuse; cross-model, cross-provider, cross-domain, and general cognitive-method inheritance remain unshown.

Evidence and exact source paths are listed in `skill-inheritance-crosswalk.jsonl` and `source-freeze.jsonl`. No external code was run.
