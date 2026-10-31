from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator


IGNITION_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = IGNITION_ROOT / "tools/toolbox_jsonl_selector.py"
INPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-jsonl-selector-input-r0.schema.json"
OUTPUT_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-jsonl-selector-output-r0.schema.json"
C1_SCHEMA_PATH = IGNITION_ROOT / "schemas/operations/toolbox-jsonl-selector-c1-evidence-r0.schema.json"
SPEC = importlib.util.spec_from_file_location("toolbox_jsonl_selector", TOOL_PATH)
TOOL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(TOOL)


class ToolboxJsonlSelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "ignition/data").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def request(self, **overrides: object) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": "toolbox-jsonl-selector-input-r0",
            "source_path": "ignition/data/rows.jsonl",
            "json_pointer": "/key",
            "equals": "wanted",
            "max_source_bytes": 10_000,
            "max_returned_bytes": 4_000,
            "max_matches": 10,
        }
        result.update(overrides)
        return result

    def write_source(self, content: bytes) -> Path:
        source = self.root / "ignition/data/rows.jsonl"
        source.write_bytes(content)
        return source

    def test_exact_match_returns_source_and_record_digests_and_byte_offsets(self) -> None:
        content = b'{"key":"other"}\r\n{"key":"wanted","n":2}\n'
        self.write_source(content)

        result = TOOL.execute_request(self.request(), self.root)

        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["source_sha256"], hashlib.sha256(content).hexdigest())
        self.assertEqual(result["source_bytes"], len(content))
        self.assertEqual(result["lines_scanned"], 2)
        self.assertEqual(result["selected_record_count"], 1)
        record = result["records"][0]
        expected = b'{"key":"wanted","n":2}'
        start = content.index(expected)
        self.assertEqual(record["line_number"], 2)
        self.assertEqual(record["start_byte_offset"], start)
        self.assertEqual(record["end_byte_offset_exclusive"], start + len(expected))
        self.assertEqual(record["byte_count"], len(expected))
        self.assertEqual(record["sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(record["text"].encode("utf-8"), expected)

    def test_json_number_equality_and_boolean_separation(self) -> None:
        self.write_source(b'{"key":1}\n')
        numeric_result = TOOL.execute_request(self.request(equals=1.0), self.root)
        boolean_result = TOOL.execute_request(self.request(equals=True), self.root)
        self.assertEqual(numeric_result["selected_record_count"], 1)
        self.assertEqual(numeric_result["selector"]["equality"], "JSON_SCALAR_VALUE_EXACT")
        self.assertEqual(boolean_result["selected_record_count"], 0)

    def test_json_pointer_escape_and_array_index_are_supported(self) -> None:
        self.write_source(b'{"a/b":[{"value":"yes"}]}\n')
        result = TOOL.execute_request(
            self.request(json_pointer="/a~1b/0/value", equals="yes"), self.root
        )
        self.assertEqual(result["selected_record_count"], 1)

    def test_invalid_json_pointer_escape_is_rejected(self) -> None:
        self.write_source(b'{"key":"wanted"}\n')
        with self.assertRaises(TOOL.SelectorError) as caught:
            TOOL.execute_request(self.request(json_pointer="/bad~2escape"), self.root)
        self.assertEqual(caught.exception.code, "INVALID_JSON_POINTER")

    def test_path_traversal_is_rejected_before_read(self) -> None:
        with self.assertRaises(TOOL.SelectorError) as caught:
            TOOL.execute_request(self.request(source_path="ignition/../outside.jsonl"), self.root)
        self.assertEqual(caught.exception.code, "INVALID_SOURCE_PATH")

    def test_symlink_source_is_rejected(self) -> None:
        target = self.root / "ignition/data/target.jsonl"
        target.write_text('{"key":"wanted"}\n', encoding="utf-8")
        (self.root / "ignition/data/rows.jsonl").symlink_to(target)
        with self.assertRaises(TOOL.SelectorError) as caught:
            TOOL.execute_request(self.request(), self.root)
        self.assertEqual(caught.exception.code, "SOURCE_SYMLINK")

    def test_duplicate_object_keys_and_malformed_rows_fail_closed(self) -> None:
        for content in (b'{"key":"wanted","key":"other"}\n', b'{not-json}\n'):
            with self.subTest(content=content):
                self.write_source(content)
                with self.assertRaises(TOOL.SelectorError):
                    TOOL.execute_request(self.request(), self.root)

    def test_blank_line_and_non_object_rows_fail_closed(self) -> None:
        for content in (b'{"key":"wanted"}\n\n', b'["wanted"]\n'):
            with self.subTest(content=content):
                self.write_source(content)
                with self.assertRaises(TOOL.SelectorError):
                    TOOL.execute_request(self.request(), self.root)

    def test_non_finite_overflowing_json_number_is_rejected(self) -> None:
        self.write_source(b'{"key":1e9999}\n')
        with self.assertRaises(TOOL.SelectorError) as caught:
            TOOL.execute_request(self.request(json_pointer="/key", equals=1), self.root)
        self.assertEqual(caught.exception.code, "NON_JSON_NUMBER")

    def test_match_and_return_limits_reject_without_partial_result(self) -> None:
        self.write_source(b'{"key":"wanted"}\n{"key":"wanted"}\n')
        with self.assertRaises(TOOL.SelectorError) as caught:
            TOOL.execute_request(self.request(max_matches=1), self.root)
        self.assertEqual(caught.exception.code, "TOO_MANY_MATCHES")
        with self.assertRaises(TOOL.SelectorError) as caught:
            TOOL.execute_request(self.request(max_returned_bytes=4), self.root)
        self.assertEqual(caught.exception.code, "RETURN_LIMIT_EXCEEDED")

    def test_request_and_result_match_json_schemas(self) -> None:
        self.write_source(b'{"key":"wanted"}\n')
        input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        request = self.request()
        result = TOOL.execute_request(request, self.root)
        Draft202012Validator.check_schema(input_schema)
        Draft202012Validator.check_schema(output_schema)
        Draft202012Validator(input_schema).validate(request)
        Draft202012Validator(output_schema).validate(result)
        rejected = TOOL._rejection(TOOL.SelectorError("TEST_REJECTED", "bounded rejection"))
        Draft202012Validator(output_schema).validate(rejected)

    def test_checked_in_real_task_and_c1_fallback_evidence_are_exactly_bound(self) -> None:
        operations = IGNITION_ROOT / "data/operations"
        candidate = json.loads((operations / "toolbox-jsonl-selector-real-task-r0.json").read_text(encoding="utf-8"))
        fallback = json.loads((operations / "toolbox-jsonl-selector-fallback-task-r0.json").read_text(encoding="utf-8"))
        evidence = json.loads((operations / "toolbox-jsonl-selector-c1-evidence-r0.json").read_text(encoding="utf-8"))
        request = json.loads((operations / "toolbox-jsonl-selector-real-task-input-r0.json").read_text(encoding="utf-8"))
        input_schema = json.loads(INPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        evidence_schema = json.loads(C1_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator(input_schema).validate(request)
        Draft202012Validator(output_schema).validate(candidate)
        Draft202012Validator.check_schema(evidence_schema)
        Draft202012Validator(evidence_schema).validate(evidence)
        candidate_record = candidate["records"][0]
        fallback_record = fallback["records"][0]
        self.assertEqual(candidate["status"], "COMPLETE")
        self.assertEqual(candidate["selected_record_count"], 1)
        source_bytes = (IGNITION_ROOT / "data/governance/knowledge-experience/search-index.jsonl").read_bytes()
        self.assertEqual(candidate["source_bytes"], len(source_bytes))
        self.assertEqual(candidate["source_sha256"], hashlib.sha256(source_bytes).hexdigest())
        self.assertEqual(candidate["source_sha256"], fallback["source_sha256"])
        self.assertEqual(candidate_record, {key: fallback_record[key] for key in candidate_record})
        self.assertEqual(evidence["disposition"]["comparison_status"], "COMPARISON_UNKNOWN")
        self.assertEqual(evidence["parity"], {
            "source_sha256_equal": True,
            "selected_record_count_equal": True,
            "line_number_equal": True,
            "byte_offsets_equal": True,
            "record_byte_count_equal": True,
            "record_sha256_equal": True,
            "record_text_equal": True,
        })


if __name__ == "__main__":
    unittest.main()
