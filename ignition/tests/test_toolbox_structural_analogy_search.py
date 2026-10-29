from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator = None


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import toolbox_structural_analogy_search as TOOL  # noqa: E402


TOOL_PATH = IGNITION_ROOT / "tools/toolbox_structural_analogy_search.py"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-structural-analogy-search-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-structural-analogy-search-output-r0.schema.json"
FIXTURE_PATH = IGNITION_ROOT / "tests/fixtures/toolbox-structural-analogy-search/real-task-input-r0.json"


def request() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class StructuralAnalogySearchTests(unittest.TestCase):
    def test_real_tool_input_ranks_exact_structure_before_extra_relation_and_reversal(self) -> None:
        data = request()
        result = TOOL.search_structural_analogies(data)
        rows = result["candidates"]
        self.assertEqual(result["status"], "STRUCTURAL_OVERLAP_CANDIDATES_FOUND")
        self.assertEqual([row["candidate_id"] for row in rows], [
            "a_pipeline_validation", "b_pipeline_with_extra_relation", "c_reversed_relations",
        ])
        self.assertEqual(rows[0]["source_relation_coverage_fraction"], "3/3")
        self.assertEqual(rows[0]["mapped_target_relation_precision_fraction"], "3/3")
        self.assertEqual(rows[1]["extra_mapped_target_relation_count"], 1)
        self.assertEqual(rows[1]["mapped_target_relation_precision_fraction"], "3/4")
        self.assertEqual(rows[2]["matched_source_relation_count"], 0)
        self.assertEqual(rows[2]["status"], "NO_MAPPED_RELATION_OVERLAP")
        self.assertTrue(all(hyp["status"] == "REQUIRES_TARGET_DOMAIN_VALIDATION" for row in rows for mapping in row["best_mappings"] for hyp in mapping["transfer_hypotheses"]))
        for key in ("source_authority_verified", "target_domain_validated", "analogy_is_evidence", "authority_transferred", "execution_authorized"):
            self.assertFalse(result[key])
        self.assertFalse(result["surface_text_used"])

    def test_no_role_compatible_mapping_keeps_actual_relation_denominator_and_null_precision(self) -> None:
        data = request()
        data["target_candidates"] = [data["target_candidates"][0]]
        candidate = data["target_candidates"][0]
        candidate["nodes"][0]["role_class"] = "RESOURCE"
        result = TOOL.search_structural_analogies(data)
        row = result["candidates"][0]
        self.assertEqual(row["status"], "NO_ROLE_COMPATIBLE_NODE_MAPPING")
        self.assertEqual(row["source_relation_coverage_fraction"], "0/3")
        self.assertIsNone(row["mapped_target_relation_precision_fraction"])
        self.assertEqual(row["unmapped_target_relation_count_range"], [3, 3])
        self.assertEqual(result["status"], "NO_STRUCTURAL_OVERLAP_CANDIDATES_FOUND")

    def test_symmetric_best_mappings_report_tie_count_and_truncate_detail(self) -> None:
        nodes = [{"node_id": f"s{i}", "role_class": "ACTOR"} for i in range(2)]
        targets = [{"node_id": f"t{i}", "role_class": "ACTOR"} for i in range(4)]
        data = {
            "schema_version": TOOL.SCHEMA_VERSION,
            "task_id": "symmetric-tie",
            "source_structure": {
                "structure_id": "source",
                "domain_id": "domain_a",
                "nodes": nodes,
                "relations": [{"relation_id": "srel", "subject_id": "s0", "relation_type": "r", "object_id": "s1"}],
            },
            "relation_mappings": [{"source_relation_type": "r", "target_relation_type": "mapped_r"}],
            "target_candidates": [{
                "candidate_id": "symmetric",
                "structure_id": "target",
                "domain_id": "domain_b",
                "nodes": targets,
                "relations": [
                    {"relation_id": f"t{i}{j}", "subject_id": f"t{i}", "relation_type": "mapped_r", "object_id": f"t{j}"}
                    for i in range(4) for j in range(4) if i != j
                ],
            }],
        }
        row = TOOL.search_structural_analogies(data)["candidates"][0]
        self.assertEqual(row["best_mapping_tie_count"], 12)
        self.assertEqual(len(row["best_mappings"]), TOOL.MAX_REPORTED_TIES)
        self.assertTrue(row["best_mapping_ties_truncated"])

    def test_unknown_surface_labels_and_duplicate_relation_mapping_are_rejected(self) -> None:
        data = request()
        data["source_structure"]["nodes"][0]["label"] = "similar words do not count"
        with self.assertRaises(TOOL.StructuralAnalogySearchError):
            TOOL.search_structural_analogies(data)
        data = request()
        data["relation_mappings"].append({"source_relation_type": "initiates", "target_relation_type": "starts"})
        with self.assertRaises(TOOL.StructuralAnalogySearchError):
            TOOL.search_structural_analogies(data)

    def test_noninjective_relation_mapping_and_unknown_relation_endpoint_are_rejected(self) -> None:
        data = request()
        data["relation_mappings"][1]["target_relation_type"] = "triggers"
        with self.assertRaisesRegex(TOOL.StructuralAnalogySearchError, "one-to-one"):
            TOOL.search_structural_analogies(data)
        data = request()
        data["source_structure"]["relations"][0]["object_id"] = "missing"
        with self.assertRaisesRegex(TOOL.StructuralAnalogySearchError, "endpoints"):
            TOOL.search_structural_analogies(data)

    def test_mapping_budget_fails_closed(self) -> None:
        nodes = [{"node_id": f"s{i}", "role_class": "ACTOR"} for i in range(8)]
        target_nodes = [{"node_id": f"t{i}", "role_class": "ACTOR"} for i in range(8)]
        graph = {
            "structure_id": "target",
            "domain_id": "domain_b",
            "nodes": target_nodes,
            "relations": [{"relation_id": "target_edge", "subject_id": "t0", "relation_type": "mapped_r", "object_id": "t1"}],
        }
        data = {
            "schema_version": TOOL.SCHEMA_VERSION,
            "task_id": "budget-control",
            "source_structure": {"structure_id": "source", "domain_id": "domain_a", "nodes": nodes,
                                 "relations": [{"relation_id": "source_edge", "subject_id": "s0", "relation_type": "r", "object_id": "s1"}]},
            "relation_mappings": [{"source_relation_type": "r", "target_relation_type": "mapped_r"}],
            "target_candidates": [dict(graph, candidate_id=f"candidate{i}") for i in range(5)],
        }
        with self.assertRaisesRegex(TOOL.StructuralAnalogySearchError, "comparison budget"):
            TOOL.search_structural_analogies(data)

    def test_duplicate_json_keys_are_rejected_before_analysis(self) -> None:
        payload = b'{"schema_version":"toolbox-structural-analogy-search-input-r0","schema_version":"other"}'
        with self.assertRaisesRegex(TOOL.StructuralAnalogySearchError, "duplicate JSON key"):
            TOOL.analyze_bytes(payload)

    def test_oversized_stdin_and_uncovered_source_relation_types_are_rejected(self) -> None:
        with self.assertRaisesRegex(TOOL.StructuralAnalogySearchError, "256 KiB"):
            TOOL.analyze_bytes(b" " * (TOOL.MAX_INPUT_BYTES + 1))
        data = request()
        data["relation_mappings"] = data["relation_mappings"][:2]
        with self.assertRaisesRegex(TOOL.StructuralAnalogySearchError, "cover exactly"):
            TOOL.search_structural_analogies(data)

    def test_cli_smoke_and_output_schema(self) -> None:
        data = request()
        completed = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
            input=json.dumps(data).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=IGNITION_ROOT.parent,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8"))
        output = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(output["task_id"], data["task_id"])
        if Draft202012Validator is None:
            self.skipTest("jsonschema is unavailable; stdlib-only CLI contract was exercised")
        input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(input_schema).validate(data)
        Draft202012Validator(output_schema).validate(output)

    def test_input_schema_rejects_extra_surface_fields_when_available(self) -> None:
        if Draft202012Validator is None:
            self.skipTest("jsonschema is unavailable")
        schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        data = request()
        data["source_structure"]["nodes"][0]["free_text"] = "not part of structural matching"
        errors = list(Draft202012Validator(schema).iter_errors(data))
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
