# IGNITION-20260930-229-R1 wrapper protocol

This is a new, separately preregistered transfer-only replication after the original Task229 operational dispatch blocker. The scientific design is inherited mechanically; this wrapper changes runtime and provenance only.

## Fixed inputs

- The 19-file source preregistration is copied byte-for-byte from formal commit `961603c2cb8b6cd1aac14ff72ecd946e26828aa5`; its original freeze manifest is preserved under `provenance/`.
- The 18 concrete prompts are copied byte-for-byte from formal commit `4ee132e8d50e8805c466cb5d681aaa18c34c9f68`. They were frozen after the original target-opening gate and before successor execution; they are not described as pre-target-opening prompts.
- The original six lineages, three conditions, 18 design session IDs, deterministic session order, response schema, missingness/retry rules, rubric, sanitization, thresholds, and `recompute.py` remain byte-frozen.
- The coordinator has historical target exposure. No post-exposure tuning is permitted. Historical Attempt-1 semantic responses are excluded from every new response, packet, evaluation, and analysis input.

## Runtime wrapper

Use the unchanged H1 exact-stdin dispatcher with local `codex-cli 0.159.2`, requesting `gpt-6-astra` and `medium`. Each invocation uses `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, `--strict-config`, a read-only sandbox, and a fresh empty workspace. Prompts travel only through subprocess stdin after exact source hash and strict UTF-8 roundtrip checks. Preserve JSONL, stderr, final message, process/thread identity, exit status, dispatch receipt, and response hashes. The CLI JSONL does not independently echo backend model or effort.

## Scientific gate

No successor session may start until this wrapper is frozen, exact-head required CI is green, the 19/19 source hashes, 18/18 prompt hashes and dispatcher hash pass, and the large-input non-scientific transport canary passes. The canary is not a scientific session. Freeze all 18 responses and their integrity before opening target scoring criteria for evaluator packet generation.

## Lifecycle

Keep the new PR Open, Draft, and unmerged. Do not modify or promote historical PR #239. Do not run revision generation, full-chain work, Ready, merge, canonical promotion, R1 generalization, cross-model work, Model-RSI, or training. After terminal results, update the 1111 receipt and wait for Owner/GPT; do not automatically start Task230.
