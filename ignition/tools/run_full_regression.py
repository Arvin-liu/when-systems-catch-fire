#!/usr/bin/env python3
"""Run the repository's canonical unittest discovery contract.

This is deliberately an orchestration wrapper around the existing unittest
suite.  It derives the application root from this file, runs discovery from
that explicit root, performs a dependency preflight, and records whether the
suite changed the tracked worktree.  Projection regeneration is a separate
explicit release step; this runner never repairs generated output.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]
REPO_ROOT = APP_ROOT.parent
REQUIREMENTS_PATH = APP_ROOT / "requirements-foundation.txt"
CONTRACT_PATH = APP_ROOT / "data/operations/full-regression-runner-r1.json"
NATURAL_WINDOW_MIN_SECONDS = 4 * 60 * 60
TEST_DISCOVERY_ARGS = ("-m", "unittest", "discover", "-s", "tests", "-p", "test*.py")
VERSION_IMPORTS = {"sympy": "sympy", "z3-solver": "z3", "jsonschema": "jsonschema"}
FOUNDATION_PYTHON_ENV_VAR = "IGNITION_FOUNDATION_PYTHON"
ISOLATED_ENV_PREFIX = "ignition-135-foundation-"
RAN_RE = re.compile(r"Ran\s+(\d+)\s+tests?\s+in\s+([0-9.]+)s")
FAILURE_RE = re.compile(r"failures=(\d+)")
ERROR_RE = re.compile(r"errors=(\d+)")
SKIP_RE = re.compile(r"skipped=(\d+)")


class RunnerContractError(RuntimeError):
    """Raised when the canonical runner contract cannot be established."""


def relative_to_repo(path: Path, repo_root: Path = REPO_ROOT) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def discover_repository_root(explicit: str | Path | None = None) -> tuple[Path, Path]:
    """Return ``(repo_root, application_root)`` without consulting cwd."""

    repo_root = Path(explicit).expanduser().resolve() if explicit else REPO_ROOT
    app_root = repo_root / "ignition"
    if not (app_root / "tests").is_dir() or not (app_root / "tools").is_dir():
        raise RunnerContractError(f"repository root does not contain the formal ignition tree: {repo_root}")
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RunnerContractError(f"repository root is not a Git checkout: {repo_root}")
    git_root = Path(completed.stdout.strip()).resolve()
    if git_root != repo_root:
        raise RunnerContractError(f"Git toplevel mismatch: expected {repo_root}, observed {git_root}")
    return repo_root, app_root


def canonical_environment(
    app_root: Path,
    python_executable: str | Path | None = None,
) -> dict[str, str]:
    """Build the explicit module and executable path for the test environment.

    Several existing validator profiles intentionally use the portable
    ``python3`` argv rather than embedding an interpreter path.  When the
    runner executes an isolated venv through an absolute path, the child
    validators must nevertheless resolve that same venv.  Prepending the
    execution interpreter's directory makes the environment boundary explicit
    without changing the tracked profiles or mutating the host Python.
    """

    entries = [app_root, app_root / "tests", app_root / "tools/foundation"]
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        entries.extend(Path(item) for item in existing.split(os.pathsep) if item)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in entries)
    if python_executable is not None:
        executable_dir = str(Path(python_executable).expanduser().absolute().parent)
        inherited_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(
            item for item in (executable_dir, inherited_path) if item
        )
    return env


def interpreter_identity(python_executable: str | Path) -> dict[str, Any]:
    """Read interpreter identity without importing project dependencies."""

    # Keep the venv launcher symlink intact. Resolving ``bin/python`` to the
    # base interpreter would erase the venv context and falsely report a
    # non-isolated environment on macOS.
    executable = Path(python_executable).expanduser().absolute()
    probe = (
        "import json, platform, sys; "
        "print(json.dumps({"
        "'executable': sys.executable, 'prefix': sys.prefix, "
        "'base_prefix': sys.base_prefix, 'version': platform.python_version()"
        "}, sort_keys=True))"
    )
    completed = subprocess.run(
        [str(executable), "-c", probe],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RunnerContractError(
            f"cannot inspect Python interpreter {executable}: {completed.stderr.strip()}"
        )
    try:
        identity = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RunnerContractError(f"invalid interpreter identity from {executable}") from exc
    identity["path"] = str(executable)
    identity["isolated"] = identity.get("prefix") != identity.get("base_prefix")
    return identity


def provision_isolated_environment(
    *,
    requirements_path: Path = REQUIREMENTS_PATH,
    base_python: str | Path | None = None,
) -> tuple[Path, tempfile.TemporaryDirectory[str], dict[str, Any]]:
    """Create the existing Task134-style temporary foundation venv.

    The returned TemporaryDirectory must be held by the caller until the test
    process exits. The venv is deliberately outside the repository and is never
    persisted in a receipt.
    """

    bootstrap = Path(base_python or sys.executable).expanduser().resolve()
    holder = tempfile.TemporaryDirectory(prefix=ISOLATED_ENV_PREFIX)
    environment_root = Path(holder.name) / "venv"
    created = subprocess.run(
        [str(bootstrap), "-m", "venv", str(environment_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if created.returncode != 0:
        holder.cleanup()
        raise RunnerContractError(f"isolated venv creation failed: {created.stderr.strip()}")
    executable = environment_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed = subprocess.run(
        [
            str(executable),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            str(requirements_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if installed.returncode != 0:
        detail = installed.stderr.strip() or installed.stdout.strip()
        holder.cleanup()
        raise RunnerContractError(f"isolated dependency installation failed: {detail}")
    return executable, holder, {
        "mode": "provisioned_temporary_foundation_venv",
        "install_performed": True,
        "path_persisted": False,
        "bootstrap_python": str(bootstrap),
    }


def prepare_execution_environment(
    *,
    repo_root: Path,
    app_root: Path,
    python_executable: str | Path | None = None,
    provision_isolated: bool = False,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None, dict[str, Any]]:
    """Resolve a reusable isolated interpreter or explicitly provision one."""

    configured = python_executable or os.environ.get(FOUNDATION_PYTHON_ENV_VAR)
    if configured and provision_isolated:
        raise RunnerContractError("choose an existing isolated Python or --provision-isolated, not both")
    if configured:
        executable = Path(configured).expanduser().absolute()
        if not executable.is_file():
            raise RunnerContractError(f"configured isolated Python is missing: {executable}")
        if repo_root == executable or repo_root in executable.parents:
            raise RunnerContractError("isolated Python must live outside the formal repository")
        identity = interpreter_identity(executable)
        if not identity.get("isolated"):
            raise RunnerContractError(
                f"configured Python is not isolated: {executable}; use --provision-isolated"
            )
        return executable, None, {
            "mode": "reused_existing_isolated_python",
            "install_performed": False,
            "path_persisted": False,
        }
    if not provision_isolated:
        raise RunnerContractError(
            f"isolated execution is required; provide --python, {FOUNDATION_PYTHON_ENV_VAR}, or --provision-isolated"
        )
    executable, holder, metadata = provision_isolated_environment(
        requirements_path=app_root / "requirements-foundation.txt"
    )
    return executable, holder, metadata


def parse_requirements(path: Path = REQUIREMENTS_PATH) -> list[dict[str, str]]:
    requirements: list[dict[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            requirements.append({"name": name.strip(), "version": version.strip()})
        else:
            requirements.append({"name": line, "version": ""})
    return requirements


def dependency_preflight(
    *,
    requirements_path: Path = REQUIREMENTS_PATH,
    import_module=importlib.util.find_spec,
    version_lookup=importlib.metadata.version,
    python_executable: str | Path | None = None,
) -> dict[str, Any]:
    """Check declared dependencies without installing or modifying anything."""

    requirements = parse_requirements(requirements_path)
    target = Path(python_executable).expanduser().absolute() if python_executable else None
    if target is not None:
        probe = (
            "import importlib.metadata, importlib.util, json, sys; "
            "requirements=json.loads(sys.argv[1]); mapping=json.loads(sys.argv[2]); "
            "rows=[]; errors=[]; "
            "\nfor req in requirements:\n"
            "    name=req['name']; module=mapping.get(name, name.replace('-', '_')); "
            "    found=importlib.util.find_spec(module) is not None; observed=None; "
            "    \n    if found:\n"
            "        \n        try: observed=importlib.metadata.version(name)\n"
            "        except importlib.metadata.PackageNotFoundError: found=False\n"
            "    version_ok=(not req['version']) or observed == req['version']; "
            "    rows.append({'name':name,'module':module,'required_version':req['version'],'observed_version':observed,'installed':found,'version_match':version_ok}); "
            "    \n    if not found: errors.append(name + ': missing')\n"
            "    elif not version_ok: errors.append(name + ': expected ' + req['version'] + ', observed ' + str(observed))\n"
            "print(json.dumps({'requirements':rows,'errors':errors}, sort_keys=True))"
        )
        completed = subprocess.run(
            [str(target), "-c", probe, json.dumps(requirements), json.dumps(VERSION_IMPORTS)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            rows = []
            errors = [f"{target}: dependency probe failed: {completed.stderr.strip()}"]
        else:
            try:
                payload = json.loads(completed.stdout)
                rows = payload.get("requirements", [])
                errors = payload.get("errors", [])
            except json.JSONDecodeError:
                rows = []
                errors = [f"{target}: dependency probe returned invalid JSON"]
        identity = interpreter_identity(target)
        if not identity.get("isolated"):
            errors.append("interpreter is not isolated")
        return {
            "requirements_file": relative_to_repo(requirements_path),
            "python_executable": str(target),
            "isolated": bool(identity.get("isolated")),
            "status": "PASS" if not errors else "FAIL",
            "requirements": rows,
            "errors": errors,
            "install_performed": False,
            "isolated_environment_required": True,
        }
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for requirement in requirements:
        name = requirement["name"]
        module_name = VERSION_IMPORTS.get(name, name.replace("-", "_"))
        try:
            found = import_module(module_name) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            found = False
        observed_version: str | None = None
        if found:
            try:
                observed_version = version_lookup(name)
            except importlib.metadata.PackageNotFoundError:
                found = False
        version_ok = not requirement["version"] or observed_version == requirement["version"]
        row = {
            "name": name,
            "module": module_name,
            "required_version": requirement["version"],
            "observed_version": observed_version,
            "installed": found,
            "version_match": version_ok,
        }
        rows.append(row)
        if not found:
            errors.append(f"{name}: missing")
        elif not version_ok:
            errors.append(f"{name}: expected {requirement['version']}, observed {observed_version}")
    return {
        "requirements_file": relative_to_repo(requirements_path),
        "python_executable": sys.executable,
        "isolated": sys.prefix != sys.base_prefix,
        "status": "PASS" if not errors else "FAIL",
        "requirements": rows,
        "errors": errors,
        "install_performed": False,
        "isolated_environment_required": True,
    }


def git_status(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RunnerContractError(f"git status failed: {completed.stderr.strip()}")
    return [line for line in completed.stdout.splitlines() if line]


def git_head(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RunnerContractError(f"git rev-parse failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def parse_unittest_result(stdout: str, stderr: str, process_returncode: int) -> dict[str, Any]:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    ran_matches = list(RAN_RE.finditer(combined))
    ran = ran_matches[-1] if ran_matches else None
    tests_run = int(ran.group(1)) if ran else None
    runtime_seconds = float(ran.group(2)) if ran else None
    nonempty_lines = [line.strip() for line in combined.splitlines() if line.strip()]
    summary_text = nonempty_lines[-1] if nonempty_lines else ""
    failures = int(FAILURE_RE.search(summary_text).group(1)) if FAILURE_RE.search(summary_text) else 0
    errors = int(ERROR_RE.search(summary_text).group(1)) if ERROR_RE.search(summary_text) else 0
    skipped = int(SKIP_RE.search(summary_text).group(1)) if SKIP_RE.search(summary_text) else 0
    if "OK" in summary_text and failures == 0 and errors == 0:
        status = "PASS" if process_returncode == 0 and skipped == 0 else "FAIL"
    elif "FAILED" in summary_text or process_returncode != 0:
        status = "FAIL"
    else:
        status = "PARSE_FAILED"
    return {
        "status": status,
        "process_returncode": process_returncode,
        "tests_run": tests_run,
        "runtime_seconds": runtime_seconds,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "summary": summary_text,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stdout_bytes": len(stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(stderr.encode("utf-8", errors="replace")),
    }


def _write_capture(output_dir: Path, name: str, content: str) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def run_full_regression(
    *,
    repo_root: str | Path | None = None,
    output_dir: str | Path | None = None,
    python_executable: str | Path | None = None,
    provision_isolated: bool = False,
    run=subprocess.run,
) -> dict[str, Any]:
    """Run the existing unittest suite under the canonical root contract."""

    resolved_repo, app_root = discover_repository_root(repo_root)
    before = git_status(resolved_repo)
    result: dict[str, Any] = {
        "schema_version": "ignition-full-regression-result-r1",
        "runner": relative_to_repo(HERE),
        "repository_root": str(resolved_repo),
        "application_root": str(app_root),
        "working_directory": relative_to_repo(app_root, resolved_repo),
        "head_sha": git_head(resolved_repo),
        "runner_bootstrap_python": sys.executable,
        "command": None,
        "display_command": "python3 ignition/tools/run_full_regression.py --provision-isolated",
        "natural_window": {
            "minimum_supported_seconds": NATURAL_WINDOW_MIN_SECONDS,
            "watchdog_used": False,
            "process_completed_naturally": False,
        },
        "clean_before": not before,
        "before_status": before,
    }
    if before:
        result.update({"status": "PRECONDITION_FAILED", "exit_code": 2})
        return result

    holder: tempfile.TemporaryDirectory[str] | None = None
    try:
        execution_python, holder, environment = prepare_execution_environment(
            repo_root=resolved_repo,
            app_root=app_root,
            python_executable=python_executable,
            provision_isolated=provision_isolated,
        )
        result["execution_environment"] = environment
        result["execution_python"] = str(execution_python)
        result["python_version"] = interpreter_identity(execution_python)["version"]
        result["command"] = [str(execution_python), *TEST_DISCOVERY_ARGS]
        dependencies = dependency_preflight(
            requirements_path=app_root / "requirements-foundation.txt",
            python_executable=execution_python,
        )
        result["dependency_preflight"] = dependencies
        if dependencies["status"] != "PASS":
            result.update({"status": "PREFLIGHT_FAILED", "exit_code": 2})
            return result

        env = canonical_environment(app_root, execution_python)
        started = time.monotonic()
        completed = run(
            [str(execution_python), *TEST_DISCOVERY_ARGS],
            cwd=app_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        elapsed = time.monotonic() - started
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        parsed = parse_unittest_result(stdout, stderr, completed.returncode)
        after = git_status(resolved_repo)
        tree_clean = not after
        result.update(parsed)
        result["elapsed_seconds"] = round(elapsed, 3)
        result["natural_window"]["process_completed_naturally"] = True
        result["clean_after"] = tree_clean
        result["after_status"] = after
        result["generated_output_drift"] = sorted(set(before) | set(after))
        result["projection_preflight"] = "REQUIRED_SEPARATE_STEP"
        if output_dir is not None:
            capture_root = Path(output_dir).expanduser().resolve()
            if capture_root == resolved_repo or resolved_repo in capture_root.parents:
                raise RunnerContractError("capture output must be outside the repository")
            result["stdout_path"] = _write_capture(capture_root, "full-regression.stdout.txt", stdout)
            result["stderr_path"] = _write_capture(capture_root, "full-regression.stderr.txt", stderr)
        passed = (
            completed.returncode == 0
            and parsed["status"] == "PASS"
            and parsed["tests_run"] is not None
            and parsed["failures"] == 0
            and parsed["errors"] == 0
            and parsed["skipped"] == 0
            and tree_clean
        )
        result["status"] = "PASS" if passed else "FAIL"
        result["exit_code"] = 0 if passed else 1
        return result
    except (OSError, RunnerContractError) as exc:
        result.update({"status": "PREFLIGHT_FAILED", "exit_code": 2, "error": str(exc)})
        return result
    finally:
        if holder is not None:
            holder.cleanup()


def contract_summary() -> dict[str, Any]:
    return {
        "schema_version": "ignition-full-regression-runner-r1",
        "task_id": "IGNITION-20260822-135",
        "runner": relative_to_repo(HERE),
        "repository_root_discovery": "script_path_then_git_toplevel; never cwd-derived",
        "application_root": "ignition",
        "canonical_working_directory": "ignition",
        "python": "isolated execution interpreter; reuse --python or provision only with --provision-isolated",
        "dependency_preflight": "ignition/requirements-foundation.txt exact declared versions checked inside the execution interpreter; missing/mismatched dependencies fail closed",
        "isolated_environment": "temporary venv outside repository using the existing Task134 procedure; reuse via --python or IGNITION_FOUNDATION_PYTHON; no system Python mutation",
        "command": "python3 ignition/tools/run_full_regression.py --provision-isolated",
        "natural_window_minimum_seconds": NATURAL_WINDOW_MIN_SECONDS,
        "watchdog": "none; outer orchestration may observe but must not kill the process",
        "capture": "stdout and stderr captured; optional files outside repository; sha256 always recorded",
        "clean_tree": "must be clean before and after; any tracked/untracked mutation is FAIL",
        "generated_output_drift": "reported by before/after git status; projection preflight is a separate explicit step",
        "exit_semantics": {
            "0": "PASS with parsed tests, failures=0, errors=0, skips=0 and clean tree",
            "1": "natural unittest failure/error/skip, parse failure, or post-run tree mutation",
            "2": "dirty precondition, missing/mismatched declared dependency, or runner contract failure"
        },
        "prohibited": ["skip laundering", "xfail laundering", "expectedFailure laundering", "blanket ignore", "automatic regeneration during suite"]
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="formal repository root; defaults to the root derived from this script")
    parser.add_argument("--output-dir", help="optional capture directory outside the formal repository")
    parser.add_argument("--python", dest="python_executable", help="existing isolated Python executable to reuse")
    parser.add_argument("--provision-isolated", action="store_true", help="create a temporary pinned foundation venv outside the repository")
    parser.add_argument("--contract", action="store_true", help="print the runner contract without executing tests")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.contract:
            print(json.dumps(contract_summary(), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        result = run_full_regression(
            repo_root=args.repo_root,
            output_dir=args.output_dir,
            python_executable=args.python_executable,
            provision_isolated=args.provision_isolated,
        )
    except (OSError, RunnerContractError, ValueError) as exc:
        print(json.dumps({"schema_version": "ignition-full-regression-result-r1", "status": "RUNNER_ERROR", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
