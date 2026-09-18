# Operational Control Surface R0.2

Repository hooks are execution-only controls. They read a task-scoped
authorization receipt under the clone's Git directory, check the repository,
exact task branch and base ancestry, public noreply identity, push remote, and
operation class, then return one finite status code. R0.2 successor may invoke
the controls and observe a listed code; it must not open or interpret their
source or the authorization receipt.

The receipt is provisioned by the Builder or Owner from the active task
command. It is local to a clone and is not copied into the cognitive evidence
packet. The command reference and blob SHA provide traceability, not a digital
signature. A local user or process with write access to .git can replace the
receipt or bypass local hooks. The guard prevents accidental wrong-branch and
wrong-remote writes; GitHub credentials, server-side repository policy, and
human review remain the actual remote authority boundary.

No global Git configuration is changed. --no-verify, a changed
core.hooksPath, direct Git API writes, or a forged local receipt can bypass
a local hook; these limitations are explicit and do not grant remote
authority.

The packet manifest records each operational component, its source digest,
the status vocabulary, and execution-only policy without adding its source to
the cognitive allowlist. The read-ledger validator returns only
PASS_READ_LEDGER_CLEAN, FAIL_READ_LEDGER_CONTAMINATED, or
FAIL_READ_LEDGER_INVALID. Hook invocations return only the finite
task_branch_guard_r0_2.py status vocabulary. Opening source, reading the
receipt, or exposing case-specific information through operational output is
prohibited or contaminating under the R0.2 ledger contract.

The hooks keep a narrow compatibility path for frozen R0.1 test clones that
copy the hook and R0.1 preflight without the R0.2 guard. That legacy path can
only return the old branch-specific rejection on an R0.2 successor branch; it
cannot authorize R0.2 work. An actual R2 clone must have the R0.2 guard and a
valid task receipt or stop.
