# Agent Episode Binding Plan Preflight

This optional tool checks one declarative Agent Episode Binding plan from JSON on stdin. It checks the plan schema and consistency between role declarations, digest-bound context references, feedback edges, write-domain bindings, permissions declared in the plan, and the work-unit dependency DAG.

The tool does not resolve or read context references. It does not authenticate the caller-declared permission ceiling, identify agents or providers, schedule work, send messages, enforce context isolation or resource leases, interpret aggregation policy, or authorize execution. A consistent plan is only a structurally consistent declaration.

## Use

Run the focused fixture from the repository root:

    python3 -B ignition/tools/toolbox_agent_episode_binding.py --stdin < ignition/tests/fixtures/toolbox-agent-episode-binding/valid-plan-r0.json

The tool reads one UTF-8 JSON object capped at 262,144 bytes. It prints one JSON result. Exit status 0 means the declaration checks found no conflicts; status 2 means malformed input, schema failure, or a cross-reference conflict. Output always keeps execution_authorized false and runtime_enforcement_status as NOT_EVALUATED.

## Checks

- Role tool and read/write-domain declarations stay within the plan's caller-declared ceiling.
- Each context reference has a SHA-256 declaration and an explicit private/shared audience; a role or work unit cannot reference a context outside its declared role scope.
- Feedback channels declare message kinds and control effects. Informational channels cannot change inputs, stop work, or request Owner review. A stop channel requires a typed PROTOCOL_HARD_STOP, a role declaration that allows stop signaling, and a caller-declared policy reference.
- Every work unit references a declared role, compatible input/output classes, declared context IDs, and valid dependencies.
- Work-unit dependencies form a DAG. Two work units that write the same exclusive domain must be ordered by a dependency path.
- Mutating work units bind to an exclusive write-domain declaration. External and unknown effects remain visible as requiring separate admission.

The permission ceiling and policy references are caller declarations, not authenticated authorities. The validator cannot establish live isolation, exclusive-writer enforcement, hard-stop correctness, safe concurrency, scientific quality, or production readiness. The existing scheduler and resource-arbitration components remain the execution substrate; this tool does not implement a scheduler or lock manager.

The input contract is the toolbox candidate's strict plan schema at ignition/schemas/operations/toolbox-agent-episode-binding-r0.schema.json. It is an optional candidate extension informed by Workbench AB-05; it does not change public Current or promote the Workbench schema.
