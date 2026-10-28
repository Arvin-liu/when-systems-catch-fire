# SYMBOLIC-SPHERE repair-r2 — R0 controlled reproduction (RB09 shared engine)

This checkpoint is the linchpin: it fixes the shared fail-closed engine
`tools/governance/structured_capability_gate.py`, which is imported by every
downstream B09 wrapper (`from tools.governance.structured_capability_gate import
run, result`). Fixing it here closes four of the five independent root blockers
for all nine importing consumers via `--no-ff` predecessor merges.

## Controlled reproductions (pre-fix behaviour, per corrected reproduction)

The corrected reproduction `agent-results/independent-re-review-r1-correction/
shared-engine-controlled-reproduction.md` recorded that the original engine
returned **exit 0** (GATE_PASS) for each of the following bypass attempts:

1. **Absolute path** — `repository_relative_path: /etc/hosts` escaped ROOT
   because `ROOT/e.get("artifact","")` discards ROOT on an absolute join and the
   engine then read the working-tree file as authoritative.
2. **`..` traversal** — `repository_relative_path: ../secrets` escaped the repo.
3. **Backslash / symlink escape** — non-canonical paths resolved outside ROOT.
4. **Fabricated exact_head** — `exact_head: "deadbeef"*5` (format-valid,
   non-existent object) passed the `HEAD_RE` format check and was never
   `git cat-file -e` resolved.
5. **Missing git-object fields** — omitting `commit_sha` / `repository_relative_path`
   / `blob_sha` / `sha256` still returned exit 0 (the engine treated them as
   optional).
6. **Tampered blob / sha256** — a wrong `blob_sha` / `sha256` was not recomputed
   from the real Git blob.
7. **Caller-asserted semantics** — `facts[rid]=True` and `rule_assertions[].status="PASS"`
   alone satisfied the gate even with no resolvable evidence.

## Post-fix verification

`tests/test_structured_capability_gate.py` (added this checkpoint) drives the
real engine CLI with a valid bundle built from a **real Git object** in this
repo and with each of the seven forged variants above. Assertions:

- valid bundle → exit 0 (GATE_PASS)
- absolute / `..` / backslash / symlink escape → non-zero (EVIDENCE_BINDING_INVALID)
- fabricated exact_head / missing git-object field / tampered blob / tampered
  sha256 → non-zero
- caller-asserted `facts=true` / `status=PASS` with non-resolving evidence → non-zero
- parent head mismatch → non-zero (PARENT_BINDING_INVALID)

All assertions pass. The engine now resolves `commit:path` against the real Git
blob, recomputes `sha256`, enforces canonical repo-relative POSIX paths, requires
`commit_sha`/`exact_head` to be real commits (exact_head an ancestor of
`commit_sha`), and recomputes every rule from registered, git-resolved evidence
instead of trusting caller flags.
