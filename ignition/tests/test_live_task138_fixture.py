import json
from pathlib import Path
import stat
import tempfile
import unittest

from agent_federation.live_pilot import DisposableLive138CompletionFixture, Live138CompletionValidator


class LiveTask138FixtureTests(unittest.TestCase):
    def test_fixture_freezes_new_answer_and_external_strict_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "fixture-parent"
            parent.mkdir()
            with DisposableLive138CompletionFixture.create(parent, nonce="abcdef0123456789abcdef01") as fixture:
                fixture.make_read_only()
                self.assertTrue(fixture.schema_path.is_file())
                self.assertNotEqual(fixture.schema_path.parent, fixture.root)
                self.assertEqual(stat.S_IMODE(fixture.schema_path.stat().st_mode), 0o444)
                self.assertEqual(fixture.file_names(), ("README.txt", "nonce.txt", "table.json"))
                self.assertEqual(fixture.expectation.selected_ids, ("item-a", "item-d", "item-f", "item-c"))
                self.assertEqual(fixture.expectation.count, 4)
                schema = json.loads(fixture.schema_path.read_text(encoding="utf-8"))
                self.assertEqual(schema["required"], ["nonce", "selected_ids", "count", "workspace_digest_claim"])
                self.assertFalse(schema["additionalProperties"])
            self.assertFalse(fixture.root.exists())
            self.assertFalse(fixture.schema_path.exists())

    def test_independent_validator_passes_exact_answer_and_rejects_wrong_answer(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "fixture-parent"
            parent.mkdir()
            with DisposableLive138CompletionFixture.create(parent, nonce="abcdef0123456789abcdef01") as fixture:
                fixture.make_read_only()
                validator = Live138CompletionValidator(fixture)
                correct = {
                    "nonce": fixture.expectation.nonce,
                    "selected_ids": list(fixture.expectation.selected_ids),
                    "count": fixture.expectation.count,
                    "workspace_digest_claim": fixture.before_digest,
                }
                passed = validator.validate(correct, before_digest=fixture.before_digest, after_digest=fixture.current_digest())
                self.assertEqual(passed.status, "PASS")
                self.assertTrue(all(passed.checks.values()))
                wrong = {**correct, "selected_ids": ["item-c"], "count": 1}
                failed = validator.validate(wrong, before_digest=fixture.before_digest, after_digest=fixture.current_digest())
                self.assertEqual(failed.status, "FAIL")
                self.assertIn("SELECTED_IDS_EXACT", failed.failure_codes)
                self.assertIn("COUNT_EXACT", failed.failure_codes)


if __name__ == "__main__":
    unittest.main()
