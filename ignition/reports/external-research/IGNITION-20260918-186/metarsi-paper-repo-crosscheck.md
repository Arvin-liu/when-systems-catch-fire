# MetaRSI paper/repository cross-check

## Frozen targets

- Paper: [arXiv v2](https://arxiv.org/html/2609.06396v2), version `2609.06396v2`.
- Official software: [RSI-Harness commit 33c4f8d](https://github.com/CosmosMind-ai/RSI-Harness/commit/33c4f8dfac4359987f2e814e187de67c332498de).
- Official artifact metadata: [Hugging Face snapshot a861001](https://huggingface.co/CosmosMind/RSI-Harness/tree/a861001d54c456e9b7eabc57a40296cd4e3b0205).

## Findings

The frozen code implements an RSIH/Pi harness with configurable, versionable Genomes. A Genome can describe prompts, skills, tools, MCP integrations, extensions, runtime policies, memory, and settings. The `harness-rsi` Genome reads user-selected session history through a bounded extension, has the agent classify recurring patterns, presents the proposed Genome plan, and waits for user confirmation before writing. The extension itself has three tools and no model calls; the authoring policy resides in the Genome's instructions and skill files.

This gives the repo an executable Harness configuration and user-gated harness-authoring path. It does not expose the paper's unified D/H/weight loop, Data-RSI dataset synthesis, Model-RSI trainer, transition adapters, horizontal operator scheduler, vertical policy rewrite, protected benchmark evaluator, sealed holdout, release gate, or end-to-end cost ledger. The README itself says no benchmark, data-generation, training, or evaluation code is included. HF metadata has no weights. The paper's five-slot contract is therefore a framework claim; the released repo provides a narrower Genome/configuration system.

| Paper mechanism | Pinned repository finding | Status |
| --- | --- | --- |
| Shared D/H/θ system and loop kernel | No three-surface kernel found; repo is the harness runtime/config layer | `PAPER_ONLY` |
| Data-RSI and verified data pipeline | No generation/training/evaluation path found | `PAPER_ONLY` |
| Harness-RSI | Genomes and the user-approved GEE session-history authoring flow exist; paper's evaluation/promotion path does not | `PARTIALLY_IMPLEMENTED` |
| Model-RSI | README says no training code; HF snapshot has no model weights | `PAPER_ONLY` |
| Horizontal/vertical/meta scheduler | No operator scheduler or method-policy update loop found | `PAPER_ONLY` |
| GEE Genome generator | Documented and represented in the repo, but not a distinct mechanism in the paper contract | `REPO_ONLY` |
| Sealed evaluator/release boundary | No benchmark/evaluation code or strict-improvement release gate found | `PAPER_ONLY` |
| Replay-checked subtraction/rollback | No such executable path found in inspected files | `NOT_FOUND` |
| Cross-model method inheritance | Config portability is described; no cross-model behavioral evaluation is supplied | `AMBIGUOUS` |

Full mechanism records, including file paths and negative-result boundaries, are in `metarsi-paper-repo-crosscheck.jsonl`.

## Important separation

The paper says generated-record Operator and blind Anchor roles use the same target model with input isolation. This prevents the proposed answer from being passed directly to the blind re-derivation in the described design; it does not give distinct model identity or independent error sources. In contrast, the paper separately claims a protected evaluation layer and release gate. The public RSIH repository does not implement or reproduce that evaluation boundary.

Static inspection was limited to the paths pinned in `source-freeze.jsonl`. No build, runtime generation, private session scan, model training, benchmark run, or integration was performed. `NOT_FOUND` and `AMBIGUOUS` are source-bounded findings.
