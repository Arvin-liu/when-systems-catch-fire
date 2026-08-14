# Mechanism Adjudication Plane

Status: `121Q12_OPERATION_OVERLAY`

The Mechanism Adjudication Plane constrains what the project may say after an action, test, failure, or external response. It does not replace proof, empirical study, or the L0-L6 architecture.

## Question Form

The plane does not begin with:

- is this good or bad;
- is this success or failure;
- is this a breakthrough;
- did AI make the user stronger or weaker.

It begins with:

- which variables or components changed;
- through which path did the change occur;
- which events merely co-occurred;
- which variables may mediate or moderate the effect;
- which boundary conditions matter;
- which alternative mechanisms remain plausible;
- which tests could distinguish those mechanisms.

Value judgment remains necessary, but it is recorded separately from the factual and mechanism chain.

## M0 / M1 Review

### M0: Pre-action Mechanism Sketch

Before an action, record:

- phenomenon and question;
- candidate mechanism paths;
- expected observations;
- strongest alternative mechanisms;
- counterfactuals;
- distinguishing tests;
- results that would downgrade or falsify the current explanation.

M0 prevents a task from retrofitting its mechanism after seeing the result.

### M1: Post-action Mechanism Adjudication

After observation and validation, record:

- what actually changed;
- which candidate path was supported;
- which path was not supported;
- which result is only an implementation pass;
- which conclusion cannot be upgraded to a mechanism claim;
- the claim ceiling and downgrade conditions.

M1 may leave the result at `implementation_observed`, `workflow_passed`, `mechanism_plausible`, or `pending`. It must not upgrade a claim merely because the task felt successful.

## Claim Ceiling

The claim ceiling is the strongest statement currently warranted by the evidence mix. Examples:

- `artifact_created`
- `schema_validated`
- `workflow_passed`
- `implementation_observed`
- `mechanism_plausible`
- `mechanism_discriminated`
- `causal_identification_pending`
- `insufficient_evidence`

The ceiling must bind object, criterion, version, test, and boundary. A higher ceiling requires a discriminating test or stronger evidence, not better wording.

## Stance-Blind Review

Reviewer inputs should normally include only:

- artifact;
- claim;
- evidence;
- mechanism map;
- failure conditions.

They should not include the proponent's excitement, expected conclusion, or emotional framing. This is separation of review input, not deception: necessary provenance and context remain available in a separate context record.

## Calibration Mix

Calibration sources are not fungible and do not automatically offset one another. A report must distinguish:

- external_source;
- repository_artifact;
- executable_test_or_CI;
- real_world_response;
- human_judgment;
- independent_model_or_review.

Three AI affirmations do not cancel one missing executable test. One CI pass does not settle a value conflict. One human preference does not prove a mechanism.

## Output Boundary

Positive evaluative words such as "complete", "correct", "excellent", "breakthrough", "revolutionary", "mature", or "green" are allowed only when bound to:

- object;
- criterion;
- version;
- test or evidence;
- boundary.

The goal is not forced negativity. The goal is to prevent praise, alignment, or reassurance from replacing mechanism, evidence, and boundaries.
