"""Function OS v0.2 — Canonical Symbolic Reference Implementation.

Nodes: N1 FunctionSpec, N2 Representation, N3 Compiler, N4 Artifact,
       N5 Interpreter, N6 ExecutionTrace, N7 Validator, N8 ComposerRouter,
       N9 VersionedRegistry.

Canonical pipeline: N1→N2→N3→N4→N5→N6→N7→N9, with N8 for composition routing.
"""
__version__ = "0.2.0"
__status__ = "CANDIDATE"
__domain__ = "symbolic-only"
