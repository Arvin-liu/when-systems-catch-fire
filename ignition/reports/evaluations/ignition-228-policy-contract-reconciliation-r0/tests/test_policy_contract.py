from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

TASK228 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK228 / "tools"))

import build_reference_instruments  # noqa: E402
import validate_policy  # noqa: E402


POLICY_IDS = ["POLICY_F01_A", "POLICY_F01_B", "POLICY_F02_A", "POLICY_F02_B", "POLICY_F03_A", "POLICY_F03_B"]


def load_policy(policy_id: str) -> dict:
    return json.loads((TASK228 / "policies" / f"{policy_id}.json").read_text(encoding="utf-8"))


def mutate(policy: dict, operation: str) -> dict:
    result = copy.deepcopy(policy)
    if operation == "wrong_source_hash":
        result["evidence_basis"][0]["source_sha256"] = "0" * 64
    elif operation == "wrong_excerpt_hash":
        result["evidence_basis"][0]["locator"]["excerpt_sha256"] = "0" * 64
    elif operation == "condition_unit_drift":
        result["selector"]["rule"][0]["when"][0]["unit"] = "unexpected-unit"
    elif operation == "action_condition_drift":
        result["action_table"][0]["when"][0]["value"] = not result["action_table"][0]["when"][0]["value"]
    elif operation == "region_condition_drift":
        result["applicability"]["licensed_region"][0]["conditions"][0]["value"] = not result["applicability"]["licensed_region"][0]["conditions"][0]["value"]
    elif operation == "preserved_e1_reference":
        evidence_id = next(item["evidence_id"] for item in result["evidence_basis"] if item["source_type"] == "E1")
        preserved = result["preserved_rules"][0]
        preserved["evidence_refs"] = [evidence_id]
        link = next(row for row in result["provenance"]["links"] if row["element_type"] == "preserved_rule" and row["element_id"] == preserved["preservation_id"])
        link["evidence_refs"] = [evidence_id]
    elif operation == "parameter_unit_mismatch":
        parameter = next(parameter for action in result["action_table"] for parameter in action["action"]["parameters"] if parameter["binding"] == "input_ref")
        parameter["unit"] = "unexpected-unit"
    elif operation == "claim_outside_region":
        result["scope_ceiling"]["licensed_claims"][0]["region_refs"] = [result["applicability"]["out_of_scope"][0]["region_id"]]
    elif operation == "remove_provenance_link":
        result["provenance"]["links"].pop(0)
    elif operation == "second_empty_complement":
        original = result["applicability"]["out_of_scope"][0]
        result["applicability"]["out_of_scope"].append({**original, "region_id": original["region_id"] + "_SECOND"})
    elif operation == "fallback_condition":
        result["fallback"]["when"].append({"input_id": result["selector"]["required_inputs"][0]["input_id"], "operator": "eq", "value": False, "unit": None})
    else:
        raise AssertionError(f"Unknown adversarial fixture mutation: {operation}")
    return result


class PolicyContractConformanceTests(unittest.TestCase):
    def test_schema_and_all_six_candidates_pass(self) -> None:
        schema = validate_policy.load_json(validate_policy.SCHEMA_PATH)
        validate_policy.Draft202012Validator.check_schema(schema)
        for policy_id in POLICY_IDS:
            with self.subTest(policy_id=policy_id):
                self.assertEqual([], validate_policy.validate_policy(load_policy(policy_id)))

    def test_adversarial_negative_fixtures_fail_the_expected_rule(self) -> None:
        fixtures = json.loads((TASK228 / "tests/fixtures/adversarial-policy-fixtures.json").read_text(encoding="utf-8"))
        for fixture in fixtures:
            with self.subTest(fixture_id=fixture["fixture_id"]):
                candidate = mutate(load_policy(fixture["policy_id"]), fixture["mutation"])
                rule_ids = {finding["rule_id"] for finding in validate_policy.validate_policy(candidate)}
                self.assertIn(fixture["expected_rule_id"], rule_ids)

    def test_compiler_rebuild_is_byte_identical_and_target_blind(self) -> None:
        compiled, manifest = build_reference_instruments.compile_all()
        self.assertEqual(6, manifest["candidate_count"])
        self.assertFalse(manifest["target_access_during_build"])
        self.assertFalse(manifest["transfer_experiment_run"])
        self.assertFalse(manifest["revision_experiment_run"])
        for path, expected in compiled.items():
            with self.subTest(path=str(path.relative_to(TASK228))):
                self.assertTrue(path.exists())
                self.assertEqual(expected, path.read_bytes())

    def test_lf_locator_preserves_cr_bytes_and_final_unterminated_line(self) -> None:
        raw = "α\r\nbeta\nlast-without-newline".encode("utf-8")
        lines = validate_policy.source_lines_lf(raw)
        self.assertEqual(["α\r\n".encode(), b"beta\n", b"last-without-newline"], lines)
        self.assertEqual(raw, b"".join(lines))


if __name__ == "__main__":
    unittest.main()
