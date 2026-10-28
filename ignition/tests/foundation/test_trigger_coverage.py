#!/usr/bin/env python3
"""Layer B trigger coverage (Task 107 §4).

Proves the governed classification source is the single source of truth for the
authoritative-input boundary, and that Layer B (heavy Foundation validation)
actually triggers on authoritative-input changes -- the exact gap that let the
drift lie dormant through PR #160/#161.

Scenarios covered here:
  * 5  authoritative input change must trigger (not silently skip) Layer B.
  * the preflight authoritative set == the discovery engine's authoritative boundary
    (single governed source, contract §4 Layer B).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "tools" / "foundation"))
import validate_repository_path_classification as preflight  # noqa: E402
import run_foundation_ci  # noqa: E402

CJK = ("统一函数总表/", "统一案例总表/")

# NOTE: this test is intentionally stdlib-only (no import of the discovery engine)
# so it can run in the fast Layer A preflight without pulling heavy dependencies.


def _discovery_nonauthoritative_prefixes() -> tuple[str, ...]:
    """Read the discovery engine's governed input boundary without importing it."""
    src = (ROOT / "tools/foundation/adjudicate_nonfunction_claims.py").read_text(encoding="utf-8")
    m = re.search(r"NON_AUTHORITATIVE_PREFIXES\s*=\s*\(([^)]*)\)", src, re.S)
    if not m:
        raise RuntimeError("could not locate NON_AUTHORITATIVE_PREFIXES in discovery engine")
    items = re.findall(r'"([^"]+)"', m.group(1))
    return tuple(items)


def _discovery_authoritative_prefixes() -> tuple[str, ...]:
    """Read the discovery engine's authoritative (fresh claim) source prefixes.

    These are the two CJK master tables; everything else scanned is either a
    governed/non-authoritative record or historical/audit context.
    """
    src = (ROOT / "tools/foundation/adjudicate_nonfunction_claims.py").read_text(encoding="utf-8")
    # Match the HISTORICAL_OR_AUDIT_RECORD prefix tuple's authoritative (CJK) entries:
    #   path.startswith(("统一函数总表/", "统一案例总表/", "reports/", ...))
    m = re.search(r'path\.startswith\(\(([^)]*)\)', src, re.S)
    if not m:
        raise RuntimeError("could not locate authoritative prefix tuple in discovery engine")
    items = re.findall(r'"([^"]+)"', m.group(1))
    # The authoritative (fresh claim) sources are exactly the two CJK tables.
    return tuple(p for p in items if p in CJK)


class AuthoritativeBoundaryTest(unittest.TestCase):
    def test_authoritative_set_is_two_cjk_tables(self) -> None:
        self.assertEqual(preflight.AUTHORITATIVE_PREFIXES, CJK)

    def test_discovery_nonauthoritative_disjoint_from_authoritative(self) -> None:
        nonauth = _discovery_nonauthoritative_prefixes()
        for p in nonauth:
            self.assertFalse(
                any(p.startswith(c) or c.startswith(p) for c in CJK),
                f"{p!r} overlaps the authoritative allowlist",
            )

    def test_preflight_never_mislabels_nonauthoritative_as_authoritative(self) -> None:
        nonauth = _discovery_nonauthoritative_prefixes()
        for p in nonauth:
            sample = p.rstrip("/") + "/sample.md"
            cat, _ = preflight.classify(sample)
            self.assertNotEqual(
                cat, "AUTHORITATIVE_CLAIM_INPUT",
                f"{sample!r} must not be classified authoritative (anti-backflow)",
            )

    def test_preflight_authoritative_matches_discovery_boundary(self) -> None:
        # The discovery engine scans claim fragments for every path NOT in
        # NON_AUTHORITATIVE_PREFIXES; among those, only the two CJK tables are the
        # fresh authoritative (E-promotable) sources. The preflight must agree exactly.
        self.assertEqual(set(preflight.AUTHORITATIVE_PREFIXES), set(CJK))
        for p in CJK:
            cat, _ = preflight.classify(p + "x.md")
            self.assertEqual(cat, "AUTHORITATIVE_CLAIM_INPUT")

    def test_discovery_authoritative_is_two_cjk_tables(self) -> None:
        self.assertEqual(_discovery_authoritative_prefixes(), CJK)


class LayerBTriggerTest(unittest.TestCase):
    """Scenario 5: an authoritative-input change must reach Layer B.

    Reads .github/workflows/foundation-validation.yml and asserts the heavy
    Foundation validation is not gated behind a narrow `paths:` filter that would
    omit the authoritative CJK-table directories (the PR #160/#161 gap).
    """

    def _on_block(self) -> str:
        path = REPO_ROOT / ".github/workflows/foundation-validation.yml"
        return path.read_text(encoding="utf-8")

    def test_layer_b_runs_task106_propagation_proof(self) -> None:
        names = {item.name for item in run_foundation_ci.foundation_checks(sys.executable)}
        self.assertIn("validate-propagation-reconciliation", names,
                      "Layer B runner must retain the task-106 propagation reconciliation step (contract §6)")

    def test_layer_b_triggers_on_authoritative_change(self) -> None:
        text = self._on_block()
        # Within the `on:` trigger, find any `paths:` list and ensure it either
        # is absent (broad trigger) or explicitly includes the authoritative dirs.
        # Match `paths:` only inside a trigger block (heuristic: lines indented under
        # `pull_request:` / `push:`). We scan for a `paths:` whose listed globs omit CJK.
        has_narrow_paths = False
        for m in re.finditer(r"paths:\s*\n((?:\s*-\s*[^\n]+\n)+)", text):
            block = m.group(1)
            listed = re.findall(r"-\s*([^\n#]+)", block)
            listed = [x.strip() for x in listed]
            if listed and not any(lp.startswith(c.rstrip("/")) for lp in listed for c in CJK):
                has_narrow_paths = True
                break
        self.assertFalse(
            has_narrow_paths,
            "foundation-validation.yml must not use a narrow `paths:` filter that "
            "would omit the authoritative CJK-table directories (contract §3.4)",
        )

    def test_final_main_witness_script_path_matches_working_directory(self) -> None:
        text = self._on_block()
        self.assertIn("working-directory: ignition", text)
        self.assertIn("python3 tools/operations/write_final_main_witness.py", text)
        self.assertNotIn("python3 ignition/tools/operations/write_final_main_witness.py", text)
        self.assertTrue((ROOT / "tools/operations/write_final_main_witness.py").is_file())

    def test_final_main_witness_installs_dependencies_in_its_own_job(self) -> None:
        workflow = self._on_block()
        parts = workflow.split("\n  final_main_witness:\n", 1)
        self.assertEqual(len(parts), 2, "final-main witness job is missing")
        witness = parts[1]
        install = "python3 -m pip install -r requirements-foundation.txt"
        invoke = "python3 tools/operations/write_final_main_witness.py"
        self.assertIn("actions/setup-python@v5", witness)
        self.assertIn(install, witness, "the witness job must install its own dependencies")
        self.assertIn(invoke, witness)
        self.assertLess(witness.index(install), witness.index(invoke))
        self.assertIn("jsonschema==4.26.0", (ROOT / "requirements-foundation.txt").read_text(encoding="utf-8"))


class FoundationCiRunnerTest(unittest.TestCase):
    def test_suite_inventory_is_unique_and_sequential(self) -> None:
        checks = run_foundation_ci.foundation_checks(sys.executable)
        names = [item.name for item in checks]
        self.assertEqual(len(checks), 57)
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("adjudicate-nonfunction-claims", names)
        self.assertIn("test-human-front-door", names)
        self.assertIn("validate-propagation-reconciliation", names)

    def test_generated_output_negative_authority_runs_on_every_foundation_head(self) -> None:
        checks = run_foundation_ci.foundation_checks(sys.executable)
        authority_check = next(item for item in checks if item.name == "test-era-resolver-and-generated-output-authority")
        self.assertIn("tests.test_generated_output_authority_negative", authority_check.argv)

    def test_runner_continues_after_failure_and_retains_per_command_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-runner-test-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            checks = [
                run_foundation_ci.Check(
                    "intentional-failure",
                    (sys.executable, "-c", "print('first ran'); raise SystemExit(7)"),
                ),
                run_foundation_ci.Check(
                    "run-after-failure",
                    (sys.executable, "-c", "from pathlib import Path; Path('second-ran').write_text('yes')"),
                ),
            ]
            summary = run_foundation_ci.execute_checks(
                checks,
                repo_root=repo,
                app_root=app,
                evidence_dir=evidence,
            )
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(summary["checks_total"], 2)
            self.assertEqual(summary["checks_failed"], 1)
            self.assertEqual((app / "second-ran").read_text(encoding="utf-8"), "yes")
            rows = [json.loads(line) for line in (evidence / "command-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["status"] for row in rows], ["FAIL", "PASS"])
            self.assertTrue(all((evidence / row[stream]["path"]).is_file() for row in rows for stream in ("stdout", "stderr")))


    def test_runner_declares_resource_policies_and_job_timeout(self) -> None:
        checks = run_foundation_ci.foundation_checks(sys.executable)
        names = [item.name for item in checks]
        self.assertEqual(len(checks), 57)
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(item.timeout_seconds == 45 * 60 for item in checks))
        self.assertTrue(all(item.output_limit_bytes == 256 * 1024 for item in checks))
        workflow = (REPO_ROOT / ".github" / "workflows" / "foundation-validation.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^    timeout-minutes:\s*240\s*$")

    def test_launch_error_fails_but_does_not_hide_a_later_independent_check(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-launch-error-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            marker = app / "after-launch-error"
            checks = [
                run_foundation_ci.Check("missing-executable", (str(root / "missing-command"),)),
                run_foundation_ci.Check(
                    "run-after-launch-error",
                    (sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')"),
                ),
            ]
            summary = run_foundation_ci.execute_checks(checks, repo_root=repo, app_root=app, evidence_dir=evidence)
            rows = [json.loads(line) for line in (evidence / "command-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual([row["status"] for row in rows], ["FAIL", "PASS"])
            self.assertEqual(rows[0]["returncode"], 127)
            self.assertIn("FileNotFoundError", rows[0]["runner_error"])
            self.assertTrue(marker.is_file())

    def test_success_with_margin_records_full_stream_integrity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-success-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            payload = b"bounded-success\n"
            code = "import sys; sys.stdout.buffer.write(" + repr(payload) + "); sys.stdout.flush()"
            summary = run_foundation_ci.execute_checks(
                [run_foundation_ci.Check("success-with-margin", (sys.executable, "-c", code), timeout_seconds=0.5)],
                repo_root=repo,
                app_root=app,
                evidence_dir=evidence,
            )
            row = json.loads((evidence / "command-ledger.jsonl").read_text(encoding="utf-8"))
            stream = (evidence / row["stdout"]["path"]).read_bytes()
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(row["status"], "PASS")
            self.assertLess(row["duration_seconds"], 0.5)
            self.assertEqual(stream, payload)
            self.assertEqual(row["stdout"]["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(row["stdout"]["observed_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertTrue(row["stdout"]["eof_reached"])

    def test_stdout_and_stderr_caps_fail_with_verifiable_partial_evidence(self) -> None:
        for stream_name in ("stdout", "stderr"):
            with self.subTest(stream=stream_name), tempfile.TemporaryDirectory(prefix="foundation-ci-output-cap-") as directory:
                root = Path(directory)
                repo = root / "repo"
                app = repo / "ignition"
                app.mkdir(parents=True)
                evidence = root / "evidence"
                code = (
                    "import sys\n"
                    "stream = sys." + stream_name + ".buffer\n"
                    "block = b'z' * 4096\n"
                    "while True:\n"
                    "    stream.write(block)\n"
                    "    stream.flush()\n"
                )
                summary = run_foundation_ci.execute_checks(
                    [run_foundation_ci.Check("flood-" + stream_name, (sys.executable, "-c", code), output_limit_bytes=1024)],
                    repo_root=repo,
                    app_root=app,
                    evidence_dir=evidence,
                )
                row = json.loads((evidence / "command-ledger.jsonl").read_text(encoding="utf-8"))
                capture = row[stream_name]
                saved = (evidence / capture["path"]).read_bytes()
                self.assertEqual(summary["status"], "FAIL")
                self.assertEqual(row["status"], "OUTPUT_LIMIT_EXCEEDED")
                self.assertTrue(capture["truncated"])
                self.assertEqual(capture["bytes"], 1024)
                self.assertEqual(capture["sha256"], hashlib.sha256(saved).hexdigest())
                self.assertGreater(capture["observed_bytes"], capture["bytes"])
                self.assertEqual(len(capture["observed_sha256"]), 64)
                self.assertTrue(capture["eof_reached"])

    @unittest.skipUnless(os.name == "posix", "process-group cleanup proof requires POSIX")
    def test_timeout_terminates_and_reaps_child_process_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-timeout-tree-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            child_pid_path = root / "grandchild.pid"
            child_code = "import time; time.sleep(60)"
            parent_code = (
                "import subprocess, sys, time; from pathlib import Path; "
                "child=subprocess.Popen([sys.executable, '-c', sys.argv[2]]); "
                "Path(sys.argv[1]).write_text(str(child.pid)); time.sleep(60)"
            )
            summary = run_foundation_ci.execute_checks(
                [run_foundation_ci.Check(
                    "timeout-tree",
                    (sys.executable, "-c", parent_code, str(child_pid_path), child_code),
                    timeout_seconds=0.5,
                )],
                repo_root=repo,
                app_root=app,
                evidence_dir=evidence,
            )
            row = json.loads((evidence / "command-ledger.jsonl").read_text(encoding="utf-8"))
            self.assertTrue(child_pid_path.is_file(), "the fixture must start its descendant before timeout")
            child_pid = int(child_pid_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(row["status"], "TIMEOUT")
            self.assertIn("SIGTERM", row["signals_sent"])
            self.assertTrue(row["process_tree_cleanup_complete"])
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                try:
                    os.kill(child_pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                self.fail(f"descendant {child_pid} survived process-group cleanup")

    @unittest.skipUnless(os.name == "posix", "signal cancellation proof requires POSIX")
    def test_signal_cancellation_writes_partial_summary_and_not_executed_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-cancel-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            marker = root / "first-check-finished"
            long_check_started = root / "long-check-started"
            script = r"""
import importlib.util, sys, threading
from pathlib import Path
runner_path, repo_root, app_root, evidence_dir, marker, long_check_started = sys.argv[1:]
spec = importlib.util.spec_from_file_location("run_foundation_ci", runner_path)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)
event = threading.Event()
runner.install_cancellation_handlers(event)
checks = [
    runner.Check("first", (sys.executable, "-c", "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('done')", marker)),
    runner.Check("long-running", (
        sys.executable, "-c",
        "import pathlib,sys,time; pathlib.Path(sys.argv[1]).write_text('started'); time.sleep(60)",
        long_check_started,
    ), timeout_seconds=30),
    runner.Check("unknown-after-cancel", (sys.executable, "-c", "raise SystemExit(0)")),
]
runner.execute_checks(checks, repo_root=Path(repo_root), app_root=Path(app_root), evidence_dir=Path(evidence_dir), cancel_event=event)
"""
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    script,
                    str(ROOT / "tools/foundation/run_foundation_ci.py"),
                    str(repo),
                    str(app),
                    str(evidence),
                    str(marker),
                    str(long_check_started),
                ],
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline and process.poll() is None and not long_check_started.is_file():
                    time.sleep(0.02)
                self.assertTrue(marker.is_file(), "first check did not finish before cancellation")
                self.assertTrue(long_check_started.is_file(), "long-running check did not start before cancellation")
                process.send_signal(signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=10)
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGTERM)
                    try:
                        process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
            summary = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
            rows = [json.loads(line) for line in (evidence / "command-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(process.returncode, 0, f"stdout={stdout}\nstderr={stderr}")
            self.assertEqual(summary["status"], "CANCELLED")
            self.assertFalse(summary["full_suite_completed"])
            self.assertEqual(summary["checks_total"], 3)
            self.assertEqual(summary["checks_executed"], 2)
            self.assertEqual(summary["checks_not_executed"], 1)
            self.assertEqual([row["status"] for row in rows], ["PASS", "CANCELLED", "NOT_EXECUTED"])
            self.assertTrue(rows[1]["process_tree_cleanup_complete"])

if __name__ == "__main__":
    unittest.main()
