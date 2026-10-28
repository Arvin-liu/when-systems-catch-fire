# Function OS v0.1 Candidate — Symbolic Reference Implementation

**Status**: CANDIDATE — NOT FROZEN, NOT FINAL, NOT PROVEN
**Version**: 0.1
**Generated**: 2026-07-15

## Node Inventory

| Node | Component | File | Status |
|------|-----------|------|--------|
| N1 | FunctionSpec Parser | `n1_functionspec_parser.py` | ✅ |
| N1 | Semantic Checker | `n1_semantic_checker.py` | ✅ |
| N1 | Safe Expression DSL | `n1_safe_expression_dsl.py` | ✅ |
| N2 | Symbolic Compiler | `n2_symbolic_compiler.py` | ✅ |
| N3 | Expression Interpreter | `n3_expression_interpreter.py` | ✅ |
| N4 | Artifact Packager | `n4_artifact_packager.py` | ✅ |
| N5 | Compile Feedback Loop | `n5_compile_feedback.py` | ✅ |
| N6 | Validation Feedback | `n6_validation_feedback.py` | ✅ |
| N7 | Cross-Node Pipeline | `n7_cross_node_composition.py` | ✅ |
| N8 | Trace Archiver | `n8_trace_archiver.py` | ✅ |
| N9 | Registry Store | `n9_registry_store.py` | ✅ |
| N9 | Registry Updater | `n9_registry_updater.py` | ✅ |
| N9 | Registry Validator | `n9_registry_validator.py` | ✅ |

## Schema Inventory

| Schema | File |
|--------|------|
| N1 FunctionSpec | `schemas/n1-functionspec-schema.json` |
| N4 Artifact Manifest | `schemas/n4-artifact-manifest-schema.json` |
| N9 Registry Record | `schemas/n9-registry-record-schema.json` |
| ID/Version/Hash | `schemas/v0.1-id-version-hash-spec.json` |

## Contracts

| Document | File |
|----------|------|
| Scope & Non-Goals | `function_os/v0.1-scope-contract.json` |

## Tests

| Test | File | Result |
|------|------|--------|
| N9 Registry | `tests/test_n9_registry.py` | 6/6 |
| E2E Pipeline | `tests/test_e2e_pipeline.py` | PASS |

## Constraints

- Python 3.10+ (stdlib only, no external dependencies)
- Symbolic functions only (no neural/weight-space)
- No eval, exec, shell, network, filesystem I/O (except trace archiver)
- JSON file store for registry (no database)
- Append-only registry history
- SHA-256 content integrity

## Known Gaps

- N3, N5, N8 have zero asset mapping from 121Q3
- No cross-representation equivalence (GAP-017)
- No weight-space algebra (GAP-016)
- No probabilistic semantics (GAP-020)
