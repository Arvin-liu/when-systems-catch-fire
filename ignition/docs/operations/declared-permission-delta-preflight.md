# Declared Permission Delta Preflight

`governance.preflight_declared_permission_delta@0.1.0` compares two caller-supplied declarations of grants for the same policy and subject. It reports exact `(capability, scope)` strings added to and removed from the candidate list. An addition or mixed change is labeled for review; a removal is not treated as safe automatically.

The tool reads one UTF-8 JSON request from stdin, capped at 128 KiB. It makes no repository reads, network requests, policy writes, sandbox calls, or external actions. Runtime requirements are Python's standard library. See [the strict input schema](../../schemas/operations/declared-permission-delta-r0.schema.json) and [the synthetic fixture](../../tests/fixtures/toolbox-declared-permission-delta/valid-input-r0.json).

The output compares caller-provided strings only. It does not authenticate who produced the snapshots, resolve inheritance or wildcard meanings, determine whether a path or host is contained by another scope, inspect effective runtime permissions, enforce an isolation boundary, or authorize a change. A string such as `*` is only an exact label in the supplied set; it is never interpreted as a wildcard. Do not place secrets or sensitive values in scopes because changed labels appear in the output.

The checked-in fixture is synthetic. The existing route planner's default-off/explicit-allowlist route experiment is recorded in [the route profile](../../data/operations/toolbox-declared-permission-delta-route-profile-r0.json) and [the route evidence](../../data/operations/toolbox-declared-permission-delta-route-evidence-r0.json); selecting a route proposes a tool only and never applies or authorizes a policy.
