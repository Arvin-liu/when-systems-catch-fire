from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator

from tools.toolbox_execution_pareto_frontier import MAX_INPUT_BYTES, ParetoInputError, analyze


FIXTURE = Path(__file__).parent / "fixtures/toolbox-execution-pareto-frontier/matched-candidates-r0.json"
TOOL = Path(__file__).resolve().parents[1] / "tools/toolbox_execution_pareto_frontier.py"


class ExecutionCandidateParetoFrontierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.raw = FIXTURE.read_bytes()

    def test_paired_frontier_keeps_tradeoff_and_marks_dominated_and_below_floor(self) -> None:
        result = analyze(self.raw)
        self.assertEqual(result["analysis_status"], "COMPARABLE_CALLER_DECLARED_MEASUREMENTS_NOT_AUTHENTICATED")
        self.assertEqual(result["quality_floor_pass_rate_fraction"], "3/4")
        self.assertEqual(result["frontier_candidate_ids"], ["baseline", "higher-pass-rate"])
        by_id = {row["candidate_id"]: row for row in result["candidates"]}
        self.assertEqual(by_id["baseline"]["mean_resource_cost_fraction"], "10/1")
        self.assertEqual(by_id["higher-pass-rate"]["pass_rate_fraction"], "1/1")
        self.assertEqual(by_id["dominated"]["status"], "DOMINATED")
        self.assertEqual(by_id["dominated"]["dominated_by"], ["baseline"])
        self.assertEqual(by_id["below-quality-floor"]["status"], "BELOW_BASELINE_PASS_RATE")
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["non_claims"]["statistical_significance_established"])
        self.assertFalse(result["non_claims"]["route_or_candidate_selected"])

    def test_missing_cost_preserves_unknown_and_suppresses_frontier(self) -> None:
        document = copy.deepcopy(self.document)
        document["candidates"][1]["observations"][0]["resource_cost"] = None
        result = analyze(json.dumps(document).encode())
        self.assertEqual(result["analysis_status"], "COMPARISON_UNDETERMINED_COST_MISSING")
        self.assertEqual(result["frontier_status"], "NOT_COMPUTED_MISSING_COST")
        self.assertEqual(result["frontier_candidate_ids"], [])
        self.assertEqual(
            next(row for row in result["candidates"] if row["candidate_id"] == "higher-pass-rate")["mean_resource_cost_fraction"],
            None,
        )

    def test_rejects_unpaired_rows_and_unknown_or_unhashable_outcome(self) -> None:
        document = copy.deepcopy(self.document)
        document["candidates"][1]["observations"][0]["case_id"] = "different-case"
        with self.assertRaisesRegex(ParetoInputError, "do not match the paired case/trial set"):
            analyze(json.dumps(document).encode())

        document = copy.deepcopy(self.document)
        document["candidates"][0]["observations"][0]["outcome"] = {"result": "PASS"}
        with self.assertRaisesRegex(ParetoInputError, "outcome must be PASS or FAIL"):
            analyze(json.dumps(document).encode())

    def test_rejects_bool_cost_duplicate_candidate_and_duplicate_key(self) -> None:
        document = copy.deepcopy(self.document)
        document["candidates"][0]["observations"][0]["resource_cost"] = True
        with self.assertRaisesRegex(ParetoInputError, "must be a non-negative JSON number or null"):
            analyze(json.dumps(document).encode())

        document = copy.deepcopy(self.document)
        document["candidates"].append(copy.deepcopy(document["candidates"][0]))
        with self.assertRaisesRegex(ParetoInputError, "duplicate candidate_id"):
            analyze(json.dumps(document).encode())

        with self.assertRaisesRegex(ParetoInputError, "duplicate JSON key"):
            analyze(b'{"schema_version":"x","schema_version":"y"}')

    def test_cli_emits_one_receipt_and_rejects_overflow(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL), "--stdin"],
            input=self.raw,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        self.assertEqual(json.loads(completed.stdout)["frontier_candidate_ids"], ["baseline", "higher-pass-rate"])

        with self.assertRaisesRegex(ParetoInputError, "input exceeds"):
            analyze(b" " * (MAX_INPUT_BYTES + 1))

    def test_input_and_output_match_the_published_schemas(self) -> None:
        schema_root = Path(__file__).resolve().parents[1] / "schemas/operations"
        input_schema = json.loads((schema_root / "execution-candidate-pareto-input-r0.schema.json").read_text(encoding="utf-8"))
        output_schema = json.loads((schema_root / "execution-candidate-pareto-output-r0.schema.json").read_text(encoding="utf-8"))
        result = analyze(self.raw)
        self.assertEqual(list(Draft202012Validator(input_schema).iter_errors(self.document)), [])
        self.assertEqual(list(Draft202012Validator(output_schema).iter_errors(result)), [])


if __name__ == "__main__":
    unittest.main()
