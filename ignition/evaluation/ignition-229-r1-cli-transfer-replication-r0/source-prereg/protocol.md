# Task229 preregistered protocol R0

## Scope and frozen anchors

This is a transfer-only experiment with six frozen Task228 reference instruments. It does not run revision generation or the full chain.

- Task227 PR #237 exact head: `7d979b1aa523030b16f773a973477cbfca1e4513` (OPEN, DRAFT, UNMERGED).
- Task228 PR #238 exact head: `d82a52077df6d4e96e998ace3757f2fb343b4db5` (OPEN, DRAFT, UNMERGED).
- Task228 checksum-manifest SHA-256: `864c4b91dc12b7f3166d1f0101b8e4dc300551fd4e83f28bb9e1be96a0312538`.
- Task228 candidate-build manifest SHA-256: `dc679675af1401a3b4c7c816bcded9e7485dbf49f109d3e08f757011f21eb484`.
- Task225 frozen case/target/evaluator manifest SHA-256: `f6201ea25d3614af34ef05d36cc8f620a8c149902fcef8937d259445b0b302a8`.
- Task227 frozen transfer evaluator manifest SHA-256: `91a33c38f209b88644ef473c21a133463bf7839d1bd5afc9c1507b88d128b7ec`.

All six policy files are bound by byte SHA-256 in `condition-manifest.json`. Task227's A/B/C case files and sealed targets remain unopened until the target-opening gate passes.

## Experimental units and conditions

The six fixed lineages are the six Task228 policies, two per family. Every lineage has one fresh isolated session in each condition:

1. `M0_ONLY`: family M0 only; no raw E1 and no reference policy.
2. `M0_PLUS_E1`: family M0 and raw E1; no reference policy. This condition is descriptive only.
3. `REFERENCE_M1`: family M0 and that lineage's exact frozen Task228 policy; raw E1 is not supplied separately.

This yields 18 fresh sessions. Within each family, the same frozen A/B/C case bytes are supplied in each of the three conditions. A session receives only its own cases and method inputs. No session receives a condition name, lineage ID, manifest, sibling output, evaluator criteria, or target outcome. No session may reuse another session's conversation.

The mapping of opaque session IDs to lineages and conditions is recorded only in the coordinator manifest. The deterministic execution order is fixed in `session-order.json` before the first session.

## Fixed successor environment

The experiment uses the same declared runtime and visible prompt for all 18 sessions:

- Provider/runtime: OpenAI Codex collaboration-agent runtime.
- Model: `gpt-6-astra`.
- Reasoning effort: `medium`.
- Temperature/sampling settings: not exposed by the session tool.
- System-prompt control: the platform-managed outer system message is not exposed; the identical study prompt in `session-prompt-template.md` is supplied to every session.
- Tool surface: inherited Codex tools are available in every session; the study prompt prohibits tool use and supplies all required material in-message. No tool use is part of the experimental interface.
- Response schema: `task229-successor-output-r0`.

The fixed analysis runtime is Python 3 with `jsonschema` 4.25.1. The exact interpreter and validator versions are recorded by the preregistration validator before freeze. Route verification uses the supplied case input IDs and values captured in the run record after the target-opening gate; no policy or routing logic may be changed in response to target content.

If this model/runtime or the fixed session tool becomes unavailable, stop. Do not substitute a model, reasoning effort, tool path, or configuration mid-run.

## Response interface

Every session returns exactly one JSON object satisfying `response-schema.json`, with exactly one response each for cases A, B, and C. The common envelope contains the primary action, additional actions, reported values, preserved baseline action IDs, fallback, scope, and rationale.

When a supplied method file contains a route policy with a `policy_id`, every case response also contains a `route_trace` with the supplied policy ID, route type, rule/action IDs when selected, cited input IDs, and preserved baseline action IDs. When no route policy is supplied, `route_trace` is omitted. The trace is interface evidence, not target success.

No commentary may surround the JSON object. A semantic response that is malformed, schema-invalid, refused, or substantively incomplete is preserved as received and is not retried.

For each case, the coordinator's analysis input records the frozen case's supplied input values as an object keyed by input ID. The successor's `route_trace.input_ids` must cite only IDs present for that case. The frozen recomputation code resolves stop conditions first, then matching selector rules, then fallback; it checks the reported route, rule, action, policy ID, and preserved baseline action IDs against those values and the exact supplied policy bytes.

## Retry rule

One replacement attempt is allowed only for a documented transport or infrastructure failure before any model response exists. Preserve both the failed transport event and replacement metadata. No replacement is allowed for a refusal, invalid schema, malformed semantic output, wrong trace, or case failure. Such outcomes remain in the denominator.

## Blind evaluation

After all 18 raw outputs are frozen, the coordinator sanitizes them using `sanitization-procedure.md` without using the condition map. Two independent evaluators each score all A/B/C dimensions for all 18 sessions using the pinned Task225 R0.1 criteria and the frozen Task227 transfer scoring contract. Each evaluator receives a separately randomized packet order and opaque response IDs. Evaluators do not receive condition names, policies, policy traces, lineages, session order, Task228 audit outcomes, or the other evaluator's scores. There is no reconciliation and no third evaluator. Missing or invalid evaluator rows score false and remain raw.

## Terminal invariants

- Do not edit or regenerate Task227/Task228 frozen assets.
- Do not synthesize, repair, rewrite, or re-author any policy.
- Do not change prompts, thresholds, policies, scoring, order, model, effort, or routing after target opening.
- Do not run revision generation, full-chain R0.2, R1, cross-model, Model-RSI, or training.
- Keep PR #238 and Task229 OPEN + DRAFT + UNMERGED. Do not Ready, merge, or promote canonical/current.
- Preserve all raw session/evaluator records immutably and hash them.

The deterministic recomputation input contract is `analysis-input-schema.json`. Raw successor response files remain one file per session. Evaluator score files retain opaque response IDs, and each evaluator has a separate response-key file held only by the coordinator. Missing, invalid, duplicate, or unknown score rows never become successes.
