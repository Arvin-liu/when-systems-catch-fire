# Operational control surface R0.2

The repository hooks are execution-only controls. They read a task-scoped
authorization receipt stored under the clone's Git directory, check the
repository, exact task branch, authorized base ancestry, public noreply
identity, push remote, and operation class, then return one finite status code.
The R0.2 successor may invoke these controls and observe those codes; it must
not open or interpret their source or the authorization receipt.

The receipt is provisioned by the Builder or Owner from the active task
command. It is local to a clone and is not copied into the cognitive evidence
packet. The command reference and blob SHA provide traceability, not a digital
signature. A local user or process with write access to `.git` can replace the
receipt or bypass local hooks. The guard prevents accidental wrong-branch and
wrong-remote writes; GitHub credentials, server-side repository policy, and
human review remain the actual remote authority boundary.

No global Git configuration is changed. The installer writes only repository-
local configuration and the clone-local receipt. `--no-verify`, a changed
`core.hooksPath`, direct Git API writes, or a forged local receipt can bypass a
local hook; these limitations are explicit and do not grant remote authority.

The R0.2 packet manifest lists the permitted component identities and finite
status vocabulary without including operational source in its cognitive file
allowlist. A hook execution with a status-only result is an operational event,
not a cognitive read. Opening source, reading the receipt, or exposing
case-specific information through output is a prohibited cognitive read or
protocol contamination under the R0.2 ledger contract.
