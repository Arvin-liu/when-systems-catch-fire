# 121Q38-I1 Interfaces

## Q37 input

Only a Q37 audit decision with `ALLOWED_AS_RESTRICTED_SEED`, an `audited` lifecycle, preserved counteranalogy state, a resolvable exact head and an explicit downgraded ceiling may become `audited_search_seed`. Q38 retains the Q37 candidate, decision and frozen-head identifiers without re-adjudication.

## Q33, Q34 and Q35 inputs

- Q33 rights records decide whether evidence may carry publishable content or citation-only metadata.
- Q34 committed claim and ceiling constrain the search question and final conclusion.
- Q35 active, in-scope authority constrains who may issue and close the repository-local search plan.

## Q39 output

Every `COUNTEREXAMPLE`, `NEGATIVE_RESULT`, and `FAILED_RETRIEVAL` item yields a `q39_failure_export` with originating task/artifact/exact head, symptom, evidence refs, affected claim, retry preconditions, prohibited retry and ceiling impact. Q39 owns append-only lineage, repair events and propagation.

## Call order

`Q37 restricted seed -> freeze Q38 plan and stop rule -> collect metadata-bound evidence -> apply inclusion/exclusion -> preserve negative and failed retrievals -> assess saturation and gaps -> emit bounded conclusion and Q39 exports`.

No Q38 object may modify Q37 history, execute a real-world action, publish unknown-rights content, or promote structural/case similarity to a mechanism claim.
