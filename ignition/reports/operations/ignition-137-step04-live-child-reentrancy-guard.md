# IGNITION-20260824-137 — Step 04 Child Context and Reentrancy Guard

The live Codex adapter now materializes at most one child context. A parent at
depth 0 may issue a depth-1 child with
`POINTFIRE_LIVE_CHILD_DEPTH=1`; a depth-1 context cannot issue another child,
and a Codex adapter created at depth 1 refuses to build a dispatch argv.

The child prompt is rendered only from the synthetic fixture reference,
bounded success criteria, and output contract. The formal parent prompt, 1111
task body, and parent context are not accepted as inputs. The child environment
is an explicit allowlist; `HOME` and `TMPDIR` point at the disposable fixture,
and only the existing Codex auth boundary may be carried as `CODEX_HOME`.
User environment variables, formal repository paths, relay paths, and agent
spawn capability are not forwarded.

The fake child proof and adapter/dispatch tests passed: `11 tests / 0 failures /
0 errors / 0 skips`. No live inference was run.

Claim ceiling: this establishes a bounded child/reentrancy boundary, not a
validated live completion or a claim about the model's behavior.
