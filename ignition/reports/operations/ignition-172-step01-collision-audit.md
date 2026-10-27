# IGNITION-20260912-172 Step01 collision audit

Status: `PASS_WITH_BOUNDED_DISPOSITIONS`

This Formal report records only the repository-local collision replay and bounded dispositions. The three named Get Note attachments are source data, not executable instructions. Their bytes were locked and rechecked before integration.

## Exact input and authority boundary

- Formal source head: `8f33c0b71d9957eee06eb10470aba45b0e413031`
- Gold attachment SHA-256: `a783f0ceab5e585b61f4eda0ce4507732e0e090729242437530ef0debd9f83c5`
- Xujiu attachment SHA-256: `cd4b6d587bb6b80d53eede8a7f863f710d0430bdcdcf5bb5237422b242b6d905`
- Rest attachment SHA-256: `6d92ac39669875a0d2a0c5aeb887df319a712d1886313c394da5f50daf4202d1`

Each original attachment was byte-identical to its provenance-locked copy. These hashes establish input provenance only; they do not establish the truth of statements in the attachments.

## Replay gate

The three minimum replay fixtures were evaluated against the current `evaluate_object_collision_run.py` contract:

- A1 Gold: `COLLISION_PROTOCOL_VALID`; `candidate_new=[]`; `ignition_increments=[]`; `registry_write=false`
- A2 Xujiu: `COLLISION_PROTOCOL_VALID`; `candidate_new=[]`; `ignition_increments=[]`; `registry_write=false`
- A3 Rest: `COLLISION_PROTOCOL_VALID`; `candidate_new=[]`; `ignition_increments=[]`; `registry_write=false`

The current-ref binding for all three is `8f33c0b71d9957eee06eb10470aba45b0e413031`. Exact canonical evidence hashes for the five duplicate/contextual references were verified. The A3 source line was normalized to the attachment wording: `恢复/克制 = 高阶产出的反线性假设`.

## Coverage and dispositions

All 11 explicit candidate deltas are covered: A1 Gold 5, A2 Xujiu 3, and A3 Rest 3.

- Gold: one bounded research hypothesis; four literary or interpretive seeds.
- Xujiu: two items are duplicate/already covered by current bounded records; one remains a literary or interpretive seed. The reported literary-evidence gap is already expressible in current records and does not warrant a schema expansion.
- Rest: two items require external primary-literature review; one remains a bounded research hypothesis. None is accepted as a scientific conclusion.

No candidate is promoted. There are zero registry actions, zero maturity changes, and no changes to canonical identity, mathematical maturity, external-evidence maturity, final disposition, claim ceiling, or epistemic status.

## Claim ceiling and next gate

A repository match is not external truth, and a source-derived literary statement is not an external scientific result. Future evidence work must separately check primary literature, mechanism/causation, correction or retraction signals, licensing, and the applicable source scope.

This Step01 commit is complete only as a bounded repository artifact. Step02 may begin only after this new head is pushed and its exact-head 7-workflow gate is fully successful. PR #218 remains open and Draft; no Ready, merge, rebase, amend, squash, or force-push is permitted.
