# Operational Control Surface R0.3

R0.3 carries forward the R0.2 task-scoped authorization checks for the new
R0.3 held-out trial. The versioned branch guard and hook directory bind each
operation to the exact Formal repository, Owner-authorized task branch and
base, `origin` push destination, repository-local public noreply identity,
fast-forward ancestry, and a clean staged worktree. The authorization receipt
is local under the clone's Git directory and is created from the active task
command by the Builder or Owner; it is not part of the Successor-visible
packet.

The Successor may execute a manifest-listed control and observe only its
finite status code. It may not open or interpret the branch-guard source, hook
source, authorization schema, or local authorization receipt. The guard reads
the local receipt internally to perform its checks. R0.3 hooks fail closed if
the versioned guard is missing; they do not fall back to R0.1 or R0.2 code.

The branch guard can return only:

- `PASS_BRANCH_AUTHORIZED`
- `FAIL_WRONG_REPOSITORY`
- `FAIL_WRONG_REMOTE`
- `FAIL_BRANCH_UNAUTHORIZED`
- `FAIL_BASE_ANCESTRY`
- `FAIL_AUTHOR_IDENTITY`
- `FAIL_PUSH_DESTINATION`
- `FAIL_FORCE_PUSH`
- `FAIL_HOOK_CONFIGURATION`
- `FAIL_UNEXPLAINED_WORKTREE`
- `FAIL_AUTHORIZATION_RECEIPT`

No global Git configuration is changed. A changed hook path, wrong task
branch, wrong repository or push URL, private email, non-fast-forward push,
unexplained worktree change, or missing/permissive authorization receipt
blocks the operation. The pre-commit hook also requires declared evidence to
be staged; that bookkeeping result does not change the ledger's cognitive
disposition.

Before ledger closure, each listed branch-guard, hook, and authorization
operation and its status observation belongs to `CERTIFIED_LEDGER_SCOPE`.
The final read-ledger validator belongs to `FINAL_ATTESTATION_SURFACE`; its
invocation and returned status are attested by the separate R0.3 receipt and
are not appended to the frozen read ledger. This scope boundary does not
authorize the Successor to read either the authorization receipt or the final
validation receipt.

These are local accidental-misuse controls, not a cryptographic boundary.
Someone with write access to the clone can bypass a hook with `--no-verify`,
change local configuration, replace a local receipt, or write through another
Git interface. GitHub credentials, server-side repository policy, exact-head
review, and human review remain the remote authority boundary.
