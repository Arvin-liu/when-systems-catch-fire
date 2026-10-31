from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


IGNITION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION / "tools"))
import toolbox_raw_evidence_navigator as tool  # noqa: E402


def make_repo(root: Path, source: bytes, indexed_source: bytes | None = None) -> Path:
    index_dir = root / "ignition/data/governance/knowledge-experience"
    source_dir = root / "ignition/sources"
    index_dir.mkdir(parents=True)
    source_dir.mkdir(parents=True)
    (source_dir / "current.md").write_bytes(source)
    prior = indexed_source if indexed_source is not None else source
    row = {
        "search_id": "NFC-test-1",
        "title": "Annual carbon dioxide concentration",
        "aliases": ["CO2 annual growth"],
        "subjects": ["atmosphere"],
        "canonical_source": "sources/current.md",
        "source_sha256": hashlib.sha256(prior).hexdigest(),
    }
    (index_dir / "search-index.jsonl").write_text(
        json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return root


def request(
    terms: list[str] | None = None,
    max_bytes: int = 10_000,
) -> dict[str, object]:
    return {
        "requirements": [
            {
                "requirement_id": "R1",
                "query_terms": terms or ["annual", "carbon"],
            }
        ],
        "max_sources_per_requirement": 3,
        "max_total_source_bytes": max_bytes,
        "max_excerpt_chars": 200,
    }


class RawEvidenceNavigatorTests(unittest.TestCase):
    def test_reopens_current_raw_source_and_marks_index_digest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prior = b"Annual carbon source before update.\n"
            current = b"Current annual carbon observation.\nA second line.\n"
            make_repo(root, current, prior)

            result = tool.build_navigation_result(request(), repo_root=root)
            item = result["requirements"][0]
            source = item["sources"][0]

            self.assertEqual(item["navigation_status"], "RAW_MATCHES_FOUND")
            self.assertEqual(item["sufficiency_decision"], "NOT_EVALUATED")
            self.assertEqual(source["source_status"], "CURRENT_RAW_MATCHES_ALL_QUERY_TERMS")
            self.assertEqual(source["indexed_digest_relation"], "DIFFERS_FROM_INDEXED_DIGEST")
            self.assertEqual(source["current_source_sha256"], hashlib.sha256(current).hexdigest())
            self.assertEqual(source["line_matches"][0]["line"], 1)
            self.assertFalse(result["execution_authorized"])

    def test_budget_exhaustion_returns_an_open_gap_without_false_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = b"Annual carbon source that exceeds the tiny budget.\n"
            make_repo(root, content)

            result = tool.build_navigation_result(request(max_bytes=1), repo_root=root)
            item = result["requirements"][0]

            self.assertEqual(item["navigation_status"], "BUDGET_EXHAUSTED")
            self.assertEqual(item["current_raw_match_count"], 0)
            self.assertEqual(item["sufficiency_decision"], "NOT_EVALUATED")
            self.assertEqual(item["sources"][0]["source_status"], "RAW_SOURCE_NOT_OPENED_BUDGET")
            self.assertEqual(result["budgets"]["source_bytes_read"], 0)

    def test_found_match_keeps_budget_blocked_candidates_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current = b"Annual carbon source.\n"
            make_repo(root, current)
            source_dir = root / "ignition/sources"
            large = b"Annual carbon " + b"x" * 400
            (source_dir / "large.md").write_bytes(large)
            index = root / "ignition/data/governance/knowledge-experience/search-index.jsonl"
            rows = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
            rows.append(
                {
                    "search_id": "NFC-test-large",
                    "title": "Annual carbon large source",
                    "aliases": [],
                    "subjects": [],
                    "canonical_source": "sources/large.md",
                    "source_sha256": hashlib.sha256(large).hexdigest(),
                }
            )
            index.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n",
                encoding="utf-8",
            )
            limited = request(max_bytes=len(current))
            limited["max_sources_per_requirement"] = 2

            result = tool.build_navigation_result(limited, repo_root=root)
            item = result["requirements"][0]

            self.assertEqual(item["navigation_status"], "RAW_MATCHES_FOUND_WITH_BUDGET_GAP")
            self.assertEqual(item["current_raw_match_count"], 1)
            self.assertEqual(item["unopened_source_count"], 1)
            self.assertIn("were not opened within budget", item["unresolved_gap"])
            self.assertEqual(item["sufficiency_decision"], "NOT_EVALUATED")

    def test_stale_index_candidate_without_raw_literal_match_is_not_a_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current = b"Updated document with no relevant terms.\n"
            prior = b"Annual carbon source before update.\n"
            make_repo(root, current, prior)

            result = tool.build_navigation_result(request(), repo_root=root)
            item = result["requirements"][0]

            self.assertEqual(item["navigation_status"], "NO_CURRENT_RAW_MATCH")
            self.assertEqual(item["current_raw_match_count"], 0)
            self.assertEqual(item["sources"][0]["source_status"], "CURRENT_RAW_NO_TERM_MATCH")
            self.assertEqual(item["sources"][0]["indexed_digest_relation"], "DIFFERS_FROM_INDEXED_DIGEST")

    def test_partial_current_match_keeps_missing_query_terms_open(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root, b"Current annual observation.\n")

            result = tool.build_navigation_result(request(), repo_root=root)
            item = result["requirements"][0]
            source = item["sources"][0]

            self.assertEqual(item["navigation_status"], "PARTIAL_RAW_MATCHES_FOUND")
            self.assertEqual(item["current_raw_match_count"], 0)
            self.assertEqual(item["partial_raw_source_count"], 1)
            self.assertEqual(source["source_status"], "CURRENT_RAW_PARTIAL_QUERY_TERM_MATCH")
            self.assertEqual(source["missing_current_terms"], ["carbon"])

    def test_line_match_limit_reports_count_and_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            content = "".join("Annual carbon source line %d.\n" % number for number in range(12)).encode()
            make_repo(root, content)

            result = tool.build_navigation_result(request(), repo_root=root)
            source = result["requirements"][0]["sources"][0]

            self.assertEqual(source["source_status"], "CURRENT_RAW_MATCHES_ALL_QUERY_TERMS")
            self.assertEqual(source["matched_line_count"], 12)
            self.assertEqual(len(source["line_matches"]), tool.MAX_HITS_PER_SOURCE)
            self.assertTrue(source["line_matches_truncated"])

    def test_index_path_traversal_is_reported_without_reading_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root, b"Annual carbon source.\n")
            index = root / "ignition/data/governance/knowledge-experience/search-index.jsonl"
            row = json.loads(index.read_text(encoding="utf-8"))
            row["canonical_source"] = "../../outside.txt"
            index.write_text(json.dumps(row) + "\n", encoding="utf-8")
            outside = root.parent / "outside.txt"
            outside.write_text("Annual carbon secret\n", encoding="utf-8")
            try:
                result = tool.build_navigation_result(request(), repo_root=root)
            finally:
                outside.unlink(missing_ok=True)

            source = result["requirements"][0]["sources"][0]
            self.assertEqual(source["source_status"], "RAW_SOURCE_PATH_REJECTED")
            self.assertEqual(source["line_matches"], [])

    def test_symlinked_raw_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside_temp:
            root = Path(temp)
            outside = Path(outside_temp) / "secret.md"
            outside.write_text("Annual carbon secret\n", encoding="utf-8")
            make_repo(root, b"placeholder\n")
            current = root / "ignition/sources/current.md"
            current.unlink()
            current.symlink_to(outside)

            result = tool.build_navigation_result(request(), repo_root=root)
            source = result["requirements"][0]["sources"][0]

            self.assertEqual(source["source_status"], "RAW_SOURCE_PATH_REJECTED")
            self.assertEqual(source["line_matches"], [])

    def test_duplicate_source_records_are_deduplicated_and_results_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root, b"Annual carbon source.\n")
            index = root / "ignition/data/governance/knowledge-experience/search-index.jsonl"
            rows = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines()]
            duplicate = dict(rows[0], search_id="NFC-test-2", title="Annual carbon duplicate")
            index.write_text(
                "\n".join(json.dumps(row, ensure_ascii=False) for row in (rows[0], duplicate)) + "\n",
                encoding="utf-8",
            )

            first = tool.build_navigation_result(request(), repo_root=root)
            second = tool.build_navigation_result(request(), repo_root=root)

            self.assertEqual(first, second)
            self.assertEqual(first["requirements"][0]["candidate_source_count"], 1)
            self.assertEqual(first["requirements"][0]["selected_source_count"], 1)

    def test_invalid_or_unbounded_request_is_rejected(self) -> None:
        for payload in (
            {},
            request(max_bytes=tool.MAX_TOTAL_SOURCE_BYTES + 1),
            {
                **request(),
                "requirements": [
                    {"requirement_id": "R1", "query_terms": ["annual"]},
                    {"requirement_id": "R1", "query_terms": ["carbon"]},
                ],
            },
        ):
            with self.subTest(payload=payload), self.assertRaises(tool.RawEvidenceNavigationError):
                tool.build_navigation_result(payload, repo_root=Path("/missing"))


if __name__ == "__main__":
    unittest.main()
