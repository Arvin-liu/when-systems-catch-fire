# Fixed visible prompt for each successor session

You are handling one fresh, isolated case-solving session. Use only the case files and method material included in this message. Do not use tools, browse, inspect a workspace, request other records, infer an unstated threshold, or refer to another session. Do not mention any study, condition, lineage, evaluator, or other session.

For each supplied case A, B, and C, return the requested machine-readable fields. Preserve the available baseline action IDs. If the supplied method material contains a route policy with a `policy_id`, execute that policy as written and include a `route_trace` for every case: the exact supplied `policy_id`, selected route type (`selector`, `fallback`, or `stop`), selected rule ID and action ID when applicable, the case input IDs used in routing, and the preserved baseline action IDs still available. For a selector, cite the matching selector rule and its action reference. For a stop, cite the stop ID as the selected rule and use a null action ID. For fallback, use null selected rule and action IDs. Do not invent IDs. If no route policy is present, omit `route_trace`.

Return exactly one JSON object matching the supplied response schema and nothing else. Do not include markdown fences or commentary.

## Session inputs

### Method material

{{METHOD_MATERIAL}}

### Case A

{{CASE_A}}

### Case B

{{CASE_B}}

### Case C

{{CASE_C}}

### Response schema

{{RESPONSE_SCHEMA}}
