#!/usr/bin/env python3
"""Static, fail-closed import gate for the generic Kernel and Runtime R0."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (ROOT / "agent_kernel", ROOT / "agent_runtime")
FORBIDDEN_TOKENS = {
    "foundation",
    "claim",
    "claims",
    "evidence",
    "function",
    "functions",
    "nonfunction",
    "nonfunctions",
    "results",
    "knowledge",
    "reos",
    "writing",
    "publication",
}
FORBIDDEN_PROVIDER_TOPS = {"openai", "anthropic", "google", "mistral", "ollama", "transformers"}
GENERIC_SUCCESS_PATTERN = re.compile(r"(?:StopState|state)\s*[.(\[][^\n]*(?:SUCCESS|success\b)")


def _module_name(node: ast.ImportFrom) -> str:
    prefix = "." * node.level
    return prefix + (node.module or "")


def _top_level(module: str) -> str:
    return module.lstrip(".").split(".", 1)[0]


def validate() -> dict[str, object]:
    violations: list[str] = []
    files_scanned = 0
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    stdlib.update({"__future__"})
    for package in PACKAGES:
        for path in sorted(package.rglob("*.py")):
            files_scanned += 1
            relative = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8")
            if GENERIC_SUCCESS_PATTERN.search(source):
                violations.append(f"{relative}: generic SUCCESS terminal marker")
            tree = ast.parse(source, filename=relative)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    modules = [_module_name(node)]
                else:
                    continue
                for module in modules:
                    normalized = module.lstrip(".")
                    top = _top_level(module)
                    tokens = set(normalized.replace("-", "_").split("."))
                    forbidden = sorted(token for token in tokens if token.casefold() in FORBIDDEN_TOKENS)
                    if forbidden:
                        violations.append(f"{relative}: prohibited domain import {module} ({','.join(forbidden)})")
                    if top in FORBIDDEN_PROVIDER_TOPS:
                        violations.append(f"{relative}: provider/model import is forbidden: {module}")
                    if not module.startswith(".") and top not in {"agent_kernel", "agent_runtime"} and top not in stdlib:
                        violations.append(f"{relative}: non-stdlib external import is forbidden: {module}")
            if path.parent == ROOT / "agent_kernel":
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.level == 0 and _top_level(_module_name(node)) in {"agent_runtime"}:
                        violations.append(f"{relative}: Kernel imports Runtime")
    if violations:
        raise ValueError("agent runtime boundary violations: " + "; ".join(violations))
    return {
        "status": "PASS",
        "packages": [path.relative_to(ROOT).as_posix() for path in PACKAGES],
        "files_scanned": files_scanned,
        "forbidden_domain_imports": sorted(FORBIDDEN_TOKENS),
        "provider_model_dependency": "none",
        "knowledge_dependency": "none",
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
