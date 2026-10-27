# Task 110 propagation record

This record binds the task-110 completion-state repair and the OpenAlex pilot to
the existing propagation machinery. It is a projection, not a new scientific
claim or an authorization for a future task.

## Lifecycle

- Candidate event: appended to `data/operations/lifecycle-events.jsonl` before the
  content PR is merged.
- Candidate state: `READY_FOR_CONTENT_MERGE`; it contains no future merge, tag or
  receipt hash.
- Terminalization: a separate projection will be appended only after the content
  PR and the narrow terminalization PR are ordinarily merged.

## Nine-dimensional impact

The machine contract is `data/operations/propagation/110-impact.json`. Public
wording, project state, open questions, editorial review and Evidence Program
surfaces are changed and therefore declared `IMPACT_REQUIRED`. The machine claim
record set, Function OS reference surface, maturity/disposition surfaces and the
four system-map sources are byte-identical to the recorded baseline; their
`NO_IMPACT_JUSTIFIED` decisions are hash-backed, not free text.

## System map

`data/operations/propagation/110-impact/system-map-nonimpact-proof.json` records
the independent audit. The OpenAlex run is bounded to bibliographic metadata and
does not add or retype a runtime component, capability node or architectural
edge. No system-map regeneration is required.

## Article lifecycle

Article 009 is new and reviewed against the task-110 baseline, completion ledger,
sealed OpenAlex result and this propagation record. Article 008 is marked
`STALE_REVIEW_REQUIRED` by the candidate event because its lifecycle source set
changes; it must be reviewed and its source manifest refreshed before final
terminal truth is published.

## Boundary

The result remains a cross-source bibliographic metadata consistency result. It
does not promote M/E levels, dispositions, paper-content validity, scientific
truth, Pointfire physics, MCF, PSD or ARN.
