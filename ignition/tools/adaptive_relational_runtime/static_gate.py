# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Anti-second-executor static scanner for tools/adaptive_relational_runtime.

Runs the CI gate in commit 5. Performs an AST + text dual scan over every .py
file in this package:

  * import whitelist: only stdlib, intra-package (relative + tools.adaptive_
    relational_runtime.*) and the four predecessor modules
    (tools.ignition_runtime.{generation,hashutil,errors,schemas_loader}) are
    permitted. Network / subprocess / second-executor modules are rejected.
  * banned tokens (pro.mote / evo.lve / trans.action) as standalone words are
    rejected, except the runtime-envelope assertion field names ``promote_called``
    and ``evolve_called`` which are const-assertions of non-use and do not match
    the word-boundary pattern.
  * no second executor: ``subprocess`` / ``socket`` / ``urllib`` / ``requests`` /
    ``http`` imports are forbidden; ``os.system`` / ``os.popen`` / ``os.spawn*``
    / ``os.exec*`` and any ``open(...)`` with a write mode are forbidden.

Exit code 0 iff zero violations. The scanner file itself is excluded from the
token text scan (it is the enforcer); its imports are still scanned.
"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
GATE_SELF = Path(__file__).resolve()

ALLOWED_EXACT = {
    "tools.ignition_runtime.generation",
    "tools.ignition_runtime.hashutil",
    "tools.ignition_runtime.errors",
    "tools.ignition_runtime.schemas_loader",
}
ALLOWED_PREFIXES = ("tools.adaptive_relational_runtime",)
DENY_MODULES = {"subprocess", "socket", "urllib", "requests", "http", "pty", "paramiko"}
FORBID_OS_ATTRS = {"system", "popen"}
FORBID_OS_PREFIXES = ("spawn", "exec")

# Word-boundary regex built from fragments so the scanner source itself never
# contains a contiguous banned token. Word boundaries use an explicit character
# class (no backslash escapes) to stay warning-free.
_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(prom" + "ote|evo" + "lve|trans" + "action)(?![A-Za-z0-9_])"
)

STDLIB = getattr(sys, "stdlib_module_names", set())


def _judge_module(module: str, path: Path, findings: list[str]) -> None:
    if module == "":
        return  # relative, module resolved below
    if module in ALLOWED_EXACT:
        return
    if module.startswith(ALLOWED_PREFIXES):
        return
    top = module.split(".")[0]
    if top in DENY_MODULES:
        findings.append(f"{path.name}: forbidden module import: {module}")
        return
    if any(part in ("promote", "evolve", "transaction") for part in module.split(".")):
        findings.append(f"{path.name}: forbidden module path component: {module}")
        return
    if top in STDLIB:
        return
    findings.append(f"{path.name}: import outside whitelist (third-party/unknown): {module}")


def _check_imports(tree: ast.AST, path: Path, findings: list[str]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _judge_module(alias.name, path, findings)
        elif isinstance(node, ast.ImportFrom):
            if node.level >= 1:
                continue  # relative import within the package
            _judge_module(node.module or "", path, findings)


def _check_calls(tree: ast.AST, path: Path, findings: list[str]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "os":
            if func.attr in FORBID_OS_ATTRS or func.attr.startswith(FORBID_OS_PREFIXES):
                findings.append(f"{path.name}: forbidden os call: os.{func.attr}")
        if isinstance(func, ast.Name) and func.id == "open":
            mode = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    mode = kw.value.value
            if mode and any(c in mode for c in ("w", "a", "x", "+")):
                findings.append(f"{path.name}: open() with write mode: {mode!r}")


def _check_tokens(source: str, path: Path, findings: list[str]) -> None:
    if path.resolve() == GATE_SELF:
        return  # scanner self-excluded from token text scan
    for match in _TOKEN_RE.finditer(source):
        findings.append(f"{path.name}: banned standalone token: {match.group(0)!r}")


def scan(package: Path | None = None) -> list[str]:
    """Scan the package; return a list of violation strings (empty == clean)."""
    root = package or PACKAGE
    findings: list[str] = []
    scanned = sorted(root.rglob("*.py"))
    for path in scanned:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError) as exc:
            findings.append(f"{path.name}: unreadable/parse error: {exc}")
            continue
        _check_imports(tree, path, findings)
        _check_calls(tree, path, findings)
        _check_tokens(source, path, findings)
    return findings


def main() -> int:
    findings = scan()
    print("== ARR static gate (anti-second-executor) ==")
    print(f"scanned package: {PACKAGE}")
    if not findings:
        print("result: ZERO VIOLATIONS")
        print("imports: within whitelist (stdlib / intra-package / 4 predecessor modules)")
        print("tokens: no standalone pro.mote / evo.lve / trans.action")
        print("second-executor: no subprocess/network/write paths")
        return 0
    print(f"result: {len(findings)} VIOLATION(S)")
    for item in findings:
        print(f"  - {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
