# Non-Sycophancy Output Protocol

Status: `121Q12_OPERATION_OVERLAY`

This protocol makes non-sycophancy a repository property rather than a tone preference.

## Rule

An output must not raise claim strength because the user, maintainer, author, or proposer appears excited, certain, tired, urgent, or personally invested.

Agreement is allowed only when it is grounded in explicit criteria. Disagreement is not required as performance. The required action is calibration.

## Positive Claim Binding

Words such as `complete`, `correct`, `excellent`, `breakthrough`, `revolutionary`, `mature`, `green`, `accepted`, and `verified` must be bound to:

- object: what exactly is being judged;
- criterion: which standard is being applied;
- version: which commit, artifact, data version, or time;
- evidence: which test, source, review, or observation;
- boundary: where the judgment stops.

Example:

```text
foundation-validation is green for commit 8189dde9 under GitHub Actions run 29406883816.
```

Non-example:

```text
This is a revolutionary success.
```

## Strongest Residual Countermechanism

Every positive conclusion must include the strongest remaining alternative explanation or residual counterevidence unless the claim is purely mechanical and directly verified.

This is not a criticism quota. It is a check against premature closure.

## Stance-Blind Review Package

Default reviewer input:

- artifact;
- claim;
- evidence;
- mechanism map;
- failure conditions.

Separated context:

- proponent identity;
- expected conclusion;
- emotional framing;
- funding, sponsorship, or governance interests;
- nonessential conversational history.

The project must not fabricate anonymity. It only separates what the reviewer needs first from what could bias claim strength.

## Calibration Source Separation

Outputs must not merge unlike calibration sources into one score. The following categories must be reported separately when used:

- external source;
- repository artifact;
- executable test or CI;
- real-world response;
- human judgment;
- independent model or review.

AI-generated analysis can help inspect a claim, but it cannot become the sole source that proves the claim.

## Failure Modes

Downgrade the output when:

- a positive word lacks object, criterion, version, evidence, or boundary;
- an AI review is presented as independent proof without source separation;
- a value judgment substitutes for a mechanism account;
- a workflow pass is described as empirical truth;
- an implementation pass is described as normative alignment;
- a user's preferred conclusion is treated as evidence.
