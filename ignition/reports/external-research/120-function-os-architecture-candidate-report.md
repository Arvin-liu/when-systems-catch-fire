# 120 — Function OS Architecture Candidate Report

## IGNITION-20260709-120
**Date**: 2026-07-13  
**Executor**: QClaw (qclaw/pool-glm-5.2-night, reasoning: high)

---

## 1. Overview

This report presents the Function OS candidate architecture, mapping external research paradigms to potential ignition architecture nodes. The Function OS is a conceptual overlay — not a proposed implementation — that identifies what a complete "function operating system" for ignition would require.

## 2. Architecture: Nine Nodes

```
FunctionSpec → Representation → Compiler → Artifact → Interpreter → ExecutionTrace → Validator → ComposerRouter → VersionedRegistry
```

### Node Status Summary

| Node | Status | Existing Correspondence |
|------|--------|------------------------|
| 1. FunctionSpec | CANDIDATE | Markdown files in 统一函数总表/ |
| 2. Representation | PARTIAL | Mathematical notation in markdown |
| 3. Compiler | MISSING | None |
| 4. Artifact | PARTIAL | 085 frozen v1 JSON |
| 5. Interpreter | MISSING | None |
| 6. ExecutionTrace | MISSING | None |
| 7. Validator | PARTIAL | 106-validator.py |
| 8. ComposerRouter | MISSING | None |
| 9. VersionedRegistry | PARTIAL | Git repository (informal) |

### Node Details

#### Node 1: FunctionSpec
- **Definition**: Formal specification including preconditions, postconditions, effect signature, uncertainty model
- **Current state**: Markdown files with informal mathematical notation
- **Gap**: No machine-checkable specification format
- **Minimal prototype**: JSON schema with name, definition, preconditions, postconditions, effect_signature, uncertainty_model

#### Node 2: Representation
- **Definition**: Machine-readable encoding of a function
- **Current state**: LaTeX/mathematical formulas in markdown
- **Gap**: No standardized machine-readable format
- **Minimal prototype**: LaTeX formula string + optional Python reference implementation

#### Node 3: Compiler
- **Definition**: Transforms FunctionSpec + Representation into executable artifact
- **Current state**: Does not exist
- **Gap**: No compilation infrastructure
- **Minimal prototype**: Python function that evaluates Ψ₀ given parameters

#### Node 4: Artifact
- **Definition**: Compiled, versioned, hashable function artifact
- **Current state**: 085 frozen v1 JSON is a partial artifact
- **Gap**: No general artifact system
- **Minimal prototype**: JSON file with name, version, sha256, representation, compiled_output

#### Node 5: Interpreter
- **Definition**: Executes function artifact with given inputs
- **Current state**: Does not exist
- **Gap**: No interpreter for ignition functions
- **Minimal prototype**: Python evaluator for Ψ₀ mathematical formulas

#### Node 6: ExecutionTrace
- **Definition**: Detailed log of function execution
- **Current state**: Does not exist
- **Gap**: No execution tracing
- **Minimal prototype**: JSON log with timestamp, function_id, inputs, outputs, duration, status

#### Node 7: Validator
- **Definition**: Validates function artifacts against specifications and evidence
- **Current state**: 106-validator.py exists as partial validator
- **Gap**: Needs extension for 120 outputs
- **Minimal prototype**: Python script checking JSON schema and hash integrity

#### Node 8: ComposerRouter
- **Definition**: Composes and routes between multiple functions
- **Current state**: Does not exist
- **Gap**: No composition infrastructure
- **Minimal prototype**: Function registry with task-to-function mapping

#### Node 9: VersionedRegistry
- **Definition**: Central registry with version history and provenance
- **Current state**: Git serves as informal registry
- **Gap**: No machine-readable registry
- **Minimal prototype**: JSON index with function_id, version, sha256, file_path, provenance

## 3. Relationship to External Research

| Source Family | Primary OS Node Informed |
|---------------|-------------------------|
| 1 (Neural weights as programs) | Representation, Compiler |
| 2 (Hypernetworks) | Compiler, ComposerRouter |
| 3 (Program synthesis) | FunctionSpec, Compiler |
| 4 (Neural operators) | Representation, Interpreter |
| 5 (Adapters) | Artifact, VersionedRegistry |
| 6 (Model merging) | ComposerRouter |
| 7 (Refinement types) | FunctionSpec, Validator |
| 8 (Algebraic effects) | FunctionSpec, ExecutionTrace |
| 9 (Probabilistic programming) | Representation, Interpreter |
| 10 (Self-evolving agents) | ComposerRouter, VersionedRegistry |

## 4. Assessment

The Function OS is **aspirational**. The current ignition architecture is documentation-first, not execution-first. Three nodes have partial existing implementations (Representation, Artifact, Validator), one is a candidate (FunctionSpec), and five are entirely missing.

The most impactful next steps would be:
1. **IGNITION-124**: Build a minimal Ψ₀ interpreter (addresses Node 5 + Node 3)
2. **IGNITION-122**: Design FunctionSpec JSON schema (addresses Node 1)
3. **IGNITION-123**: Extend validator with equivalence axis (addresses Node 7)

## 5. Safety Considerations

- Function OS nodes must respect ignition red lines (no Ψ₀ modification, no new function numbers)
- Interpreter must run in sandbox with resource limits
- VersionedRegistry must be append-only after freeze
- ComposerRouter cannot access function internals
- ExecutionTraces must not leak sensitive input data
