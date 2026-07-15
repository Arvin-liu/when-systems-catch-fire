# Function OS v0.2 Candidate — Canonical Symbolic Reference Implementation

**Status**: CANDIDATE (not frozen, not final, not proven)
**Domain**: Symbolic functions only (no weight-space)
**Pipeline**: N1→N2→N3→N4→N5→N6→N7→N9, N8 for composition

## Quick Start

```bash
cd function-os-candidate/v0.2
python -m unittest discover tests -v
```

## Canonical Nodes

| Node | Name | Responsibility |
|------|------|----------------|
| N1 | FunctionSpec | Formal function specification with pre/postconditions |
| N2 | Representation | Machine-readable encoding (symbolic_ast) |
| N3 | Compiler | FunctionSpec + Representation → compiled payload |
| N4 | Artifact | Immutable, versioned, hashable artifact |
| N5 | Interpreter | Artifact + inputs → execution result |
| N6 | ExecutionTrace | Structured execution trace with events/timing |
| N7 | Validator | Artifact/spec/trace consistency validation |
| N8 | ComposerRouter | Task + candidates → execution plan |
| N9 | VersionedRegistry | Append-only, versioned, auditable registry |

## Testing

All tests use standard `unittest` with `import` — no `exec()`/`eval()`/`compile()` module loading.
No hardcoded local filesystem paths.

```bash
python -m unittest discover tests -v
```
