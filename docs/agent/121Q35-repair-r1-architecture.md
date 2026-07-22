# 121Q35 repair-r1 architecture decision

Status: `BUILDER_REPAIR_CANDIDATE / NOT REVIEWED / NOT CURRENT`

## Locked scope

This repair addresses independent-review blocker `B03` without modifying original PR #66, its branch, frozen head `ea1408e6525ceac8ea0c9c5377aca269579d6ff4`, receipt, or history. The branch began at that exact head and incorporated direct predecessor Q34 repair-r1 through ordinary two-parent merge commit `499ead2f8278cd4913243ac1a219ced3e7a0bf0e`.

Only Q35 responsibility/authority/action contracts, canonical claim/actor/grant surfaces, validator, pilot, attack fixtures, tests, and required propagation surfaces may change.

## Original blocker reproduction

At the unmodified Q35 semantic implementation, the real CLI accepts `data/agent/fixtures/17-missing-claim-nonexistent-grantor-bypass.json` and returns `GATE_PASS` / exit `0`. The missing `claim_ref` is silently treated as `committed_current`; the nonexistent grantor/principal is neither resolved through a canonical registry nor rejected.

```text
python3 tools/agent/validate_responsibility_gate.py \
  --bundle data/agent/fixtures/17-missing-claim-nonexistent-grantor-bypass.json \
  --claims data/agent/q34-claims-registry.json \
  --q33-rejects data/agent/q33-publication-rejects.json \
  --current-main-head 06749dd118df7ade715b53f360e8177b09cdab49 \
  --now 2026-07-21T00:00:00Z
```

## Minimal repair contract

1. Resolve every claim ID through the canonical Q34 claim surface and bind its canonical digest and exact head; unknown claims fail with a dedicated stable exit.
2. Resolve grantor, principal, grantee, and action actors through the canonical actor registry; unknown grantors fail with a distinct stable exit.
3. Resolve each grant artifact from a canonical grant registry and bind repository-relative path, exact commit, Git blob, actual-byte digest, validity interval, revocation state, delegation chain, and action/resource scope.
4. Reject embedded/self-declared grants, placeholders, zero/mismatched digests, wrong heads, expired/revoked grants, broken delegation, and scope mismatch.
5. Preserve Q33 publication and Q34 commitment boundaries and perform no external action.

The validator establishes only repository-scoped authorization-record consistency. It does not create real-world authority, execute an action, or establish independent acceptance.
