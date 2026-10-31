# Execution State Lineage Audit

maintenance.audit_execution_state_lineage checks a bounded, caller-supplied projection of checkpoint and resume records. It is an optional read-only CLI and is not selected by default.

Run it with one UTF-8 JSON request on standard input:

    python3 -B ignition/tools/toolbox_execution_state_lineage.py --stdin < request.json

The request contains checkpoint records using the Kernel checkpoint fields, a declared active checkpoint, every other inactive leaf checkpoint, optional projected resume-capsule bindings, and optional rollback references. The result reports the active ancestor path, branch points, leaf checkpoints, and structural findings. It fails closed when parent links are unknown or cyclic, the selected checkpoint is not a leaf, inactive leaves are not fully accounted for, a resume projection disagrees with its checkpoint, or a rollback target is not an ancestor.

A passing result means only that these caller declarations are structurally consistent. It does not authenticate the caller, checkpoint or capsule, state digest, source, actor, or execution. The tool does not read checkpoint state bytes, store or compress memory, prove semantic branch isolation, evaluate compression quality, authorize resume or rollback, execute actions, make network calls, or write files. The caller must independently confirm that the supplied projection is complete and current.

Use this audit when a task needs one explicit active checkpoint path while preserving alternate tips. Use the existing Kernel resume validator for one checkpoint/capsule pair, Portable Research Episode for artifact-version and dependency lineage, and Execution Effect Receipt for a bounded post-run observation. Those tools retain their distinct scopes.
