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

import re
import json
import hashlib
import os
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
            first_stdout = rows[0]["stdout"]
            self.assertEqual((evidence / first_stdout["path"]).read_bytes(), b"first ran\n")
            self.assertEqual(first_stdout["retention"], "full")

    def test_runner_declares_bounded_resource_policies_and_job_timeout(self) -> None:
        checks = run_foundation_ci.foundation_checks(sys.executable)
        names = [item.name for item in checks]
        self.assertEqual(len(checks), 57)
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(item.timeout_seconds == 45 * 60 for item in checks))
        self.assertEqual(run_foundation_ci.OUTPUT_TAIL_BYTES, 256 * 1024)
        self.assertEqual(run_foundation_ci.MAX_OUTPUT_ARTIFACT_BYTES, 16 * 1024 * 1024)
        workflow = (REPO_ROOT / ".github" / "workflows" / "foundation-validation.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^    timeout-minutes:\s*240\s*$")

    def test_launch_error_fails_but_does_not_hide_a_later_independent_check(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-launch-error-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            missing = root / "missing-command"
            marker = app / "after-launch-error"
            checks = [
                run_foundation_ci.Check("missing-executable", (str(missing),)),
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
            first_stderr = (evidence / rows[0]["stderr"]["path"]).read_text(encoding="utf-8")
            self.assertIn(str(missing), first_stderr)
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
                [run_foundation_ci.Check("success-with-margin", (sys.executable, "-c", code), timeout_seconds=2.0)],
                repo_root=repo,
                app_root=app,
                evidence_dir=evidence,
            )
            row = json.loads((evidence / "command-ledger.jsonl").read_text(encoding="utf-8"))
            stream = (evidence / row["stdout"]["path"]).read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(row["status"], "PASS")
            self.assertLess(row["duration_seconds"], 2.0)
            self.assertEqual(stream, payload)
            self.assertEqual(row["stdout"]["sha256"], digest)
            self.assertEqual(row["stdout"]["stream_sha256"], digest)

    def test_stderr_artifact_is_bounded_and_keeps_verifiable_stream_integrity(self) -> None:
        block = b"z" * 4096
        total_bytes = run_foundation_ci.MAX_OUTPUT_ARTIFACT_BYTES + len(block)
        payload = block * (total_bytes // len(block))
        with tempfile.TemporaryDirectory(prefix="foundation-ci-stderr-bound-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            code = f"import sys; sys.stderr.buffer.write(b'z' * {len(payload)}); sys.stderr.flush()"
            summary = run_foundation_ci.execute_checks(
                [run_foundation_ci.Check("bounded-stderr", (sys.executable, "-c", code))],
                repo_root=repo,
                app_root=app,
                evidence_dir=evidence,
            )
            row = json.loads((evidence / "command-ledger.jsonl").read_text(encoding="utf-8"))
            capture = row["stderr"]
            saved = (evidence / capture["path"]).read_bytes()
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(row["status"], "PASS")
            self.assertEqual(capture["total_bytes"], len(payload))
            self.assertEqual(capture["bytes"], run_foundation_ci.OUTPUT_TAIL_BYTES)
            self.assertTrue(capture["truncated"])
            self.assertEqual(capture["retention"], "last_bytes")
            self.assertEqual(capture["sha256"], hashlib.sha256(saved).hexdigest())
            self.assertEqual(capture["stream_sha256"], hashlib.sha256(payload).hexdigest())

    def test_output_capture_retains_bounded_tail_and_distinguishes_hashes(self) -> None:
        pattern = b"0123456789"
        count = run_foundation_ci.MAX_OUTPUT_ARTIFACT_BYTES // len(pattern) + 100_000
        total_bytes = len(pattern) * count
        stream_digest = hashlib.sha256()
        digest_chunk = pattern * 10_000
        remaining = total_bytes
        while remaining:
            chunk = digest_chunk[: min(len(digest_chunk), remaining)]
            stream_digest.update(chunk)
            remaining -= len(chunk)
        expected_tail = (pattern * (run_foundation_ci.OUTPUT_TAIL_BYTES // len(pattern) + 1))[-run_foundation_ci.OUTPUT_TAIL_BYTES :]
        with tempfile.TemporaryDirectory(prefix="foundation-ci-output-test-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            check = run_foundation_ci.Check(
                "large-output",
                (sys.executable, "-c", f"import sys; sys.stdout.buffer.write(b'0123456789' * {count})"),
            )
            summary = run_foundation_ci.execute_checks(
                [check], repo_root=repo, app_root=app, evidence_dir=evidence,
            )
            row = json.loads((evidence / "command-ledger.jsonl").read_text(encoding="utf-8"))
            saved = (evidence / row["stdout"]["path"]).read_bytes()
            self.assertEqual(summary["status"], "PASS")
            self.assertEqual(row["stdout"]["total_bytes"], total_bytes)
            self.assertEqual(len(saved), run_foundation_ci.OUTPUT_TAIL_BYTES)
            self.assertTrue(row["stdout"]["truncated"])
            self.assertEqual(row["stdout"]["sha256"], hashlib.sha256(saved).hexdigest())
            self.assertEqual(row["stdout"]["stream_sha256"], stream_digest.hexdigest())
            self.assertEqual(row["stdout"]["retention"], "last_bytes")
            self.assertEqual(saved, expected_tail)

    @unittest.skipUnless(os.name == "posix", "process-group timeout test requires POSIX signals")
    def test_timeout_terminates_descendants_before_next_check(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-timeout-test-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            marker = app / "orphan-marker"
            child_script = (
                "import time; from pathlib import Path; time.sleep(0.7); "
                f"Path({str(marker)!r}).write_text('late', encoding='utf-8')"
            )
            parent_script = (
                "import signal, subprocess, sys, time\n"
                "stopping = False\n"
                f"child = subprocess.Popen([sys.executable, '-c', {child_script!r}])\n"
                "def stop(*_):\n"
                "    global stopping\n"
                "    stopping = True\n"
                "    child.terminate()\n"
                "signal.signal(signal.SIGTERM, stop)\n"
                "while not stopping:\n"
                "    time.sleep(0.02)\n"
                "child.wait()\n"
            )
            checks = [
                run_foundation_ci.Check("timeout-parent", (sys.executable, "-c", parent_script), timeout_seconds=0.15),
                run_foundation_ci.Check(
                    "following-check",
                    (sys.executable, "-c", "from pathlib import Path; Path('following-check').write_text('ran')"),
                ),
            ]
            summary = run_foundation_ci.execute_checks(
                checks, repo_root=repo, app_root=app, evidence_dir=evidence,
            )
            rows = [json.loads(line) for line in (evidence / "command-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            time.sleep(0.8)
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual([row["status"] for row in rows], ["TIMEOUT", "PASS"])
            self.assertTrue(rows[0]["process_group_terminated"])
            self.assertTrue(rows[0]["output_readers_complete"])
            self.assertFalse(marker.exists(), "a timed-out descendant must not keep running after the next check starts")
            self.assertTrue((app / "following-check").is_file())

    @unittest.skipUnless(os.name == "posix", "process-group cleanup test requires POSIX process groups")
    def test_successful_check_cannot_leave_a_detached_same_group_process_running(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-descendant-test-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            marker = app / "detached-marker"
            child_script = (
                "import time; from pathlib import Path; time.sleep(0.7); "
                f"Path({str(marker)!r}).write_text('late', encoding='utf-8')"
            )
            parent_script = (
                "import subprocess, sys; "
                f"subprocess.Popen([sys.executable, '-c', {child_script!r}], "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)"
            )
            checks = [
                run_foundation_ci.Check("detached-descendant", (sys.executable, "-c", parent_script)),
                run_foundation_ci.Check(
                    "following-check",
                    (sys.executable, "-c", "from pathlib import Path; Path('following-check').write_text('ran')"),
                ),
            ]
            summary = run_foundation_ci.execute_checks(
                checks, repo_root=repo, app_root=app, evidence_dir=evidence,
            )
            rows = [json.loads(line) for line in (evidence / "command-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            time.sleep(0.8)
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual([row["status"] for row in rows], ["PROCESS_GROUP_CLEANED", "PASS"])
            self.assertTrue(rows[0]["process_group_terminated"])
            self.assertFalse(marker.exists(), "an exited check's detached descendant must not outlive its process group")
            self.assertTrue((app / "following-check").is_file())

    @unittest.skipUnless(os.name == "posix", "signal reconciliation test requires POSIX signals")
    def test_sigterm_cancels_active_check_and_marks_remaining_checks_not_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="foundation-ci-cancel-test-") as directory:
            root = Path(directory)
            repo = root / "repo"
            app = repo / "ignition"
            app.mkdir(parents=True)
            evidence = root / "evidence"
            checks = [
                run_foundation_ci.Check(
                    "signal-parent",
                    (sys.executable, "-c", "import os, signal, time; os.kill(os.getppid(), signal.SIGTERM); time.sleep(30)"),
                ),
                run_foundation_ci.Check(
                    "must-not-run",
                    (sys.executable, "-c", "from pathlib import Path; Path('must-not-run').write_text('bad')"),
                ),
            ]
            summary = run_foundation_ci.execute_checks(
                checks, repo_root=repo, app_root=app, evidence_dir=evidence,
            )
            rows = [json.loads(line) for line in (evidence / "command-ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(summary["status"], "CANCELLED")
            self.assertEqual([row["status"] for row in rows], ["CANCELLED", "NOT_RUN_CANCELLED"])
            self.assertTrue(rows[0]["process_group_terminated"])
            self.assertFalse((app / "must-not-run").exists())


if __name__ == "__main__":
    unittest.main()
