from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_federation.local_executor_census import LocalExecutorCensusError, validate_census, validate_path


ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data/operations/iterations/138/local-executor-census-r1.json"


class LocalExecutorCensusTests(unittest.TestCase):
    def test_census_is_valid_and_selection_is_deterministic(self) -> None:
        summary = validate_path(CENSUS)
        self.assertTrue(summary["safe"])
        self.assertEqual(summary["selection_status"], "NO_SAFE_CANDIDATE")
        self.assertIsNone(summary["selected_executor_id"])

    def test_admission_cannot_promote_non_agent_tool(self) -> None:
        data = json.loads(CENSUS.read_text(encoding="utf-8"))
        gh = next(item for item in data["candidates"] if item["executor_id"] == "tool.github-cli")
        gh["admission_status"] = "ADMITTED"
        with self.assertRaises(LocalExecutorCensusError):
            validate_census(data)

    def test_secret_like_auth_fields_are_rejected(self) -> None:
        data = json.loads(CENSUS.read_text(encoding="utf-8"))
        data["candidates"][0]["auth"]["api_key_presence"] = False
        temporary = CENSUS.with_name(".local-executor-census-test-invalid.json")
        temporary.write_text(json.dumps(data), encoding="utf-8")
        try:
            with self.assertRaises(LocalExecutorCensusError):
                validate_path(temporary)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
