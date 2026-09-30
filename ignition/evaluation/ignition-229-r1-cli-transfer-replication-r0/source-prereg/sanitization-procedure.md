# Blind packet sanitization R0

Sanitization runs after all raw session responses are frozen and before either evaluator receives any packet. The sanitizer must not read or use the condition-to-lineage map.

1. Create a distinct opaque response ID for each session-case pair. Keep the response-ID mapping only in the coordinator ledger.
2. Pair each response with only its matching frozen case bytes and the frozen scoring criteria.
3. Remove the complete `route_trace` object, since it is interface evidence and contains policy/rule/action/input identifiers. Remove any provenance, builder, tool, file-path, source-locator, artifact-ID, session-ID, policy-ID, lineage-ID, bundle-ID, and condition-name fields.
4. In remaining text fields, replace exact known identifiers and source-locator tokens with `[REDACTED]`. Do not rewrite, summarize, reorder, or normalize the primary action, additional actions, reported values, preserved baseline action IDs, fallback, scope, or rationale.
5. Mechanically compare the scored fields before and after sanitization. If a primary action, value, preserved baseline action, fallback, scope, or case-relevant rationale changes beyond removal of a listed identifier token, stop packet preparation. Do not rescore or repair the raw output.
6. Scan each completed packet for every condition label, policy ID, lineage ID, session ID, bundle ID, source locator, and repository/file path. Require zero matches before delivery. Store scan counts and hashes.
7. Independently randomize packet order for evaluator A and evaluator B. Evaluators receive no condition map, method material, policy file, raw trace, session order, Task228 audit outcome, or other evaluator sheet.

The raw session response is immutable. Sanitization creates derived packets only; it never edits raw records.
