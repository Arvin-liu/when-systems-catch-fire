from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT))
sys.path.insert(0, str(IGNITION_ROOT / "tools/operations"))
from tools.toolbox_execution_pareto_frontier import analyze  # noqa: E402
import plan_ignition_operation_run as planner  # noqa: E402


DATA = IGNITION_ROOT / "data/operations"
TOOL_ID = "maintenance.summarize_execution_candidate_pareto_frontier"
SOURCE_PATH = DATA / "toolbox-crossref-citation-matcher-c1-evidence-r0.json"
EVALUATOR_PATH = DATA / "toolbox-execution-pareto-crossref-evaluator-r0.json"
INPUT_PATH = DATA / "toolbox-execution-pareto-crossref-input-r0.json"
OUTPUT_PATH = DATA / "toolbox-execution-pareto-crossref-output-r0.json"
PROFILE_PATH = DATA / "toolbox-execution-pareto-crossref-route-profile-r0.json"
ROUTE_EVIDENCE_PATH = DATA / "toolbox-execution-pareto-crossref-route-evidence-r0.json"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _planner_sha256(result: dict) -> str:
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256(canonical)


class ExecutionParetoCrossrefRealTaskTests(unittest.TestCase):
    def test_captured_crossref_task_is_replayable_and_route_is_explicit(self) -> None:
        source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
        evaluator_bytes = EVALUATOR_PATH.read_bytes()
        evaluator = json.loads(evaluator_bytes)
        input_bytes = INPUT_PATH.read_bytes()
        document = json.loads(input_bytes)
        output_bytes = OUTPUT_PATH.read_bytes()
        output = json.loads(output_bytes)
        route_evidence = json.loads(ROUTE_EVIDENCE_PATH.read_text(encoding="utf-8"))
        candidate_catalog = json.loads((DATA / "toolbox-candidate-cards-r0.json").read_text(encoding="utf-8"))
        pareto_card = next(card for card in candidate_catalog["candidates"] if card["tool_id"] == TOOL_ID)
        c1_comparison = json.loads((DATA / "toolbox-execution-pareto-frontier-c1-comparison-r0.json").read_text(encoding="utf-8"))

        self.assertEqual(pareto_card["availability"], "EXPERIMENTAL_AVAILABLE")
        self.assertEqual(pareto_card["lifecycle"], "EXPERIMENTAL")
        self.assertEqual(pareto_card["evidence_level"], "REAL_TASK_OUTCOME")
        self.assertFalse(pareto_card["router_selectable_by_default"])
        self.assertEqual(c1_comparison["status"], "COMPARISON_UNKNOWN")
        self.assertTrue(c1_comparison["paired_real_task_comparison"].startswith("NOT_RUN_FOR_EXISTING_COMPARATORS"))
        self.assertEqual(evaluator["task_set"]["source_input_sha256"], source["input_sha256"])
        self.assertEqual(document["evaluation_context"]["task_set_sha256"], source["input_sha256"])
        self.assertEqual(document["evaluation_context"]["evaluator_sha256"], _sha256(evaluator_bytes))
        self.assertEqual(document["evaluation_context"]["evaluation_id"], evaluator["evaluation_id"])
        input_schema = json.loads((IGNITION_ROOT / "schemas/operations/execution-candidate-pareto-input-r0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            list(Draft202012Validator(input_schema).iter_errors(document)),
            [],
        )

        target_doi = source["reference_record"]["previously_recorded_doi"]
        specialized_rows = source["specialized_adapter"]["candidates"]
        generic_rows = source["generic_adapter"]["records"]
        paired_case = "crossref-gap001-citation-lookup"
        paired_trial = "captured-live-task-2026-10-27"
        variants = [
            ("generic_only", generic_rows, 1),
            ("specialized_only", specialized_rows, 1),
            ("specialized_plus_generic", specialized_rows + generic_rows, 2),
            ("specialized_plus_generic_recheck", specialized_rows + generic_rows + generic_rows, 3),
        ]
        expected_candidates = []
        for candidate_id, rows, get_count in variants:
            outcome = "PASS" if any(row.get("doi") == target_doi for row in rows) else "FAIL"
            expected_candidates.append({
                "candidate_id": candidate_id,
                "candidate_ref": f"captured Crossref route variant {candidate_id}",
                "observations": [{
                    "case_id": paired_case,
                    "trial_id": paired_trial,
                    "outcome": outcome,
                    "resource_cost": get_count,
                    "evidence_ref": "ignition/data/operations/toolbox-crossref-citation-matcher-c1-evidence-r0.json",
                }],
            })
        self.assertEqual(document["candidates"], expected_candidates)
        self.assertEqual(document["baseline_candidate_id"], "generic_only")

        recomputed = analyze(input_bytes)
        self.assertEqual(recomputed, output)
        output_schema = json.loads((IGNITION_ROOT / "schemas/operations/execution-candidate-pareto-output-r0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            list(Draft202012Validator(output_schema).iter_errors(output)),
            [],
        )
        self.assertEqual(output["analysis_status"], "COMPARABLE_CALLER_DECLARED_MEASUREMENTS_NOT_AUTHENTICATED")
        self.assertEqual(output["quality_floor_pass_rate_fraction"], "0/1")
        self.assertEqual(output["frontier_candidate_ids"], ["specialized_only"])
        self.assertFalse(output["execution_authorized"])

        profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        default = planner.plan_tool_route(profile)
        explicit = planner.plan_tool_route(profile, include_experimental_tool_ids=[TOOL_ID])
        self.assertEqual(default["decision"], "INCOMPLETE")
        self.assertEqual(default["selected_tools"], [])
        self.assertEqual(explicit["decision"], "COMPLETE")
        self.assertEqual([row["tool_id"] for row in explicit["selected_tools"]], [TOOL_ID])
        self.assertFalse(explicit["execution_authorized"])
        self.assertFalse(explicit["selected_tools"][0]["permissions"]["network"])

        current_catalog_sha = planner.git_blob_sha1(planner.EXPERIMENTAL_TOOL_CARDS_PATH.read_bytes())
        self.assertEqual(route_evidence["candidate_catalog_git_blob_sha1"], current_catalog_sha)
        trials = {row["scenario"]: row for row in route_evidence["route_trials"]}
        for name, actual in (("default_off", default), ("explicit_allowlist", explicit)):
            record = trials[name]
            self.assertEqual(record["decision"], actual["decision"])
            self.assertEqual(record["selected_tool_ids"], [row["tool_id"] for row in actual["selected_tools"]])
            self.assertEqual(record["planner_output_sha256"], _planner_sha256(actual))
            self.assertFalse(record["execution_authorized"])
            self.assertEqual(record["router_provider_calls"], 0)
            self.assertFalse(record["candidate_invoked"])

        invocation = route_evidence["tool_invocation"]
        self.assertTrue(invocation["candidate_invoked"])
        self.assertEqual(invocation["tool_id"], TOOL_ID)
        self.assertEqual(invocation["input_sha256"], _sha256(input_bytes))
        self.assertEqual(invocation["output_sha256"], _sha256(output_bytes))
        self.assertEqual(invocation["execution_authorized_in_tool_output"], False)
        self.assertEqual(invocation["network_calls"], 0)


if __name__ == "__main__":
    unittest.main()
