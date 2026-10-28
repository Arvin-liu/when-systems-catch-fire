# IGNITION-20260825-139 Step 15 — Fresh clone, publication and witness gate

## Fresh task-branch clone

The exact pushed Task139 branch tip
`9a3b4a5561cf389b4f8af91274391096f39f65c2` was cloned into a fresh remote
checkout with no copied virtual environment, cache, generated temporary state
or untracked files. The clone passed the 25-check read-only projection
preflight with `failed_checks=[]`, `side_effect_detected=false`, and clean
before/after snapshots.

The natural full regression then completed with **1202 tests, 0 failures, 0
errors, 0 skips**. It used the isolated foundation dependency contract
(Python 3.14.6, SymPy 1.14.0, z3-solver 4.16.0.0 and jsonschema 4.26.0), ran
for `2844.034s` runtime / `2845.453s` elapsed, and had no watchdog, process
kill, arbitrary timeout or generated-output drift. The capture remained in an
external temporary directory; its stdout/stderr digests are preserved in the
machine receipt.

The tested clone was clean before and after the suite and remained at the
exact source SHA. The candidate full regression is preserved in the Step 14
receipt at the same exact tested SHA. This closes the repository-local
candidate/fresh-clone regression gate; it does not yet assert formal-main
publication.

## Live-observation boundary

No new live invocation occurred in Step 15. The canonical ledger remains at
five attempts, with zero validated completions, three unreconciled attempts
and two observation-incomplete attempts. The `LIVE_EXTERNAL_INVOCATION`
obligation remains open, retry remains unauthorized, and the next action is
reconciliation rather than another probe.

## Publication sequence

The formal main baseline is still
`12205be8ad94916a39253e0eba2106bf5da9da12`. The next operation is one ordinary
fast-forward to the exact terminal candidate, followed by fresh remote-main
SHA/HEAD equality, a clean post-publication Current check, and the separate
1111 publication witness. The formal repository will not self-witness the
publication SHA.

Claim ceiling: exact repository-local fresh-clone projection and natural
full-suite evidence for the tested Task139 candidate lineage only; no formal
main publication, validated live completion, external truth, production
readiness, Owner acceptance or epistemic acceptance is inferred.
