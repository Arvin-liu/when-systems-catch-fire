# R0.4 Method Contract

Produce one bounded response for each case in the packet manifest using only the listed cognitive evidence and provider-neutral reasoning capabilities.

For each case:

- distinguish recorded observations from interpretations;
- keep plausible relationships separate from established facts;
- identify unknowns and source limits;
- state what additional evidence would support a stronger claim;
- preserve multiple interpretations when the source does not resolve them.

The case source and its provenance are authorized cognitive evidence. Reading a case may expose case-specific information; that is expected and is not contamination when the allowlisted path and digest match. `CASE_SPECIFIC_INFORMATION_EXPOSED_IS_CHANNEL_CONTEXT_NOT_CONTAMINATION_BY_ITSELF`.

Do not invent missing observations, convert a status-only tool result into case evidence, or infer deployment or causation merely because a change was requested or acknowledged. Do not search for related real-world data.

Record every cognitive read and its SHA256 in the R0.4 read ledger. Record each pre-closure operational execution and finite status observation there as well. Operational/control channels must not expose case-specific information; if they do, the row is `CONTAMINATED` and normal work stops.

This contract is a response method, not an answer key or evaluator rubric. It does not define expected relations, preferred continuation, scoring criteria, or an inheritance threshold.
