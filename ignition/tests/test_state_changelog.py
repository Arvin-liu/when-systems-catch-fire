import tempfile
import unittest
from pathlib import Path

from tools.validate_state_changelog import ROOT, validate


class StateChangelogTests(unittest.TestCase):
    def test_current_log_is_valid(self):
        self.assertEqual([], validate())

    def test_missing_required_field_is_rejected(self):
        source = Path("STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = source.replace("- stale_knowledge:", "- stale_removed:", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "STATE-CHANGELOG.md"
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        self.assertTrue(any("stale_knowledge" in error for error in errors), errors)

    def test_broken_repository_link_is_rejected(self):
        source = Path("STATE-CHANGELOG.md").read_text(encoding="utf-8")
        source = source.replace("./AI-START-HERE.md", "./missing-state-entry.md", 1)
        path = ROOT / ".state-changelog-test.md"
        try:
            path.write_text(source, encoding="utf-8")
            errors = validate(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertTrue(any("broken repository link" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
