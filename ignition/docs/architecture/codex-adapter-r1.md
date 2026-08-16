# Codex Adapter R1

Codex is integrated as an external coding executor through its observed
public `codex exec --json` JSONL surface.  The adapter assembles literal argv
with:

```text
codex exec --json --ephemeral --ignore-user-config --ignore-rules \
  --sandbox read-only [--cd <absolute workspace>] <canonical task body>
```

`read-only` is the default federation sandbox.  A `workspace-write` adapter
instance must be constructed explicitly; the adapter never uses
`--dangerously-bypass-approvals-and-sandbox` or bypasses hook trust.  The
effective permission is the intersection of the Ignition envelope, OS policy,
Codex sandbox and Codex approval policy.  A deny on any boundary cannot be
expanded by another boundary.

JSONL events are reduced to public progress, a bounded final summary and an
optional pointer-only `codex-thread-id`.  Prompt, hidden reasoning, token
usage and Codex internal history are not imported into OS state.  Codex's
completion event maps to `COMPLETED_UNVALIDATED`; the receipt remains
`REQUIRES_RECONCILIATION` until Ignition validators establish evidence.

Step 06 intentionally used a captured JSONL fixture and injected runner.
`LIVE_SMOKE_NOT_RUN`: this task is already executing in Codex, so no nested
Codex invocation was allowed to modify a formal repository.

Official CLI reference: <https://developers.openai.com/codex/cli/reference/>.
