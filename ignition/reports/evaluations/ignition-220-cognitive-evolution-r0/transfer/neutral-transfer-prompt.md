# Neutral transfer prompt — Task220 R0

You are given three held-out case records and a bounded set of method and/or source evidence. Use only the files assigned to this conversation. Apply the supplied method material to each case independently.

For each case, return the externally visible action or disposition, the scope and preconditions that govern it, any required discriminating observation or stop condition, and the remaining uncertainty. Do not claim that an action was executed or that an outcome was observed unless the supplied record establishes it. Do not invent sources or measurements.

If the case is unresolved, state what is missing and the specific measurement or reconciliation needed. Do not respond with blanket refusal where the supplied method and case support a bounded action. Do not expose hidden chain-of-thought; provide only the structured fields in the output schema.

Return exactly one JSON object with one record for each assigned case, in the case order given in the input manifest. Do not add prose outside the object. Do not browse other repository paths, inspect sealed targets, look for scoring criteria, contact another agent, or see sibling outputs.
