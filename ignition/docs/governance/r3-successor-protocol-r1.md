# R3 Successor Protocol R1 — Candidate

**Status:** `CANDIDATE_NOT_EFFECTIVE`  
**Normative machine contract:** [`release-transaction-protocol-r3-successor-r1.json`](../../data/operations/release-transaction-protocol-r3-successor-r1.json)  
**Schema:** [`release-transaction-protocol-r3-successor-r1.schema.json`](../../schemas/operations/release-transaction-protocol-r3-successor-r1.schema.json)

This is a forward-only amendment candidate for R3 task registration, authorization, review, and publication records. Formal PR #266 is merged at `138b388fbe7815d6cdddc573315120eb4c1b099d`; its signed 1111 PR #159 `PUBLISHED_AND_VERIFIED` receipt is on current 1111/main at `d0eee10c456c7a18cbaee1e93b646dd8ddfbf053` (receipt SHA-256 `84173878716f319cd69fdf37065139a29baf5be0cadf0218701fb24a82069a9a`) and binds the effective Formal R3 protocol blob `1fd53f8023ab96d694e71c6ed28f81e30a32ca6c`. R2 checks are retained for backward compatibility; they do not describe the current effective protocol. The legacy R3 bootstrap selector's “R2 before any merge-bound activation claim” describes the earlier R2-to-R3 transition state; a missing receipt in that compatibility check does not roll current main back to R2. This successor candidate does not activate itself, authorize a release, publish V1, cure PR #267, or complete Phase 1.

## Authority for this amendment

The amendment itself is prepared from two already merged 1111 records; it does not use the candidate protocol to authorize itself.

1. The direct founding authority is Owner-verified PR #163, merged at `5f5af13ba5cd32b9e8a363ff8672f01f65d375c6` with ordered parents `[dda58027561c1c8fc99e3fa22e2e3eab6e20b69d, 9742a6c229bfbc9d403124e8f78b7613ea05b2c8]`. Its scope permits preparing a Formal branch and Draft PR. It does not permit Ready, merge, release, activation, branch-protection changes, or a Phase 1 completion claim. The validator reads back the PR, exact changed files, signed merge, ancestry, and authority record.
2. PR #165 made Task22's identity effective under that root authority. It is an Owner-verified merge at `5449650811882f0c107e58680ee43d92577f7288`, based on #163's merge and the exact #165 head `17ed13c274630269062e84834d52b49f34236931`. Its one added file has blob `146df919b91ddf2bf189a106441abee80486056d` and SHA256 `f4300d22378458b1ed36ccb168cbe67be71c8056706005af331e3bd93c6ccc05`. The validator checks the signature, parents, current 1111/main ancestry, file bytes, Task22/ordinal 22, branch names, and permitted scope.
3. PR #166 prospectively clarifies the independent-review evidence media for Task22. Its Owner-verified merge is `064c0112ba7a8672b77a507f8763e79b6914cb0c`, with tree `b027b3ff7afa0786f22ae79adcd65abd16d0bdf8`, ordered parents [`5449650811882f0c107e58680ee43d92577f7288`, `9f6433041cf8d44d353d1ebcc32a68517a74552b`], and one added file at blob `de54df684593a98c33c14847465eb1a7a896a919` (SHA256 `92f9743246da9a9c5b5ccaf689e82a20b6fde86959addbfe446efecffe3885f1`). The validator checks the signed merge, exact file, and current 1111/main ancestry live.
4. The #163 + #165 + #166 pair authorizes only this Task22 amendment's preparation actions: candidate work, pushing its assigned branch, creating a Draft PR, and collecting required checks. The one-time bootstrap is separate from the future `PREPARATION_ONLY` record defined below. `--verify-amendment-preparation` performs the live authority and local branch/base checks before a Draft is created; `--verify-owner-review-authority` checks #166 on its own.
5. Formal merge and activation remain blocked until the exact candidate head has all inherited required contexts, a genuine substantive non-author AI review with a complete exact-head evidence report, an Owner-signed exact-head review record, protected merge evidence, and an append-only Owner-signed 1111 migration witness. A human GitHub approval is additionally required only when the live branch rules require it. The Owner's final merge decision is a separate act.

This is non-circular: the verified 1111 root mandate and Task22 identity precede the Formal PR. The future successor PREPARATION_ONLY mechanism is not used to authorize this amendment and cannot activate itself.

## Forward-only records

Every 1111 control record is a new append-only path. Each record enters through its own Owner-authored, GitHub-signature-verified PR merge and adds exactly one file unchanged from the reviewed PR head. The validator checks the full relevant first-parent history so later edits, deletion, rename, replay, signature failure, or tree mismatch cannot be hidden by the current tree.

- **Task registration** binds the Owner-selected task ID and ordinal, work and receipt branches, exact Formal base and predecessor, full collision inventory, protocol blob and digest, and nonce. Ordinals are explicit and never inferred. Supersession does not free task IDs or ordinals.
- **PREPARATION_ONLY authorization** is signed before the PR number or final PR head exists. It binds the registration, task and ordinal, assigned branch, exact base, protocol blob and digest, candidate seed SHA256, nonce, approval time, and expiry. It authorizes only `PUSH_REGISTERED_BRANCH`, `CREATE_DRAFT_PULL_REQUEST`, and `COLLECT_REQUIRED_CHECKS`. It cannot mark Ready, merge, publish, or change branch protection. The validator's preparation action check has no PR-number or PR-head input.
- **FINAL_TRANSACTION authorization** is a separate Owner-signed record created after a PR number and exact head exist. It binds the `preparation_id`, registration, task and ordinal, transaction ID, exact PR number, candidate head, base, protocol digest, nonce, approval time, and expiry. A changed PR, head, base, or preparation grant fails validation. The final grant does not expand the earlier preparation scope.
- **Owner exact-head review** is a separately signed `OWNER_EXACT_HEAD_REVIEW` record. It binds the PR author, number, base and head, a deterministic digest of the exact changed-file inventory, the protocol digest, an independent AI review report, the Owner's decision and summary, review time, and nonce. The Owner review record must precede the Formal merge and is distinct from the Owner's final merge decision.
- **Publication witness** binds both the preparation and final authorization IDs, registration and transaction, PR, exact final main commit/tree/ordered parents, remote main, fresh clone, required post-publication checks, projection result, and pre-publication record digest.
- Nonces are unique across record types, including preparation, final authorization, Owner review, revocation, and supersession. Authorization revocations bind the exact record type and bytes.

## Review chain for a single-Owner repository

The PR author may be the Owner. The Owner is the sole final merge authorizer. A separate Owner-signed exact-head review record is required before merge, and that record is distinct from the final merge decision.

A genuine substantive non-author AI review is required for the exact candidate source and diff. Its direct read-only report binds the task and ordinal, PR author and number, base and head, complete changed-file inventory, per-file patch digests when GitHub exposes them, exact whole-diff digest, protocol digest, required CI contexts, branch-protection digest and approval count, findings, limitations, verdict, artifact ID, timestamp, expiry, and canonical report digest. It records the authoring and reviewer roles, work channels, model and execution details when known, and explicitly labels identity fields that the platform does not verify. Self-reported `execution_id` or `instance_id` strings are not required and do not prove independence; no platform execution attestation is required. The report also records the reviewer's separate read-only process and evidence so the Owner can assess whether the review was genuinely non-author. If the Owner cannot establish independence from the substantive evidence, the decision remains `BLOCKED_WITH_EVIDENCE`. The Owner-signed append-only review record binds this report and the exact #166 authority before Formal merge. Missing report/source readback, report/head/diff mismatch, tampering, stale evidence, failed required CI, an expired report, or a `REJECT`/`INCONCLUSIVE` verdict fails closed. The report is AI evidence; it is never a GitHub `APPROVED` review.

A third-party human review is optional by default. The current inherited Formal main protection readback requires zero approvals. If a future live branch rule requires human approval, the validator also requires the exact live GitHub `APPROVED` review history, enough distinct non-author/non-Owner reviewers on the exact head, and matching review references in the migration witness. No branch rule is bypassed or changed to accommodate the AI review. A reviewer does not need repository write permission under project policy unless the live branch rule itself requires it. If the Owner cannot establish genuine non-author review from the substantive exact-head evidence, the decision remains `BLOCKED_WITH_EVIDENCE`.

## Inherited gates and history boundary

The candidate retains R3's current required contexts, canonical full-suite receipt and independent revalidation, exact changed-path scope, branch-protection readback, merge-commit-only method, no-bypass/no-force-push conditions, final-main verification, fresh clone, and post-publication workflows. Required contexts must pass for the exact head and base. Stale review evidence, a changed head, missing authorization, expiry, or revocation fail closed.

The legacy R3 bootstrap authorization, Task21/R7 record, Task20/R6 records, and PR #266 `PUBLISHED_AND_VERIFIED` witness remain unchanged under the existing validator profile. The signed 1111 PR #162 adjudication keeps PR #267 at `NOT_COMPLIANT`; its separate R3 witness stays `BLOCKED_WITH_EVIDENCE`. This candidate cannot alter those decisions or claim retroactive compliance. Scientific obligations remain separate and unchanged. E37 remains experimental/default-off, `LIVE_EXTERNAL_INVOCATION` remains open, and Phase 2 is not started.

## Verification and decision boundary

Focused candidate checks:

```sh
cd ignition
python3 tools/validate_release_transaction_protocol_r3.py --check --check-successor
python3 tools/validate_release_transaction_protocol_r3.py --check --check-successor --verify-owner-review-authority
python3 -m unittest tests.test_release_transaction_protocol_r3 -v
python3 -m unittest tests.test_release_transaction_protocol.py -v
python3 tools/validate_release_transaction_protocol_r3.py --check --check-successor --verify-amendment-preparation
```

The focused tests cover protocol/schema consistency, the non-circular #163/#165/#166 bootstrap, preparation/final authorization separation, forbidden preparation actions, expiry and revocation, cross-record nonce replay, disclosed identity limits, substantive read-only review evidence, report digest and exact diff/CI/branch-rule bindings, negative controls, conditional human branch approvals, signed Owner exact-head review records, required contexts, append-only history, and preserved #266/#267 decisions. They do not activate the candidate. The validator does not claim to authenticate platform execution identity; the Owner assesses the disclosed evidence and limitations.

Only a completed protected Formal merge followed by the exact signed 1111 migration witness can make this successor protocol digest effective. The distinct non-author AI review is the routine review route; a genuine human GitHub approval is additionally required only when live branch rules require it. If the AI evidence is unavailable or fails validation, stop with `BLOCKED_WITH_EVIDENCE`. Existing signed registrations, authorizations, revocations, supersessions, migration witnesses, publication witnesses, and historical R3 receipts remain append-only.
