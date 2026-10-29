# Approval Bridge, Handoff and Failover R1

The OS approval bridge computes a strict intersection between the Ignition
`ApprovalPolicy`, the requested capability ceiling, and any external approval
gate.  `DENY` always blocks.  `REQUIRE_OWNER` and `DELEGATED` wait for an
explicit Owner decision; an external executor's `APPROVED` observation never
replaces that authority.  If the external agent reports a pending gate, the
bridge records `WAITING_EXTERNAL_APPROVAL` rather than silently switching
executors.

`build_handoff_bundle` contains only public goal/work/acceptance text, validated
completed actions, pending work, capability ceiling, workspace refs, artifact
hashes, validator-linked memory capsule refs, pointer-only external session
refs and unresolveds.  It refuses to label unvalidated executor claims as
validated work.  `accept_handoff` requires a different executor to re-observe
the workspace and verify the source receipt/artifact refs before takeover.

Failover reasons are machine-enumerated in
`data/agent-federation/failover-reasons-r1.json`.  Automatic failover is
allowed only for a read-only task or validated/replayable side effects with a
verified receipt and a target that already has the same capability ceiling.
Unknown side effects, an unverified receipt, approval blocks and capability
mismatches remain typed non-automatic outcomes, usually
`REQUIRES_RECONCILIATION` or `BLOCKED_WITH_EVIDENCE`.
