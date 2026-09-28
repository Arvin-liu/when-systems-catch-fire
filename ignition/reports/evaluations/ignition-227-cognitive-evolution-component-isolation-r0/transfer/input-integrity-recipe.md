# Transfer byte-integrity and opaque bundle recipe

After reference policy validity is locked, coordinator copies each frozen FAMILY01/02/03 case A/B/C byte-for-byte into every one of the six lineage × three condition bundles. Compute and retain SHA-256 for all 54 materialized case files; within each family, the three case hashes must be identical across all six lineages and all three conditions. Only method material differs by condition. Keep hashes in the private orchestration ledger until evaluator sheets lock.

Each of the 18 trials receives a cryptographically random opaque ID unrelated to family, lineage, or condition. The successor input contains only case filenames, permitted method files, neutral prompt, and response schema. Do not pass manifests, condition names, parent repository, shell access, or coordinator notes. The response is one JSON object. Do not ask for or retain source-file names, locator tokens, artifact IDs, or evidence citation strings in responses. Keep raw session logs and returned bytes immutable; no retry or repair. A failed/missing invocation stays in the denominator and receives false raw endpoints.

Blind coordinator produces evaluator packets with new randomized response IDs, removes filenames and condition-revealing metadata, and deterministically sanitizes response text without looking at the condition map:
1. remove any evidence-provenance fields if present;
2. replace source locator tokens and artifact/file IDs with a single neutral marker;
3. replace explicit condition or bundle names, policy IDs, lineage IDs, and builder IDs with a neutral marker;
4. retain scored action, action order, values, preserved baseline, fallback, scope, and rationale content otherwise unchanged;
5. scan the completed packet for any remaining locator/condition/lineage tokens and record zero matches before delivery.

If sanitization would alter an action, value, or case-relevant rationale beyond the listed tokens, stop packet preparation and flag the issue to the study lead without rescoring or changing the raw output. Evaluators receive the visible case, sealed target, criteria, and sanitized response, one opaque response per item; they do not receive the map, method files, condition names, lineage, or sibling responses. The coordinator is not a scorer. Keep the condition map sealed until both complete evaluator sheets are locked.
