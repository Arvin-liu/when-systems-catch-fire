# Neutral revision prompt R0.1

Using only the assigned family's frozen M0 method, E1 evidence packet, and the revision schema, produce a bounded candidate M1 operational policy that resolves the observed method limitation while preserving validated M0 rules.

Requirements:

- Treat M0 as the baseline; state which rule remains valid and when it remains applicable.
- Use only selectors and relations directly supported by the assigned E1 packet.
- State selector inputs, exact bounded applicability, action mapping, preserved M0 rule IDs, unresolved/fallback behavior, stop conditions, evidence provenance, and scope ceiling.
- Keep the output operational: a reader should be able to determine when to use the added step and what to do outside its evidence envelope.
- Do not invent universal cutoffs, formulas, thresholds, causal claims, or outcome claims not established by E1.
- Do not infer any held-out case, transfer target, condition label, scoring criterion, or disposition threshold.
- Do not refer to sibling lineages, other families, prior Task225 candidates, or experimental outputs.
- Return one JSON object conforming exactly to the assigned revision schema; no prose before or after the JSON.
