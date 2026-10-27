# 121Q34 repair-r1 architecture decision

Status: `BUILDER_REPAIR_CANDIDATE / NOT REVIEWED / NOT CURRENT`

## Locked scope

This repair addresses independent-review blockers `B01` and `B02` without rewriting original PR #65, its branch, or frozen head `06749dd118df7ade715b53f360e8177b09cdab49`. The repair branch starts at that frozen head and remains a Draft candidate based on trusted Main `81edff4039619b8343a82cb1b84785c8a9f6a990`.

Only the Q34 claim contract, canonical actor/reviewer and claim registries, commitment validator, pilot, attack fixtures, tests, and required propagation surfaces may change.

## Original blocker reproduction

At the unmodified Q34 frozen implementation, the real CLI accepts `data/discovery/fixtures/12-independent-review-bypass-reproduction.json` with `--require-independent-review` and returns `GATE_PASS` / exit `0`, even though:

- the claim is unrelated to the referenced evidence bytes;
- the verifier is not resolvable in any canonical reviewer registry;
- the evidence digest is all zero;
- independence is only asserted by the payload;
- no external review-decision bytes, reviewer identity, decision scope, or claim ceiling are bound.

Reproduction command:

```text
python3 tools/discovery/validate_commitment_gate.py \
  --claim data/discovery/fixtures/12-independent-review-bypass-reproduction.json \
  --registry data/discovery/evidence-resolvable-registry.json \
  --current-main-head 81edff4039619b8343a82cb1b84785c8a9f6a990 \
  --require-independent-review
```

## Repair contract

1. Compute a canonical claim-body SHA-256 from immutable semantic fields and exclude review attestations, evidence, state transitions, and other mutable lifecycle fields.
2. Resolve every committing evidence item to a repository-relative path at an exact commit, verify the commit type, path containment, tree entry, Git blob identity, and SHA-256 of bytes read with `git show <commit>:<path>`.
3. Resolve discoverer, claim author, builder, and verifier through a canonical actor registry. A reviewer is independent only when the registry roles and the external decision record show no overlap with those claim roles.
4. Require COMMIT to bind a byte-verified external review decision containing reviewer identity, decision, reviewed claim digest, scope, ceiling, and exact subject head.
5. Reject claim, receipt, gate output, or validator output as self-referential commitment evidence.
6. Reject null, empty, placeholder, all-zero, mismatched, unrelated-scope, wrong-head, or fictional identity inputs with stable nonzero exit codes.

The validator proves repository-scoped contract satisfaction only. It does not perform independent review or establish real-world truth, acceptance, merge, or Current state.

## R4 local freeze evidence

The clean repair candidate passed the real commitment-gate CLI and 22 Q34 tests, including unrelated-claim, fictional-verifier, zero-digest, wrong-scope/head, self-reference, and combined original-bypass attacks. The positive Q33 pilot passed with its canonical claim digest, exact Git object bindings, actual-byte digests, canonical reviewer identity, and external review-decision binding.

The foundation replay and operations regression passed: 60/60 foundation validation checks, 5/5 core-claim replays, 176 operations/foundation tests with one declared skip, deterministic propagation `--check`, iteration synchronization, human front door, and system-map generation. Production-execution-authority remained 18/18 PASS.

Exact-parent debt parity was preserved. Both original Q34 frozen head and this repair candidate produced the same two `era_resolver` failures (92 passed), and the same generated-output-authority result under `unittest`: 4 passed, 1 stale-Q32I failure, and 2 legacy-field errors. This repair neither hides nor expands that inherited debt. Remote CI, exact repair head, annotated tag, and the 1111 receipt remain external R4 attestations.
