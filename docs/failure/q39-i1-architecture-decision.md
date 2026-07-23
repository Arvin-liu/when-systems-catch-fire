# Q39-I1 Architecture Decision — Append-Only Failure Lineage

Status: Draft candidate stacked on Q38 frozen exact head `312a3282381bd0cb6dcc5fa629cbd058eacd9a56`.

## Decision

Q39 introduces one repository-native governance capability: an append-only failure lineage that joins failures from observation residuals, intervention outcomes, analogy audits, evidence retrieval, retractions, rollback and repairs. A failure is never a proof of cause. Its causal status is limited to `UNKNOWN`, `CANDIDATE`, or `NOT_ESTABLISHED`.

Every event binds an originating task, artifact, exact head, content digest and previous-event digest. The gate deterministically replays the chain, preserves negative evidence and superseded records, and requires an unresolved failure to alter at least one authorized downstream search, prediction, analogy audit, intervention, escalation, defer decision or claim ceiling.

## Boundary

The lineage records repository evidence and planning effects only. It does not identify a real-world mechanism, execute a retry, perform an external action, erase an inherited event, establish L7, or upgrade any claim beyond its upstream ceiling. `ENVIRONMENT` failures cannot be relabeled as theoretical failures without new distinguishing evidence.

## Interfaces

- Q36-OBS/INT provide residual, failure, rollback and repair candidates.
- Q37 provides analogy mismatch and retraction candidates.
- Q38 provides counterexample, negative-result and failed-retrieval exports.
- Q39 emits affected-object propagation and unresolved-failure state to Symbolic Sphere, Decision Integrity and Scientific Metacognition.

## Legacy disposition

The legacy branch `lab/121q39-failure-memory-night@95d637fcd5a33791e1cf69deec49d36389b9aeb0` remains preserved at annotated tag `archive/lab-121q39-failure-memory-night`. The production branch does not merge it. Typed append-only lineage, recurrence signatures and repair propagation are selectively reimplemented against the current Q34–Q38 contracts; legacy examples and conclusions are historical only.
