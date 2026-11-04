# R3 Successor Protocol R1 — Candidate

**Status:** `CANDIDATE_NOT_EFFECTIVE`  
**Normative machine contract:** [`release-transaction-protocol-r3-successor-r1.json`](../../data/operations/release-transaction-protocol-r3-successor-r1.json)  
**Schema:** [`release-transaction-protocol-r3-successor-r1.schema.json`](../../schemas/operations/release-transaction-protocol-r3-successor-r1.schema.json)

This document describes a forward-only amendment candidate for the R3 successor-transaction authorization and task-registration limits. It does not activate the candidate, authorize a release, publish V1, or complete Phase 1.

## Authority and activation chain

1. The one-time governance mandate is the Owner-authored authority record merged as 1111 PR #163. Its exact merge is `5f5af13ba5cd32b9e8a363ff8672f01f65d375c6`, based on `dda58027561c1c8fc99e3fa22e2e3eab6e20b69d`, with candidate head `9742a6c229bfbc9d403124e8f78b7613ea05b2c8`, tree `1eac0c48bae58e7df78f764cff516ec2436e342b`, and ordered parents `[dda5802…, 9742a6c…]`. The validator re-reads the Owner attribution, verified signature, exact file list and blobs, tree, parents, and current 1111/main ancestry. This authority comes from an explicit Owner governance act outside R3; R3 does not authorize its own amendment.
2. PR #163 authorizes preparation of this Formal branch and Draft PR only. It does not authorize Ready, merge, release, identity assignment, or a Phase 1 completion claim.
3. The candidate remains inert until a Formal protocol-amendment PR is normally merged with the exact base/head, required checks, an authorized independent non-author review, and an Owner approval of the same final head. A separate, append-only Owner-signed migration witness must then enter 1111/main and pass exact live readback. Only that witness can activate this protocol digest.
4. A later release must use an Owner-registered task identity, a separately signed, time-bounded authorization for one exact transaction, the unchanged R3 evidence gates plus successor review gates, a normal protected merge, and a new append-only publication witness.

This sequence is non-circular: the PR #163 founding mandate authorizes preparation; the Formal PR is independently reviewed and separately merged by the Owner; only after that merge does its Owner-signed 1111 migration witness make the versioned profile effective. No candidate file or unsigned record is authority.

## Forward-only records

Each record is a new path on 1111/main and must enter through an Owner-authored, GitHub-signature-verified PR merge. Its merge must have exactly one added ledger file, whose bytes equal the reviewed PR head. A later edit, deletion, rename, re-addition, duplicate path, tree mismatch, bad signature, or non-Owner merge fails closed.

- A task registration binds an explicitly Owner-selected task ID, ordinal, branches, exact Formal base, predecessor, full collision inventory, protocol blob and file digest, and unique nonce. The inventory and ordinal are never inferred by the validator. Supersession can retire a registration but never frees its task ID or ordinal.
- A transaction authorization is a separate Owner-signed record for one registration, transaction ID, PR number, exact candidate head and base, protocol digest, scope, nonce, approval time, and expiry. A changed head or base needs a new authorization. Revocation is append-only; a matching revocation before merge blocks the transaction.
- A publication witness is a distinct append-only record. It binds the authorization, registration, PR, exact final main commit/tree/ordered parents, remote main, fresh clone, final-SHA checks, projection result, and prepublication record digest.
- Nonces are unique across record types. Record IDs and task identities are unique within their respective namespaces. Multiple registrations and transactions can coexist; adding a later record cannot overwrite an earlier record.

## Inherited gates and history boundary

The candidate inherits R3's current required contexts, canonical full-suite receipt and independent revalidation, exact changed-path scope, branch-protection readback, merge-commit-only method, no-bypass/no-force-push conditions, final main verification, fresh clone, and postpublication workflows. It adds a live independent authorized non-author approval and an Owner approval on the exact PR head. A missing, stale, dismissed, wrong-head, unauthorized, or post-boundary review does not satisfy the gate.

The legacy R3 bootstrap authorization, Task21/R7 record, Task20/R6 records, and PR #266 `PUBLISHED_AND_VERIFIED` witness remain on their existing paths and under the existing validator profile. The new profile neither edits nor overwrites them. The separately signed 1111 PR #162 record remains `NOT_COMPLIANT` for PR #267, and the new-main R3 witness disposition remains `BLOCKED_WITH_EVIDENCE`; neither may be upgraded by this candidate or a later publication. Scientific obligations remain separate and unchanged (`PARTIAL`, `NOT_PERFORMED`, `NOT_VALIDATED`, `NO_DELTA`, or `NOT_ESTABLISHED` where recorded). E37 remains experimental/default-off, `LIVE_EXTERNAL_INVOCATION` remains open, and Phase 2 is not started.

## Verification and decision boundary

Focused candidate checks:

```sh
cd ignition
python3 tools/validate_release_transaction_protocol_r3.py --check --check-successor
python3 -m unittest tests.test_release_transaction_protocol_r3 -v
```

The tests retain the existing R3 compatibility suite and exercise successor inertness, historical status pins, explicit registration uniqueness, cross-record nonce replay, append-only path tampering, exact transaction scope/expiry/revocation, and independent/Owner review gates. They do not create a real task identity, authorize a transaction, activate this candidate, or serve as a substitute for live GitHub evidence.

Rollback, if the Owner later rejects or wants to replace an effective amendment, requires a normal reviewed and Owner-merged successor PR. Existing signed 1111 registrations, authorizations, revocations, supersessions, migration witnesses, publication witnesses, and historical R3 receipts are retained.
