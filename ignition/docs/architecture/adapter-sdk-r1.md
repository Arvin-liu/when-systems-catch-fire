# Adapter SDK and Conformance Harness R1

The adapter SDK is intentionally thin. It provides safe argv subprocess
execution (`shell=False`, allowlist, timeout and output cap), executable and
version discovery, JSON/JSONL parsing, redaction, capability mapping,
pointer-only session references, process cancellation and a public receipt
builder. It does not provide a model loop, planner, tool ecosystem, daemon,
memory store or provider integration.

The routing tokens in
[`capability-taxonomy-r1.json`](../../data/agent-federation/capability-taxonomy-r1.json)
are compatibility labels, not permission grants. `FederationConformanceSuite`
tests the same observable boundary for a reference or external adapter:
probe/descriptor, capability denial, dispatch/progress, status ordering,
cancel, optional resume declaration and idempotency. Malformed output,
timeouts, oversized output, duplicate keys and receipt tampering remain typed
failures; no hidden executor state is imported.
