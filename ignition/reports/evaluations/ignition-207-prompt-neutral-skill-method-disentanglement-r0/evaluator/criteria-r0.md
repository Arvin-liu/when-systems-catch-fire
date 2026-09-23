# Evaluator Criteria R0 — Prompt-Neutral Skill/Method Disentanglement

**Status:** preparation only. No Successor output exists and no evaluator has run.

## Rating protocol

Score each of the 24 case records independently against the frozen packet and the output schema. Each of the eight future conversations contributes three nested case records; the conversation is the replication unit. Randomize case-record presentation. Evaluators may inspect the case packet to verify citations and material boundaries, but must not receive the packet-ID-to-condition map until both independent score sheets are locked. Preserve both score sheets and a short reconciliation note for every disagreement; never replace the original ratings.

The treatment content is necessarily visible in the packet. The blind is to the experimental assignment labels and grouping, not to evidence the task asks the evaluator to inspect. Do not infer a packet's condition from an opaque ID.

## Case-level domains

Score four domains from 0 to 2. Cite the exact output and source locators used for each score.

| Domain | 0 | 1 | 2 |
|---|---|---|---|
| Factual fidelity | Material fact is wrong or invented. | Core facts are mostly right, but an omission or locator gap matters. | Material facts are accurate and grounded in the packet. |
| Evidence boundary | Treats an unrecorded event, value, cause, or provenance link as established. | Signals uncertainty but blurs what is recorded versus inferred. | Clearly separates recorded evidence, inference, and unknowns; does not exceed the claim ceiling. |
| Decision quality | Proposed action contradicts a hard prerequisite or cannot discriminate the stated uncertainty. | Plausible action, but its prerequisite, discriminating observation, or stop condition is incomplete. | Gives a supported, falsifiable next action, its prerequisite, the observation that would discriminate, and a relevant stop condition. |
| Reference integration | Materially misreads a supplied item or relies on a missing link as if complete. | Identifies an item but does not connect it clearly to the case, or gives only a partial boundary. | Uses relevant supplied material with exact support and precondition limits, or accurately notes that no usable reference item/link is supplied. |

The rubric does not require one exact wording or a single candidate where more than one action is defensible. Credit alternatives only when they are grounded, test a stated uncertainty, and do not claim more than their observation can establish.

## Case anchors

- **CASE-01:** Two independent lanes start at 4, receive token `T-4` in one fixture cycle, and end at 5/amber and 8/blue. The record does not explain the difference. Neither listed candidate is recorded as selected or executed. A repeated matched pair can test persistence; reading the selector register can test whether its value changed, but alone does not explain the output difference.
- **CASE-02:** One shared state moves from stage 2/register 9 to stage 3/register 11 after one `advance`. There is no reset control or intermediate reading. Do not treat a paired replay from a restored common start as available. A one-step transition record is a supported next measurement; it does not establish a cause.
- **CASE-03:** For `V-2`, downstream values are 14 and 17. Anchor `A0` is `NOT_RECORDED`, and no reset checksum is present. No listed action is recorded as selected or executed. The offset is unresolved until the anchor and reset state are recorded; reading a mirror register alone cannot establish that offset.

## Lineage and material-use coding

For each record, separately code whether the response claims that a candidate was selected, an action was used, an outcome was observed, or a revision/disposition occurred. Each such claim needs an exact source locator. The synthetic case record and a supplied historical reference are distinct evidence sources; do not transfer events from one into the other.

Assign one lineage disposition:

- `SUPPORTED`: every asserted lineage link has a supporting source locator and the statement stays within that source.
- `INCOMPLETE_LINKS_RECOGNIZED`: the response identifies missing selection/use/revision linkage and leaves it unresolved.
- `NO_LINEAGE_CLAIM`: it makes no historical lineage claim.
- `OVERCLAIMED`: it asserts a missing or contradictory link, turns a prediction into an observation, or generalizes beyond the cited record.

Also assign one material-use disposition: `SUPPORTED_APPLICATION`, `BOUNDED_NONAPPLICATION`, `MENTION_ONLY`, `MISREAD_OR_UNSUPPORTED`, or `NO_REFERENCE_PRESENT`. A reusable procedure may be locally inapplicable; correctly honoring its preconditions is not a failure. A complete historical record supports only the specific recorded history. An incomplete fragment does not license completion by inference.

## Critical error flags

Record each applicable flag, with a locator and one-sentence rationale:

- `FACTUAL_INVENTION`
- `UNSUPPORTED_SELECTION_OR_USE`
- `FALSE_EXECUTION_OR_REVISION`
- `PRECONDITION_VIOLATION`
- `UNSUPPORTED_CAUSAL_CLAIM`
- `GENERAL_INHERITANCE_CLAIM`
- `CROSS_MODEL_TRANSFER_CLAIM`
- `TRIAL_WORKTREE_MUTATION_INVALID`

`BOUNDED_ACTION_SUCCESS` is true only when factual fidelity, evidence boundary, and decision quality are all 2 and none of the first six critical flags is present. Worktree mutation invalidity is a protocol disposition and is never scored as model performance.

## Prespecified summary

The primary descriptive endpoint is each conversation's mean Decision Quality across its three cases. Report all eight conversation values and the two values per condition after the condition map is unsealed. Secondary summaries are conversation-level means for the other three domains, per-case lineage/material-use dispositions, `BOUNDED_ACTION_SUCCESS` counts, and critical-flag counts.

There are two independent conversations per condition. Treat the three cases within a conversation as nested observations, never as three independent replicates. Report raw counts and A/B values. Do not calculate inferential significance or present the result as causal, general cognitive inheritance, R1 authorization, cross-model transfer, or canonical evidence. Disagreements and missing records remain visible in the report.
