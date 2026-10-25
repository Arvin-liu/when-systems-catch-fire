from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


IGNITION = Path(__file__).resolve().parents[1]
REPO_ROOT = IGNITION.parent
TOOL_PATH = IGNITION / "tools/toolbox_cognitive_migration_revision.py"
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_cognitive_migration_revision as tool  # noqa: E402


def sample_request() -> dict[str, object]:
    return {
        "schema_version": "ignition.cognitive-migration-revision-request.v1",
        "genre": "MEDIUM_LENGTH_PUBLIC_ARTICLE",
        "reader_shift": {"before": "The reader sees a count.", "after": "The reader sees who bore its cost."},
        "claim_ceiling": "Use only the facts documented in the supplied archive reference.",
        "anchors": [
            {"id": "A1", "exact_text": "The register lists 12 sacks", "source_ref": "archive:R1:p3"},
            {"id": "A2", "exact_text": "The ledger names the carriers", "source_ref": "archive:R2:p8"},
            {"id": "A3", "exact_text": "The margin records a dispute", "source_ref": "archive:R3:p2"},
        ],
        "paragraphs": [
            {
                "id": "P1", "text": "The register lists 12 sacks. What did that count leave outside the frame?",
                "role": "LEDE", "moves": ["RECURSIVE_QUESTIONING"],
                "concepts": [{"label": "accounting boundary", "anchor_id": "A1"}], "anchor_ids": ["A1"],
            },
            {
                "id": "P2", "text": "The ledger names the carriers. The total records a transfer, while the names expose its human scale.",
                "role": "BODY", "moves": ["PROGRESSIVE_DEEPENING"],
                "concepts": [{"label": "human scale", "anchor_id": "A2"}], "anchor_ids": ["A2"],
            },
            {
                "id": "P3", "text": "From the clerk's desk, the number closes a column; from a carrier's view, it marks a day of work.",
                "role": "BODY", "moves": ["PERSPECTIVE_SWITCHING"], "concepts": [], "anchor_ids": [],
            },
            {
                "id": "P4", "text": "The margin records a dispute. The record does not settle what either side intended.",
                "role": "COUNTERARGUMENT", "moves": [],
                "concepts": [{"label": "interpretive limit", "anchor_id": "A3"}], "anchor_ids": ["A3"],
            },
            {
                "id": "P5", "text": "A named carrier appears in the roll, but the source says nothing about the person's later life.",
                "role": "AFFECTED_PERSON", "moves": [], "concepts": [], "anchor_ids": [],
            },
            {
                "id": "P6", "text": "The closing distinction is small: a count can describe a transfer without describing its full human cost.",
                "role": "CLOSING", "moves": [], "concepts": [], "anchor_ids": [],
            },
            {
                "id": "P7", "text": "The next body paragraph connects the inventory to its setting.",
                "role": "BODY", "moves": [], "concepts": [], "anchor_ids": [],
            },
            {
                "id": "P8", "text": "Unanchored background paragraph to be considered for omission.",
                "role": "OTHER", "moves": [], "concepts": [], "anchor_ids": [],
            },
        ],
        "selected_paragraph_ids": ["P1", "P3", "P2", "P7", "P4", "P5", "P6"],
    }


def request_bytes(request: dict[str, object] | None = None) -> bytes:
    return json.dumps(sample_request() if request is None else request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class CognitiveMigrationRevisionTests(unittest.TestCase):
    def test_proposes_verbatim_reorder_and_preserves_protected_content(self) -> None:
        request = sample_request()
        receipt = tool.build_review(request_bytes(request))
        expected = "\n\n".join(
            next(p["text"] for p in request["paragraphs"] if p["id"] == paragraph_id)
            for paragraph_id in request["selected_paragraph_ids"]
        )
        self.assertEqual(receipt["review_status"], "PROPOSAL_REQUIRES_HUMAN_REVIEW")
        self.assertEqual(receipt["proposal_text"], expected)
        self.assertTrue(receipt["proposal_is_verbatim_join_of_selected_paragraphs"])
        self.assertEqual(receipt["omitted_paragraph_ids"], ["P8"])
        self.assertEqual(receipt["protected_omission_ids"], [])
        self.assertIn("P4", receipt["selected_paragraph_ids"])
        self.assertIn("P5", receipt["selected_paragraph_ids"])
        self.assertFalse(receipt["execution_authorized"])
        self.assertFalse(receipt["claim_ceiling_evaluated"])
        self.assertEqual(receipt["request_sha256"], hashlib.sha256(request_bytes()).hexdigest())
        self.assertFalse(receipt["source_ref_relation_verified"])
        self.assertEqual(receipt["wrapper_source_sha256"], hashlib.sha256(TOOL_PATH.read_bytes()).hexdigest())
        self.assertEqual(receipt["selected_move_types_declared_by_caller"], [
            "PERSPECTIVE_SWITCHING", "PROGRESSIVE_DEEPENING", "RECURSIVE_QUESTIONING",
        ])

    def test_protected_content_omission_withholds_proposal_text(self) -> None:
        request = sample_request()
        request["selected_paragraph_ids"] = ["P1", "P2", "P3", "P6"]
        receipt = tool.build_review(request_bytes(request))
        self.assertEqual(receipt["review_status"], "BLOCKED_PROTECTED_CONTENT_OMITTED")
        self.assertIsNone(receipt["proposal_text"])
        self.assertEqual(receipt["protected_omission_ids"], ["P4", "P5"])
        self.assertFalse(receipt["proposal_is_verbatim_join_of_selected_paragraphs"])
        self.assertIn("P4", receipt["omitted_paragraph_ids"])
        self.assertIn("P5", receipt["omitted_paragraph_ids"])

    def test_anchor_excerpt_must_exist_in_its_declared_paragraph(self) -> None:
        request = sample_request()
        request["anchors"][0]["exact_text"] = "not present in paragraph"
        with self.assertRaisesRegex(tool.ToolInputError, "exact text"):
            tool.build_review(request_bytes(request))

    def test_concept_needs_a_distinct_anchor_on_its_paragraph(self) -> None:
        request = sample_request()
        request["paragraphs"][0]["concepts"][0]["anchor_id"] = "A2"
        with self.assertRaisesRegex(tool.ToolInputError, "attached to paragraph"):
            tool.build_review(request_bytes(request))
        request = sample_request()
        request["paragraphs"][1]["concepts"].append({"label": "second concept", "anchor_id": "A2"})
        with self.assertRaisesRegex(tool.ToolInputError, "own declared anchor"):
            tool.build_review(request_bytes(request))

    def test_repeated_phrases_are_advisories_and_not_a_ban(self) -> None:
        request = sample_request()
        request["genre"] = "OTHER"
        request["paragraphs"][1]["text"] += " 不是数字而是人的劳动。"
        request["paragraphs"][2]["text"] += " 不是孤立事实而是换一个视角。"
        receipt = tool.build_review(request_bytes(request))
        self.assertIsNotNone(receipt["proposal_text"])
        self.assertIn("REPEATED_SURFACE_PATTERN_REVIEW", {row["code"] for row in receipt["findings"]})
        self.assertEqual(receipt["proposal_formula_pattern_counts"]["not_x_but_y"], 2)
        self.assertNotEqual(receipt["review_status"], "BLOCKED_PROTECTED_CONTENT_OMITTED")

    def test_invalid_duplicate_key_oversized_and_unmapped_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(tool.ToolInputError, "duplicate JSON"):
            tool.parse_request(b'{"schema_version":"x","schema_version":"y"}')
        with self.assertRaisesRegex(tool.ToolInputError, "exceeds"):
            tool.parse_request(b" " * (tool.MAX_INPUT_BYTES + 1))
        request = sample_request()
        request["selected_paragraph_ids"] = ["P1", "NOT-A-PARAGRAPH"]
        with self.assertRaisesRegex(tool.ToolInputError, "unknown IDs"):
            tool.build_review(request_bytes(request))

    def test_cli_receipt_is_deterministic_and_stdout_only(self) -> None:
        raw = request_bytes()
        runs = [
            subprocess.run(
                [sys.executable, "-B", str(TOOL_PATH), "--stdin"],
                cwd=REPO_ROOT, input=raw, capture_output=True, check=False,
            )
            for _ in range(2)
        ]
        self.assertEqual([run.returncode for run in runs], [0, 0])
        self.assertEqual(runs[0].stdout, runs[1].stdout)
        self.assertEqual(runs[0].stderr, b"")
        decoded = json.loads(runs[0].stdout)
        self.assertEqual(decoded["tool_id"], "writing.preflight_cognitive_migration_revision")
        self.assertFalse(decoded["execution_authorized"])

    def test_unknown_output_path_option_is_rejected_before_report(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(TOOL_PATH), "--stdin", "--output", "/tmp/forbidden-tool-output"],
            cwd=REPO_ROOT, input=request_bytes(), capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")


if __name__ == "__main__":
    unittest.main()
