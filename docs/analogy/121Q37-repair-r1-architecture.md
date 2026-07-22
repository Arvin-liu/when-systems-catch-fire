# 121Q37 repair-r1 architecture decision

Status: `LOCAL BUILDER REPAIR CANDIDATE / NOT REVIEWED / NOT CURRENT`

This repair addresses `B06` without changing original PR #69, branch, frozen head `927cae48f3c65d3c23543dac4b9262704fabb6f1`, tag, receipt or history. It starts at that exact head and incorporates Q36-INT repair-r1 through ordinary merge commit `186f747efa600c918a51378d8326525192024ee1`.

## Original blocker reproduction

At the original frozen head, the real CLI runs the checked-in pilot against `927cae48f3c65d3c23543dac4b9262704fabb6f1` and exits `17` because the pilot embeds intermediate commit `e302459e721149cc5a42a4ae506b473a1cd92693`. The same pilot promotes a Q34 `commitment_candidate` into a locally asserted `committed_current` claim and supplies fictive external evidence and grant records.

## Minimal repair contract

1. Bind the runtime exact candidate head through the CLI and require it to equal the actual checked-out commit object, avoiding self-embedded intermediate heads.
2. Resolve the originating Q34 claim and Q35 authority/action from canonical predecessor bytes; candidate claims and fictional grants fail.
3. Replace fictive external evidence with repository-contained Q36-OBS/Q36-INT artifacts at exact commits, Git blobs and actual-byte digests.
4. Recompute mapping digest from its semantic content and preserve the analogy as structural only; no mechanism or transportability promotion.
5. Keep Q38 retrieval `NOT_ALLOWED` and execute no external lookup or real-world action.
