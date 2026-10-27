from __future__ import annotations

import builtins
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


IGNITION = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION / "tools" / "toolbox_validate_q38_evidence_bundle.py"
FIXTURE_PATH = IGNITION / "tests" / "fixtures" / "toolbox-q38" / "pilot-q38-i1.json"
sys.dont_write_bytecode = True
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_validate_q38_evidence_bundle as gate  # noqa: E402


def pilot() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class Q38EvidenceBundleTests(unittest.TestCase):
    def assert_gate(self, bundle: dict, expected_code: int) -> dict:
        result = gate.validate_bundle(bundle)
        self.assertEqual(result["exit_code"], expected_code, result)
        return result

    def test_frozen_repository_pilot_passes_with_limited_claim_ceiling(self) -> None:
        result = self.assert_gate(pilot(), 0)
        self.assertEqual(result["exit_name"], "GATE_PASS")
        self.assertEqual(result["boundary"], "repository retrieval governance only; no mechanism or causal proof")

    def test_fail_closed_guards_reject_each_declared_attack_class(self) -> None:
        cases = []

        bad_schema = pilot()
        del bad_schema["task_id"]
        cases.append(("schema", bad_schema, 2))

        bad_seed = pilot()
        bad_seed["audited_search_seed"]["q37_exact_head"] = "a" * 40
        cases.append(("wrong frozen seed head", bad_seed, 3))

        support_only = pilot()
        support_only["search_plan"]["query_plan"][-1]["target_kind"] = "SUPPORT"
        cases.append(("unbalanced search plan", support_only, 4))

        deleted_negative = pilot()
        failed = next(item for item in deleted_negative["evidence_items"] if item["kind"] == "FAILED_RETRIEVAL")
        failed["kind"] = "SUPPORT"
        cases.append(("negative or failed result deleted", deleted_negative, 5))

        duplicate_family = pilot()
        duplicate_family["evidence_items"][2]["source_family"] = duplicate_family["evidence_items"][0]["source_family"]
        cases.append(("duplicate source family counted", duplicate_family, 6))

        invalid_duplicate_link = pilot()
        invalid_duplicate_link["evidence_items"][2]["source_family"] = invalid_duplicate_link["evidence_items"][0]["source_family"]
        invalid_duplicate_link["evidence_items"][2]["duplicate_of"] = "missing.evidence"
        cases.append(("unbound duplicate link", invalid_duplicate_link, 6))

        rights_bypass = pilot()
        rights_bypass["evidence_items"][0]["rights_status"] = "UNKNOWN"
        cases.append(("unknown rights published", rights_bypass, 7))

        stale = pilot()
        stale["evidence_items"][0]["freshness"].update(time_sensitive=True, status="STALE")
        cases.append(("stale time-sensitive evidence", stale, 8))

        unrepresentative = pilot()
        unrepresentative["conclusion"]["statement"] = "This applies to all populations."
        unrepresentative["evidence_items"][0]["representativeness"]["status"] = "NOT_REPRESENTATIVE"
        cases.append(("generalization without representativeness", unrepresentative, 9))

        quantity_vote = pilot()
        quantity_vote["conclusion"]["statement"] = "The case count proves truth."
        cases.append(("quantity vote", quantity_vote, 10))

        mechanism_upgrade = pilot()
        mechanism_upgrade["conclusion"]["statement"] = "The same mechanism in both domains is proven."
        cases.append(("mechanism upgrade", mechanism_upgrade, 11))

        stop_rewrite = pilot()
        stop_rewrite["stop_assessment"]["original_stop_condition"] = "Changed after retrieval."
        cases.append(("stop condition rewrite", stop_rewrite, 12))

        selective_exclusion = pilot()
        negative = next(item for item in selective_exclusion["evidence_items"] if item["kind"] == "COUNTEREXAMPLE")
        negative["selection_status"] = "EXCLUDED"
        negative["q39_export_required"] = False
        selective_exclusion["stop_assessment"]["independent_source_family_count"] = 3
        cases.append(("selective negative exclusion", selective_exclusion, 13))

        overclaim = pilot()
        overclaim["conclusion"]["claim_ceiling"] = "bounded repository retrieval with no mechanism statement"
        cases.append(("claim ceiling overreach", overclaim, 14))

        bad_digest = pilot()
        bad_digest["evidence_items"][0]["summary"] += " altered"
        cases.append(("provenance digest mismatch", bad_digest, 15))

        incomplete_log = pilot()
        incomplete_log["selection_log"][0]["action"] = "EXCLUDE"
        cases.append(("selection log integrity", incomplete_log, 16))

        missing_export = pilot()
        missing_export["q39_failure_exports"][0]["evidence_id"] = "ev.support.q37"
        cases.append(("Q39 export missing", missing_export, 17))

        overridden_counterevidence = pilot()
        overridden_counterevidence["conclusion"]["statement"] = "Counterexample overridden by support grade."
        cases.append(("counterevidence overridden", overridden_counterevidence, 18))

        future_as_of = pilot()
        future_as_of["evidence_items"][0]["freshness"]["as_of"] = "2026-07-22T17:31:00Z"
        cases.append(("future as-of time", future_as_of, 19))

        unbounded = pilot()
        unbounded["stop_assessment"]["status"] = "NOT_STOPPED"
        unbounded["stop_assessment"]["stopped_at"] = None
        cases.append(("not stopped", unbounded, 20))

        dangling_ref = pilot()
        dangling_ref["conclusion"]["unresolved_gap_refs"].append("gap.missing")
        cases.append(("dangling evidence gap reference", dangling_ref, 21))

        for label, bundle, expected in cases:
            with self.subTest(case=label):
                self.assert_gate(bundle, expected)

    def test_valid_duplicate_family_must_bind_to_an_included_canonical_record(self) -> None:
        bundle = pilot()
        original = bundle["evidence_items"][0]
        duplicate = bundle["evidence_items"][2]
        duplicate["source_family"] = original["source_family"]
        duplicate["duplicate_of"] = original["evidence_id"]
        bundle["evidence_items"].remove(duplicate)
        bundle["evidence_items"].insert(0, duplicate)
        bundle["stop_assessment"]["independent_source_family_count"] = 3
        self.assert_gate(bundle, 0)

    def test_missing_jsonschema_dependency_fails_closed(self) -> None:
        real_import = builtins.__import__

        def without_jsonschema(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("simulated missing jsonschema")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=without_jsonschema):
            result = gate.validate_bundle(pilot())
        self.assertEqual(result["exit_code"], 2)
        self.assertIn("refusing reduced validation", result["errors"][0])

    def test_cli_reads_only_bounded_stdin_rejects_duplicate_keys_and_does_not_write(self) -> None:
        raw = FIXTURE_PATH.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            ok = subprocess.run(
                [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
                input=raw,
                text=True,
                capture_output=True,
                cwd=temp,
                check=False,
            )
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertEqual(json.loads(ok.stdout)["tool_id"], "knowledge.validate_q38_i1_evidence_bundle")
            self.assertEqual(list(Path(temp).iterdir()), [])

            duplicate_keys = subprocess.run(
                [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
                input='{"task_id":"121Q38-I1","task_id":"121Q38-I1"}',
                text=True,
                capture_output=True,
                cwd=temp,
                check=False,
            )
            self.assertEqual(duplicate_keys.returncode, 2)
            self.assertIn("duplicate JSON object key", json.loads(duplicate_keys.stdout)["errors"][0])

            oversized = subprocess.run(
                [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
                input=" " * (gate.MAX_STDIN_BYTES + 1),
                text=True,
                capture_output=True,
                cwd=temp,
                check=False,
            )
            self.assertEqual(oversized.returncode, 2)
            self.assertIn("stdin exceeds", json.loads(oversized.stdout)["errors"][0])
            self.assertEqual(list(Path(temp).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
