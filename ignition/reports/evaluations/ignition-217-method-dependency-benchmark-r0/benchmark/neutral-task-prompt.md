# Case review task

You are given a packet containing six synthetic operational cases and an output schema. For every case, determine the strongest action or disposition supported by the provided records.

Separate directly recorded observations from inferences and hypotheses. Record material unknowns, applicable boundaries, prerequisites, and a stop condition. Do not state that an action occurred unless the packet records it. If the record does not distinguish among plausible explanations or actions, preserve that uncertainty and name the specific observation or check that would resolve it. Keep conclusions scoped to the population and conditions actually described.

Use only source locators present in the packet. Support factual and relational statements with their source locator or locators; identify a relation as inferred when the records do not explicitly state it. Do not turn a missing record into evidence that an event did or did not occur.

Return only a JSON array of exactly six objects, one for each case_id shown in the packet. Each array element must conform to the supplied output schema. Copy that case's displayed Source SHA-256 value into source_sha256. Use the case_id exactly as shown.
