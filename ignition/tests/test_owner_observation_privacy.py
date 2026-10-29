import copy
import json
import unittest

from tools.validate_owner_observation_privacy import DEFAULT_RECORD, DEFAULT_SCHEMA, privacy_scan, validate


class OwnerObservationPrivacyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(DEFAULT_RECORD.read_text(encoding="utf-8"))
        cls.schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))

    def test_record_is_public_safe_and_bounded(self):
        self.assertEqual([], validate(self.record, self.schema))
        self.assertEqual([], privacy_scan((DEFAULT_RECORD,)))
        self.assertIn("NOT_INDEPENDENTLY_REPLICATED", self.record["status"])

    def test_private_path_is_rejected(self):
        record = copy.deepcopy(self.record)
        record["summary"] += " /Users/example/private-note.md"
        self.assertTrue(privacy_scan_with_record(record))


def privacy_scan_with_record(record):
    import tempfile
    from pathlib import Path
    from tools.validate_owner_observation_privacy import privacy_scan

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "record.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return bool(privacy_scan((path,)))


if __name__ == "__main__":
    unittest.main()
