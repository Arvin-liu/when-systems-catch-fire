# 121Q36-OBS repair-r1 architecture decision

Status: `BUILDER_REPAIR_CANDIDATE / NOT REVIEWED / NOT CURRENT`

## Locked scope and parent

This repair addresses independent-review blocker `B04` without changing original PR #67, branch, frozen head `a8eab57bf2a2465c48d5d624e22681a1ad1bc20c`, receipt, or history. The branch began at that exact head and incorporated direct predecessor Q35 repair-r1 through ordinary two-parent merge commit `e732ebe7e0faf8355f3885d9c98f3f7c70aadaf3`.

Only Q36-OBS observation/prediction contracts, canonical predecessor/evidence surfaces, validator, pilot, attacks, tests, and necessary propagation surfaces may change.

## Original blocker reproduction

At the unmodified Q36-OBS semantic implementation, the real CLI returns `GATE_PASS` / exit `0` for `21-missing-predecessor-nonexistent-source-zero-digest.json`, even though the Q34 claim, Q35 actor/grant/trajectory and source path do not exist and all content digests are zero. Existing checks validate only syntax and locally asserted strings.

## Minimal repair contract

1. Resolve Q34 claim and Q35 authority/action trace from their canonical predecessor surfaces and verify the expected IDs, states, claim/grant digests and trajectory event.
2. Require canonical repository-relative paths at resolvable exact Git commits; reject absolute, parent-traversal, missing, symlink or non-blob sources.
3. Read bytes from Git objects and recompute blob identity and SHA-256 rather than trusting embedded digests.
4. Bind prediction freeze, outcome reveal, source bytes, evaluation window, target and rule/model version as distinct fields in byte-verified evidence records.
5. Reject missing predecessors, nonexistent sources, digest/head mismatch, copied snapshots, placeholders and zero digests with stable nonzero exits.

The validator checks repository records only. It does not execute an intervention, establish causal mechanisms, or prove universal predictive capability.
