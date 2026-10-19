#!/usr/bin/env python3
"""Run only the exact test modules selected by a validated component plan."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import platform
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CHECKOUT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
from tools.operations.route_component_validation import (  # noqa: E402
    MAP_PATH,
    MAP_SCHEMA_PATH,
    REGISTRY_PATH,
    TOPOLOGY_PATH,
    RoutingBlocked,
    build_exact_plan,
    canonical_json,
    digest_json,
    load_json,
    _validate_checkout_binding,
    _module_file,
    _path_without_symlink_components,
    validate_checkout_file,
    validate_validation_map,
)

COMMANDS: dict[str, tuple[str, ...]] = {
    "build_human_results_check": ("tools/governance/build_human_results.py", "--check"),
    "run_self_correction_check": ("tools/governance/run_self_correction.py", "--check"),
    "build_knowledge_experience_check": ("tools/governance/build_knowledge_experience.py", "--check"),
    "validate_human_visibility": ("tools/governance/validate_human_visibility.py",),
    "validate_knowledge_experience": ("tools/governance/validate_knowledge_experience.py",),
    "validate_human_front_door": ("tools/validate_human_front_door.py",),
    "validate_fire_seeds_check": ("tools/publication/validate_fire_seeds.py", "--check"),
    "build_claim_browsers_check": ("tools/governance/build_claim_browsers.py", "--check"),
    "generate_overall_architecture_check": ("tools/generate_overall_architecture.py", "--check"),
}

NATIVE_COMMANDS: dict[str, dict[str, Any]] = {
    "validate_l4_lean_foundation": {
        "executable": "lake",
        "arguments": ["env", "lean", "Foundation.lean"],
        "working_directory": "formal/lean",
    },
}


class EvidenceTestResult(unittest.TextTestResult):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.started_at = time.time()
        self.skip_evidence: list[dict[str, str]] = []
        self.expected_failure_evidence: list[str] = []
        self.unexpected_success_evidence: list[str] = []
        self.test_outcomes: list[dict[str, str]] = []

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        self.test_outcomes.append({"test": test.id(), "status": "passed"})
        super().addSuccess(test)

    def addFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        self.test_outcomes.append({"test": test.id(), "status": "failure"})
        super().addFailure(test, err)

    def addError(self, test: unittest.case.TestCase, err: tuple) -> None:
        self.test_outcomes.append({"test": test.id(), "status": "error"})
        super().addError(test, err)

    def addSkip(self, test: unittest.case.TestCase, reason: str) -> None:
        self.skip_evidence.append({"test": test.id(), "reason": reason})
        self.test_outcomes.append({"test": test.id(), "status": "skipped", "reason": reason})
        super().addSkip(test, reason)

    def addExpectedFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        self.expected_failure_evidence.append(test.id())
        self.test_outcomes.append({"test": test.id(), "status": "expected_failure"})
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:
        self.unexpected_success_evidence.append(test.id())
        self.test_outcomes.append({"test": test.id(), "status": "unexpected_success"})
        super().addUnexpectedSuccess(test)


def run_modules(
    modules: list[str], *, repo_root: Path, import_roots: list[str] | None = None,
    verbosity: int = 2, validation_sha: str | None = None,
) -> dict[str, Any]:
    if not modules:
        raise RoutingBlocked("an empty module list cannot be reported as a successful test run")
    expected_paths: dict[str, Path] = {}
    for module in modules:
        expected_paths[module] = _module_file(
            repo_root, module, import_roots, validation_sha=validation_sha,
        )

    search_paths: list[str] = [str(repo_root.resolve())]
    for relative in import_roots or []:
        candidate = _path_without_symlink_components(
            repo_root, repo_root / relative, f"test import root {relative}"
        )
        if not candidate.is_dir():
            raise RoutingBlocked(f"selected test import root is missing: {relative}")
        search_paths.append(str(candidate))

    loader = unittest.defaultTestLoader
    previous_path = list(sys.path)
    try:
        sys.path[:0] = search_paths
        # Import origins are checked before unittest loads the modules. A module
        # that shadows a registered target from another search path blocks.
        for module, expected in expected_paths.items():
            spec = importlib.util.find_spec(module)
            if spec is None or spec.origin is None:
                raise RoutingBlocked(f"selected test module has no importable origin: {module}")
            origin = Path(spec.origin).resolve()
            if origin != expected.resolve():
                raise RoutingBlocked(
                    f"selected test module import origin differs from its registered checkout file: "
                    f"{module}: {origin} != {expected}"
                )
            if module in sys.modules:
                loaded = getattr(sys.modules[module], "__file__", None)
                if not loaded or Path(loaded).resolve() != expected.resolve():
                    raise RoutingBlocked(f"selected test module was already loaded from another path: {module}")
        suite = loader.loadTestsFromNames(modules)
        for module, expected in expected_paths.items():
            loaded = sys.modules.get(module)
            actual = getattr(loaded, "__file__", None) if loaded else None
            if not actual or Path(actual).resolve() != expected.resolve():
                raise RoutingBlocked(f"selected test module did not load from its registered file: {module}")
        return _run_suite(suite, modules, verbosity=verbosity)
    finally:
        sys.path[:] = previous_path


def _run_suite(
    suite: unittest.TestSuite,
    modules: list[str],
    *,
    verbosity: int = 2,
    stream: Any = None,
) -> dict[str, Any]:
    report_stream = stream if stream is not None else io.StringIO()
    runner = unittest.TextTestRunner(verbosity=verbosity, resultclass=EvidenceTestResult, stream=report_stream)
    started = time.monotonic()
    result = runner.run(suite)
    duration = time.monotonic() - started
    report = report_stream.getvalue() if hasattr(report_stream, "getvalue") else ""
    if stream is None and report:
        sys.stdout.write(report)
        sys.stdout.flush()
    complete = (
        result.testsRun > 0
        and not result.skipped
        and not result.expectedFailures
        and not result.unexpectedSuccesses
    )
    return {
        "modules": modules,
        "tests_run": result.testsRun,
        "tests_executed": result.testsRun - len(result.skipped),
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "skip_evidence": result.skip_evidence,
        "expected_failures": result.expected_failure_evidence,
        "unexpected_successes": result.unexpected_success_evidence,
        "test_outcomes": sorted(result.test_outcomes, key=lambda item: (item["test"], item["status"])),
        "test_report": report,
        "test_report_sha256": hashlib.sha256(report.encode("utf-8")).hexdigest(),
        "test_report_bytes": len(report.encode("utf-8")),
        "duration_seconds": round(duration, 6),
        "successful": result.wasSuccessful() and complete,
        "status": (
            "NO_TESTS_COLLECTED" if result.testsRun == 0
            else "NO_EXECUTED_TESTS" if result.testsRun == len(result.skipped)
            else "INCOMPLETE_WITH_RECORDED_SKIPS" if result.skipped and result.wasSuccessful()
            else "INCOMPLETE_WITH_EXPECTED_FAILURES" if result.expectedFailures and result.wasSuccessful()
            else "PASSED" if result.wasSuccessful() and complete
            else "FAILED"
        ),
    }


def run_commands(
    command_ids: list[str], *, repo_root: Path, validation_sha: str | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    _path_without_symlink_components(
        repo_root, repo_root / "ignition", "Ignition command root"
    )
    ignition_root = (repo_root / "ignition").resolve()
    if not ignition_root.is_dir():
        raise RoutingBlocked(f"Ignition command root is missing from the selected checkout: {ignition_root}")
    for command_id in command_ids:
        argv = COMMANDS.get(command_id)
        if argv is not None:
            script = (repo_root / "ignition").joinpath(*argv[0].split("/"))
            validate_checkout_file(
                repo_root, script, label=f"registered validation command {command_id}",
                validation_sha=validation_sha,
            )
            full_argv = [sys.executable, *argv]
            command_cwd = ignition_root
            recorded_cwd = "ignition"
        else:
            native = NATIVE_COMMANDS.get(command_id)
            if native is None:
                raise RoutingBlocked(f"validation target requests an unregistered command: {command_id}")
            executable = native["executable"]
            if shutil.which(executable) is None:
                raise RoutingBlocked(f"registered validation executable is unavailable: {executable}")
            relative_cwd = Path(native["working_directory"])
            command_cwd = _path_without_symlink_components(
                repo_root, repo_root / "ignition" / relative_cwd,
                f"registered validation working directory {relative_cwd}",
            )
            if not command_cwd.is_dir():
                raise RoutingBlocked(f"registered validation working directory is missing: {relative_cwd}")
            full_argv = [executable, *native["arguments"]]
            recorded_cwd = relative_cwd.as_posix()
        # Revalidate the exact executable path immediately before launching it.
        if argv is not None:
            validate_checkout_file(
                repo_root, script, label=f"registered validation command {command_id}",
                validation_sha=validation_sha,
            )
        started = time.monotonic()
        completed = subprocess.run(full_argv, cwd=command_cwd, capture_output=True, check=False)
        duration = time.monotonic() - started
        stdout, stderr = completed.stdout, completed.stderr
        if stdout:
            sys.stdout.buffer.write(stdout)
            sys.stdout.buffer.flush()
        if stderr:
            sys.stderr.buffer.write(stderr)
            sys.stderr.buffer.flush()
        results.append({
            "command_id": command_id,
            "argv": full_argv,
            "working_directory": recorded_cwd,
            "exit_code": completed.returncode,
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            "stdout_bytes": len(stdout),
            "stderr_bytes": len(stderr),
            "duration_seconds": round(duration, 6),
        })
    return results


def run_plan(
    plan: dict[str, Any], *, repo_root: Path = CHECKOUT_ROOT, manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or load_json(MAP_PATH)
    if plan.get("mode") not in {"TARGETED", "FULL"}:
        raise RoutingBlocked(f"target runner requires a validated TARGETED or FULL plan, got {plan.get('mode')!r}")
    supplied_hash = plan.get("plan_sha256")
    unhashed = dict(plan)
    unhashed.pop("plan_sha256", None)
    if not supplied_hash or digest_json(unhashed) != supplied_hash:
        raise RoutingBlocked("component validation plan hash is missing or invalid")
    if plan.get("validation_map_sha256") != digest_json(manifest):
        raise RoutingBlocked("validation map digest does not match the selected plan")

    source = plan.get("source")
    if (
        not isinstance(source, dict)
        or not isinstance(source.get("base_sha"), str)
        or not isinstance(source.get("head_sha"), str)
        or not isinstance(source.get("validation_sha"), str)
    ):
        raise RoutingBlocked("target execution requires exact Git base, PR head, and validation commit SHAs")
    _validate_checkout_binding(repo_root, source["base_sha"], source["head_sha"], source["validation_sha"])
    expected_plan = build_exact_plan(repo_root, source["base_sha"], source["head_sha"], source["validation_sha"])
    if canonical_json(expected_plan) != canonical_json(plan):
        raise RoutingBlocked("target execution plan does not match the exact Git diff and current validation authority")

    registry = load_json(REGISTRY_PATH)
    topology = load_json(TOPOLOGY_PATH)
    schema = load_json(MAP_SCHEMA_PATH)
    validate_validation_map(registry, topology, manifest, schema)
    target_by_id = {target["target_id"]: target for target in manifest["targets"]}
    target_ids = plan.get("selected_target_ids")
    if not isinstance(target_ids, list) or not target_ids or len(target_ids) != len(set(target_ids)):
        raise RoutingBlocked("selected target list is empty, malformed, or duplicated")

    target_results: list[dict[str, Any]] = []
    for target_id in target_ids:
        target = target_by_id.get(target_id)
        if target is None:
            raise RoutingBlocked(f"plan selects unregistered target {target_id!r}")
        for module in target["modules"]:
            _module_file(
                repo_root, module, target.get("import_roots", []), validation_sha=source["validation_sha"],
            )
        tests = run_modules(
            target["modules"],
            repo_root=repo_root,
            import_roots=target.get("import_roots", []),
            validation_sha=source["validation_sha"],
        )
        commands = run_commands(
            target.get("command_ids", []), repo_root=repo_root, validation_sha=source["validation_sha"],
        )
        result = {
            "tests": tests,
            "commands": commands,
            "successful": tests["successful"] and all(item["exit_code"] == 0 for item in commands),
        }
        result["target_id"] = target_id
        result["domain"] = target["domain"]
        target_results.append(result)

    _validate_checkout_binding(
        repo_root, source["base_sha"], source["head_sha"], source["validation_sha"]
    )

    receipt: dict[str, Any] = {
        "schema_version": "1.0.0",
        "head_sha": plan.get("source", {}).get("head_sha"),
        "base_sha": plan.get("source", {}).get("base_sha"),
        "validation_sha": plan.get("source", {}).get("validation_sha"),
        "python_version": platform.python_version(),
        "plan_sha256": supplied_hash,
        "validation_map_sha256": plan["validation_map_sha256"],
        "target_results": target_results,
        "claim_ceiling": "repository test results for the exact selected modules only",
    }
    receipt["receipt_sha256"] = digest_json(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=CHECKOUT_ROOT)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        receipt = run_plan(plan, repo_root=args.repo_root.resolve())
    except (OSError, json.JSONDecodeError, RoutingBlocked, ValueError) as exc:
        print(f"component target validation blocked: {exc}", file=sys.stderr)
        return 2
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    if any(not result["successful"] for result in receipt["target_results"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
