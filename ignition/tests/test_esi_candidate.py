import json
import unittest
from pathlib import Path

from tools.validate_esi_candidate import DEFAULT_RECORD, DEFAULT_SCHEMA, validate


class EsiCandidateTests(unittest.TestCase):
    def test_record_is_bounded_and_schema_valid(self):
        record = json.loads(DEFAULT_RECORD.read_text(encoding="utf-8"))
        schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual([], validate(record, schema))

    def test_scope_cannot_be_reinterpreted_as_hard_authority(self):
        record = json.loads(DEFAULT_RECORD.read_text(encoding="utf-8"))
        record["scope"]["not_hard_authority"] = False
        schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
        self.assertTrue(validate(record, schema))


if __name__ == "__main__":
    unittest.main()
