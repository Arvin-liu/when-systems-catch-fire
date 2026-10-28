from __future__ import annotations

import json
import unittest

from agent_federation.structured_result_contract import (
    StructuredResultContractError,
    extract_synthetic_result,
    validate_synthetic_result,
)


VALID = {"nonce": "0123456789abcdef01234567", "line_count": 3, "field_value": "value-136", "checksum_prefix": "abcdef01"}


class StructuredResultContractTests(unittest.TestCase):
    def test_exact_nested_json_object_is_accepted(self) -> None:
        event = {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(VALID)}}
        evidence = extract_synthetic_result((event,))
        self.assertEqual(dict(evidence.value), VALID)

    def test_extra_field_is_rejected_before_sanitization(self) -> None:
        value = {**VALID, "unexpected": "must-not-be-stripped"}
        with self.assertRaisesRegex(StructuredResultContractError, "EXTRA_FIELDS"):
            extract_synthetic_result(({"text": json.dumps(value)},))

    def test_missing_field_is_rejected(self) -> None:
        value = dict(VALID)
        value.pop("checksum_prefix")
        with self.assertRaisesRegex(StructuredResultContractError, "MISSING_REQUIRED_FIELDS"):
            validate_synthetic_result(value)

    def test_non_json_text_is_not_repaired_by_search(self) -> None:
        with self.assertRaisesRegex(StructuredResultContractError, "JSON_NOT_EXACT"):
            extract_synthetic_result(({"text": "prefix " + json.dumps(VALID)},))

    def test_duplicate_distinct_results_are_ambiguous(self) -> None:
        other = {**VALID, "line_count": 4}
        with self.assertRaisesRegex(StructuredResultContractError, "AMBIGUOUS_RESULTS"):
            extract_synthetic_result(({"text": json.dumps(VALID)}, {"text": json.dumps(other)}))

    def test_empty_events_have_explicit_failure(self) -> None:
        with self.assertRaisesRegex(StructuredResultContractError, "NO_PUBLIC_EVENTS"):
            extract_synthetic_result(())


if __name__ == "__main__":
    unittest.main()
