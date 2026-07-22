# 121Q39 repair-r1 architecture decision

Status: `LOCAL BUILDER REPAIR CANDIDATE / NOT REVIEWED / NOT CURRENT`

This repair addresses `B08` without changing original PR #71, branch, frozen head `824ff7f713303b18bca94b05de3f4b6530ffff51`, annotated tag, receipt or history. It starts at that exact head and incorporates Q38 repair-r1 through ordinary two-parent merge commit `89bb06cf7e45c457edb6a4e24840da3aa1bd2786`.

## Original blocker reproduction

Fixture `25-nonexistent-target-zero-digest-boolean-bypass.json` preserves the independent review attack. After refreshing the inherited source digests for the merged predecessor worktree, a nonexistent propagation target with an all-zero verification digest passes when caller-controlled `authorized=true` and `applied=true` are supplied. The unmodified Q39 real CLI returns `0`; no target bytes or effect are resolved.

## Minimal repair contract

1. Resolve every propagation target as a contained path and exact Git blob with digest recomputed from actual target bytes.
2. Resolve authorization from canonical Q35 grant/action bytes rather than caller booleans.
3. Resolve the declared plan effect from a separately bound structured effect record and require booleans to agree with that record.
4. Keep repository intervention effects request-only; no external action or target mutation is performed.

## Local validation evidence

The real CLI returns `0` for the positive pilot. Nonexistent target plus zero digest, actual target-byte mismatch, fabricated target exact head, mismatched effect-record bytes, fictional authority grant, and a caller boolean claiming that a request-only intervention was applied each return `15`.

Q39 capability tests pass `5/5`, with the matrix exercising 30 real CLI fixtures. The Q34–Q39 grouped capability and predecessor regression passes `177/177`. Propagation authority and effect are resolved from structured Git-bound objects; the high-risk intervention plan remains `REQUEST_ONLY`. Remote state is `NOT_CHECKED_LOCAL_ONLY`.
