import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.validate_state_changelog import PROFILE_PATH, ROOT, validate


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "state-changelog-profile-r1.json"


def _replace_in_entry(source: str, ordinal: int, old: str, new: str) -> str:
    headings = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} — .+$", source, re.MULTILINE))
    start = headings[ordinal - 1].start()
    end = headings[ordinal].start() if ordinal < len(headings) else len(source)
    section = source[start:end]
    if old not in section:
        raise AssertionError(f"fixture marker not found in entry {ordinal}: {old}")
    return source[:start] + section.replace(old, new, 1) + source[end:]


class StateChangelogTests(unittest.TestCase):
    def test_current_log_is_valid(self):
        self.assertEqual([], validate())

    def test_missing_required_field_is_rejected(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = source.replace("- stale_knowledge:", "- stale_removed:", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        self.assertTrue(any("stale_knowledge" in error for error in errors), errors)

    def test_broken_repository_link_is_rejected(self):
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = source.replace("./AI-START-HERE.md", "./missing-state-entry.md", 1)
        path = ROOT / ".state-changelog-test.md"
        try:
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(any("broken repository link" in error for error in errors), errors)

    def test_profile_fixture_cases_preserve_historical_boundary(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual("ignition-135-state-changelog-profile-fixtures-r1", fixture["schema_version"])
        source = (ROOT / "STATE-CHANGELOG.md").read_text(encoding="utf-8")
        for case in fixture["cases"]:
            case_id = case["case_id"]
            if case_id == "current_missing_required_field":
                mutated = _replace_in_entry(
                    source,
                    25,
                    "- authority_changes:",
                    "- authority_removed:",
                )
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "STATE-CHANGELOG.md"
                    path.write_text(mutated, encoding="utf-8")
                    errors = validate(path)
                passed = not errors
            elif case_id == "historical_sealed_exact_legacy":
                passed = not validate()
            elif case_id == "historical_sealed_mutation":
                mutated = _replace_in_entry(source, 17, "- main_state:", "- main_state: MUTATED;")
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "STATE-CHANGELOG.md"
                    path.write_text(mutated, encoding="utf-8")
                    errors = validate(path)
                passed = not errors
            elif case_id == "unknown_legacy_version":
                profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                profile["entries"][16]["profile"] = "historical-legacy-r9"
                with tempfile.TemporaryDirectory() as tmp:
                    profile_path = Path(tmp) / "state-changelog-profile.json"
                    profile_path.write_text(json.dumps(profile), encoding="utf-8")
                    errors = validate(profile_path=profile_path)
                passed = not errors
            elif case_id == "current_profile_downgrade":
                profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                profile["entries"][24]["profile"] = "historical-legacy-r0"
                with tempfile.TemporaryDirectory() as tmp:
                    profile_path = Path(tmp) / "state-changelog-profile.json"
                    profile_path.write_text(json.dumps(profile), encoding="utf-8")
                    errors = validate(profile_path=profile_path)
                passed = not errors
            else:
                self.fail(f"unhandled fixture case: {case_id}")
            expected = case["expected_status"] == "PASS"
            self.assertEqual(expected, passed, case_id)


if __name__ == "__main__":
    unittest.main()
