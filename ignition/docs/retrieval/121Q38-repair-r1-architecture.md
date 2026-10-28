# 121Q38 repair-r1 architecture decision

Status: `LOCAL BUILDER REPAIR CANDIDATE / NOT REVIEWED / NOT CURRENT`

This repair addresses `B07` without changing original PR #70, branch, frozen head `312a3282381bd0cb6dcc5fa629cbd058eacd9a56`, annotated tag, receipt or history. It starts at that exact head and incorporates Q37 repair-r1 through ordinary two-parent merge commit `64169682b7944a8de4de803caf209838bbe808cf`.

## Original blocker reproduction

Fixture `25-nonexistent-source-fabricated-head-bypass.json` preserves the independent review attack. A repository locator that does not exist and a fabricated all-`f` exact head are accepted after recomputing only `sha256(source_locator + summary)`. The original real CLI returns `0`, so no retrieved repository bytes are established.

## Minimal repair contract

1. Every successful repository evidence item carries a contained path, exact commit, Git blob identity and SHA-256 of the actual bytes at that commit.
2. Failed/unperformed retrieval remains explicit, carries no invented content binding, and cannot count as retrieved evidence.
3. Null, empty, zero or placeholder digests and nonexistent/wrong objects fail closed.
4. The Q37 seed is bound to canonical Q37 repair bytes; no network retrieval or external action is added.

## Local validation evidence

The real CLI returns `0` for the positive pilot. Nonexistent repository source, actual-byte digest mismatch, fabricated exact Git head, path traversal, null binding on a claimed retrieval, and zero placeholder digest each return `15`. The explicit failed/unperformed retrieval keeps both byte binding and digest null and is never counted as retrieved content.

Q38 capability tests pass `6/6`, with the matrix exercising all 30 real CLI fixtures. The Q34–Q38 grouped capability and predecessor regression passes `172/172`. Remote branch, PR, tag and CI state is `NOT_CHECKED_LOCAL_ONLY`.
