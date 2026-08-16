# External Agent Federation Core R1

The federation core is a vendor-neutral socket between the Ignition OS and an
external executor. `ExecutorDescriptor` describes observable compatibility;
`FederatedTaskEnvelope` carries OS-owned goal, policy, workspace, validation,
budget and handoff rules; `FederatedProgressEvent` carries public ordered
progress; `FederatedResultReceipt` carries claims plus independently verifiable
artifact/validation references; and `FederatedHandoffBundle` carries only
validated work and explicit pending scope.

`ExternalSessionRef` is always `pointer_only`. An executor's internal history,
prompt, hidden reasoning, token usage, memory database or session UI is not
canonical Ignition state. Receipt digests cover the unsigned public record and
are checked during construction and replay.

The typed records live in [`agent_federation/contracts.py`](../../agent_federation/contracts.py).
The public record schema is [`federation-core-r1.schema.json`](../../schemas/agent-federation/federation-core-r1.schema.json).
The `FederatedExecutor` protocol only asks for `probe`, `describe`, `dispatch`,
`status`, `cancel` and optional-capability `resume`; it does not prescribe an
internal agent loop.
