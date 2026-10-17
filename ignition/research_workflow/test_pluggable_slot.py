"""Offline tests for the fixed, one-slot source-binding adapter boundary."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

try:
    from . import slot
except ImportError:  # unittest discover -s ignition/research_workflow
    import slot  # type: ignore[no-redef]


class PluggableSourceBindingSlotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sources_dir = self.root / "sources"
        self.sources_dir.mkdir()
        self.capture_texts = [
            "STEP 1 randomized 1961 adults without diabetes to semaglutide or placebo with lifestyle intervention.\n"
            "At week 68, treatments including lifestyle intervention were discontinued.\n"
            "The semaglutide group regained a mean 11.6 percentage points by week 120.\n",
            "L247: STEP 4 began with 902 participants receiving semaglutide during run-in. After 20 weeks, 803 were randomized.\n"
            "L252: From week 20 to week 68, mean weight change was -7.9% with continued semaglutide and +6.9% after switch to placebo.\n",
        ]
        self.source_rows = []
        self.legacy_rows = []
        self.digest_lock = {}
        for index, text in enumerate(self.capture_texts, 1):
            raw = text.encode("utf-8")
            capture_name = f"source-{index}.txt"
            (self.sources_dir / capture_name).write_bytes(raw)
            title = f"Frozen trial abstract {index}"
            url = f"https://example.org/trial-{index}"
            self.source_rows.append({
                "title": title,
                "source_url": url,
                "capture_path": capture_name,
                "capture_kind": "web_run_observation",
                "captured_at_utc": "2026-10-17T00:00:00Z",
                "locator": "Abstract, results",
                "query_ids": [f"Q{index}"],
            })
            normalized = re.sub(r"(?m)^L[0-9]+:\s*", "", text)
            self.legacy_rows.append({
                "source_id": f"S{index}",
                "title": title,
                "source_url": url,
                "doi": f"10.1000/trial{index}",
                "year": 2021 + index,
                "abstract": normalized,
            })
            self.digest_lock[f"S{index}"] = hashlib.sha256(raw).hexdigest()
        self.expected_source_set_digest = slot._canonical_source_set_digest([
            {
                "source_id": row["source_id"],
                "title": row["title"],
                "source_url": row["source_url"],
                "abstract": row["abstract"],
            }
            for row in self.legacy_rows
        ])
        self.manifest = self.sources_dir / "manifest.jsonl"
        self.manifest.write_text("".join(json.dumps(row) + "\n" for row in self.source_rows), encoding="utf-8")
        self.records = self.root / "legacy-records.jsonl"
        self.records.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in self.legacy_rows), encoding="utf-8")
        self.digests = self.root / "expected-digests.json"
        self.digests.write_text(json.dumps(self.digest_lock, sort_keys=True) + "\n", encoding="utf-8")
        self.draft = self.root / "draft.md"
        self.draft.write_text("Trial findings [S1] and [S2].\n", encoding="utf-8")
        self.claims = self.root / "claims.jsonl"
        self.claims.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in self._base_claims()), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _review(claim_id, text, source_id, quote, judgment="SUPPORTS"):
        return {
            "claim_id": claim_id,
            "claim_text": text,
            "source_id": source_id,
            "review_judgment": judgment,
            "reviewer_type": "HUMAN" if judgment != "NOT_REVIEWED" else "NOT_REVIEWED",
            **({
                "reviewer": "fixture-reviewer",
                "reviewed_at_utc": "2026-10-17T00:00:00Z",
                "evidence_field": "abstract",
                "evidence_quote": quote,
            } if judgment != "NOT_REVIEWED" else {}),
        }

    def _base_claims(self):
        return [
            self._review("C1", "STEP 1 randomized adults to treatment with lifestyle intervention.", "S1", "STEP 1 randomized 1961 adults without diabetes to semaglutide or placebo with lifestyle intervention."),
            self._review("C2", "STEP 1 stopped treatment and lifestyle intervention at week 68.", "S1", "At week 68, treatments including lifestyle intervention were discontinued."),
            self._review("C3", "STEP 4 randomized participants after a semaglutide run-in.", "S2", "After 20 weeks, 803 were randomized."),
            self._review("C4", "STEP 4 reported the week 20 to week 68 changes.", "S2", "From week 20 to week 68, mean weight change was -7.9% with continued semaglutide and +6.9% after switch to placebo."),
        ]

    def _run(self, adapter_id, output, **override):
        args = {
            "adapter_id": adapter_id,
            "question": "What did these frozen trial abstracts report?",
            "output_dir": output,
            "draft_path": self.draft,
            "claim_review_path": self.claims,
            "task_id": "TASK-PLUGGABLE-SLOT-TEST",
            "episode_id": "EPISODE-TEST-01",
            "source_set_id": "FROZEN-TRIALS-TEST-V1",
            "namespace": "research/test",
            "authorization_scope": "read-only-public-abstract-fixtures",
            "implementation_commit": "test-working-tree",
            "expected_source_set_digest": self.expected_source_set_digest,
            "legacy_records_path": self.records if adapter_id == "legacy-openalex-v1" else None,
            "source_snapshots_path": self.manifest if adapter_id == "e37-source-snapshot-v1" else None,
            "expected_digests_path": self.digests if adapter_id == "e37-source-snapshot-v1" else None,
            "query_count": 2,
        }
        args.update(override)
        return slot.run_binding(**args)

    def test_both_adapters_use_same_claim_consumer_and_candidate_retains_exact_bytes(self):
        legacy = self._run("legacy-openalex-v1", self.root / "legacy-run")
        candidate = self._run("e37-source-snapshot-v1", self.root / "candidate-run")
        self.assertEqual(legacy["status"], "COMPLETED")
        self.assertEqual(candidate["status"], "COMPLETED")
        self.assertEqual(legacy["claim_review_status"], candidate["claim_review_status"])
        self.assertEqual(legacy["counts"]["exact_anchors"], candidate["counts"]["exact_anchors"])
        self.assertEqual(legacy["counts"]["exact_anchors"], 4)
        self.assertEqual(legacy["input"]["canonical_source_set_sha256"], candidate["input"]["canonical_source_set_sha256"])
        self.assertTrue(legacy["input"]["source_set_digest_match"])
        self.assertTrue(candidate["input"]["source_set_digest_match"])
        self.assertEqual(legacy["input"]["draft_sha256"], hashlib.sha256(self.draft.read_bytes()).hexdigest())
        self.assertEqual(candidate["input"]["draft_sha256"], legacy["input"]["draft_sha256"])
        self.assertEqual(legacy["input"]["claim_review_sha256"], hashlib.sha256(self.claims.read_bytes()).hexdigest())
        self.assertEqual(candidate["input"]["claim_review_sha256"], legacy["input"]["claim_review_sha256"])
        self.assertEqual(
            (self.root / "legacy-run/inputs/draft.md").read_bytes(),
            (self.root / "candidate-run/inputs/draft.md").read_bytes(),
        )
        self.assertEqual(
            (self.root / "legacy-run/inputs/claim-review.jsonl").read_bytes(),
            (self.root / "candidate-run/inputs/claim-review.jsonl").read_bytes(),
        )
        self.assertEqual(
            candidate["input"]["expected_capture_digest_lock_sha256"],
            hashlib.sha256(self.digests.read_bytes()).hexdigest(),
        )
        legacy_rows = [json.loads(line) for line in (self.root / "legacy-run/claim-review.jsonl").read_text().splitlines()]
        candidate_rows = [json.loads(line) for line in (self.root / "candidate-run/claim-review.jsonl").read_text().splitlines()]
        self.assertEqual([row["evidence_anchor_status"] for row in legacy_rows], [row["evidence_anchor_status"] for row in candidate_rows])
        self.assertTrue(all(row["evidence_field"] == "abstract" for row in legacy_rows + candidate_rows))
        self.assertEqual(legacy["counts"]["capture_bytes_retained"], 0)
        self.assertEqual(candidate["counts"]["capture_bytes_retained"], 2)
        for index, expected in enumerate(self.capture_texts, 1):
            raw_path = self.root / f"candidate-run/raw/source-S{index}.txt"
            self.assertEqual(raw_path.read_bytes(), expected.encode("utf-8"))
            self.assertEqual(hashlib.sha256(raw_path.read_bytes()).hexdigest(), self.digest_lock[f"S{index}"])
        legacy_sources = [json.loads(line) for line in (self.root / "legacy-run/sources.jsonl").read_text().splitlines()]
        self.assertTrue(all(row["capture_status"] == "UNAVAILABLE" and not row["raw_evidence"] for row in legacy_sources))

    def test_wrong_source_and_unknown_claim_source_fail_overall_run_for_both_adapters(self):
        wrong = self._review("W1", "STEP 1 said this.", "S1", "From week 20 to week 68, mean weight change was -7.9% with continued semaglutide and +6.9% after switch to placebo.", "CONTRADICTS")
        unknown = self._review("W2", "Unknown source claim.", "S99", "", "NOT_REVIEWED")
        for adapter_id in ("legacy-openalex-v1", "e37-source-snapshot-v1"):
            with self.subTest(adapter=adapter_id):
                wrong_file = self.root / f"wrong-{adapter_id}.jsonl"
                wrong_file.write_text(json.dumps(wrong) + "\n", encoding="utf-8")
                wrong_result = self._run(adapter_id, self.root / f"wrong-run-{adapter_id}", claim_review_path=wrong_file)
                self.assertEqual(wrong_result["input"]["claim_review_sha256"], hashlib.sha256(wrong_file.read_bytes()).hexdigest())
                self.assertEqual(wrong_result["acquisition_status"], "NORMALIZED_RECORDS_RECEIVED" if adapter_id.startswith("legacy") else "IMPORTED")
                self.assertEqual(wrong_result["claim_review_status"], "FAILED")
                self.assertEqual(wrong_result["status"], "CLAIM_REVIEW_FAILED")
                unknown_file = self.root / f"unknown-{adapter_id}.jsonl"
                unknown_file.write_text(json.dumps(unknown) + "\n", encoding="utf-8")
                unknown_result = self._run(adapter_id, self.root / f"unknown-run-{adapter_id}", claim_review_path=unknown_file)
                unknown_row = json.loads((self.root / f"unknown-run-{adapter_id}/claim-review.jsonl").read_text().splitlines()[0])
                self.assertEqual(unknown_result["status"], "CLAIM_REVIEW_FAILED")
                self.assertEqual(unknown_row["evidence_anchor_status"], "UNKNOWN_SOURCE")

    def test_unknown_draft_id_is_rejected_and_w3_anchor_does_not_claim_semantic_validation(self):
        unknown_draft = self.root / "unknown-draft.md"
        unknown_draft.write_text(self.draft.read_text() + "Unknown: [S99].\n", encoding="utf-8")
        for adapter_id in ("legacy-openalex-v1", "e37-source-snapshot-v1"):
            with self.subTest(adapter=adapter_id):
                result = self._run(adapter_id, self.root / f"bad-draft-{adapter_id}", draft_path=unknown_draft)
                self.assertEqual(result["input"]["draft_sha256"], hashlib.sha256(unknown_draft.read_bytes()).hexdigest())
                self.assertEqual(result["status"], "INVALID_DRAFT")
                self.assertIn("S99", result["draft_error"])
        w3 = self._review(
            "W3", "Every individual permanently regained all lost weight.", "S2",
            "From week 20 to week 68, mean weight change was -7.9% with continued semaglutide and +6.9% after switch to placebo.",
            "SUPPORTS",
        )
        w3_file = self.root / "w3.jsonl"
        w3_file.write_text(json.dumps(w3) + "\n", encoding="utf-8")
        result = self._run("e37-source-snapshot-v1", self.root / "w3-run", claim_review_path=w3_file)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["semantic_validation_status"], "NOT_PERFORMED")
        self.assertIn("judge whether a quote supports a claim", (self.root / "w3-run/report.md").read_text())

    def test_candidate_only_captured_text_anchor_is_explicit_and_legacy_rejects_it(self):
        raw_quote = self.capture_texts[1].splitlines()[0]
        capture_claim = self._review(
            "CAPTURE-ONLY", "Candidate binds a quote to the saved reader capture.",
            "S2", raw_quote,
        )
        capture_claim["evidence_field"] = "captured_text"
        claim_file = self.root / "capture-only.jsonl"
        claim_file.write_text(json.dumps(capture_claim) + "\n", encoding="utf-8")
        candidate = self._run(
            "e37-source-snapshot-v1", self.root / "capture-only-candidate",
            claim_review_path=claim_file,
        )
        ledger = json.loads((self.root / "capture-only-candidate/claim-review.jsonl").read_text().splitlines()[0])
        self.assertEqual(candidate["status"], "COMPLETED")
        self.assertEqual(ledger["evidence_anchor_status"], "EXACT_MATCH")
        self.assertEqual(ledger["evidence_field"], "captured_text")
        false_quote = dict(capture_claim)
        false_quote["claim_id"] = "CAPTURE-ONLY-WRONG-QUOTE"
        false_quote["evidence_quote"] = "This sentence is not present in the frozen capture."
        false_quote_file = self.root / "capture-only-wrong-quote.jsonl"
        false_quote_file.write_text(json.dumps(false_quote) + "\n", encoding="utf-8")
        false_quote_result = self._run(
            "e37-source-snapshot-v1", self.root / "capture-only-wrong-quote-candidate",
            claim_review_path=false_quote_file,
        )
        false_quote_ledger = json.loads(
            (self.root / "capture-only-wrong-quote-candidate/claim-review.jsonl")
            .read_text().splitlines()[0]
        )
        self.assertEqual(false_quote_result["claim_review_status"], "FAILED")
        self.assertEqual(false_quote_result["status"], "CLAIM_REVIEW_FAILED")
        self.assertEqual(false_quote_ledger["evidence_anchor_status"], "NOT_FOUND")
        with self.assertRaisesRegex(ValueError, "does not support captured_text"):
            self._run(
                "legacy-openalex-v1", self.root / "capture-only-legacy",
                claim_review_path=claim_file,
            )
        self.assertFalse((self.root / "capture-only-legacy").exists())

    def test_candidate_missing_malformed_or_mismatched_digest_fails_before_output(self):
        with self.assertRaisesRegex(ValueError, "requires --expected-digests"):
            self._run("e37-source-snapshot-v1", self.root / "missing-lock", expected_digests_path=None)
        missing_file = self.root / "missing-entry.json"
        missing_file.write_text(json.dumps({"S1": self.digest_lock["S1"]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing source IDs: S2"):
            self._run("e37-source-snapshot-v1", self.root / "missing-entry-run", expected_digests_path=missing_file)
        malformed = dict(self.digest_lock)
        malformed["S2"] = "not-a-sha256"
        malformed_file = self.root / "malformed.json"
        malformed_file.write_text(json.dumps(malformed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            self._run("e37-source-snapshot-v1", self.root / "malformed-run", expected_digests_path=malformed_file)
        mismatch = dict(self.digest_lock)
        mismatch["S2"] = "0" * 64
        mismatch_file = self.root / "mismatch.json"
        mismatch_file.write_text(json.dumps(mismatch), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "capture digest mismatch for S2"):
            self._run("e37-source-snapshot-v1", self.root / "mismatch-run", expected_digests_path=mismatch_file)
        for output in ("missing-lock", "missing-entry-run", "malformed-run", "mismatch-run"):
            self.assertFalse((self.root / output).exists())

    def test_invalid_source_set_digest_and_empty_claim_review_leave_no_output(self):
        with self.assertRaisesRegex(ValueError, "canonical source-set digest mismatch"):
            self._run(
                "legacy-openalex-v1", self.root / "source-digest-mismatch",
                expected_source_set_digest="0" * 64,
            )
        empty_claims = self.root / "empty-claims.jsonl"
        empty_claims.write_text("\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "at least one claim-review row"):
            self._run(
                "legacy-openalex-v1", self.root / "empty-claims-run",
                claim_review_path=empty_claims,
            )
        self.assertFalse((self.root / "source-digest-mismatch").exists())
        self.assertFalse((self.root / "empty-claims-run").exists())

    def test_manifest_and_claim_field_order_does_not_change_the_common_consumer(self):
        reordered_manifest = self.sources_dir / "manifest-reordered.jsonl"
        manifest_rows = [dict(reversed(list(row.items()))) for row in self.source_rows]
        reordered_manifest.write_text("".join(json.dumps(row) + "\n" for row in manifest_rows), encoding="utf-8")
        reordered_claims = self.root / "claims-reordered.jsonl"
        claim_rows = [json.loads(line) for line in self.claims.read_text().splitlines()]
        reordered_claims.write_text("".join(
            json.dumps(dict(reversed(list(row.items())))) + "\n" for row in claim_rows
        ), encoding="utf-8")
        legacy = self._run("legacy-openalex-v1", self.root / "legacy-reordered", claim_review_path=reordered_claims)
        candidate = self._run(
            "e37-source-snapshot-v1", self.root / "candidate-reordered",
            source_snapshots_path=reordered_manifest, claim_review_path=reordered_claims,
        )
        self.assertEqual(legacy["claim_review_status"], "COMPLETED")
        self.assertEqual(candidate["claim_review_status"], "COMPLETED")
        legacy_rows = [json.loads(line) for line in (self.root / "legacy-reordered/claim-review.jsonl").read_text().splitlines()]
        candidate_rows = [json.loads(line) for line in (self.root / "candidate-reordered/claim-review.jsonl").read_text().splitlines()]
        self.assertEqual(
            [row["evidence_anchor_status"] for row in legacy_rows],
            [row["evidence_anchor_status"] for row in candidate_rows],
        )
        self.assertEqual(legacy["input"]["canonical_source_set_sha256"], candidate["input"]["canonical_source_set_sha256"])
        self.assertNotEqual(legacy["input"]["sha256"], candidate["input"]["manifest_sha256"])

    def test_input_capabilities_are_explicit_and_next_run_can_select_legacy(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_CAPABILITY"):
            self._run(
                "legacy-openalex-v1", self.root / "unsupported-legacy",
                source_snapshots_path=self.manifest, legacy_records_path=self.records,
            )
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_CAPABILITY"):
            self._run(
                "e37-source-snapshot-v1", self.root / "unsupported-candidate",
                source_snapshots_path=None, legacy_records_path=self.records,
            )
        first = self._run("e37-source-snapshot-v1", self.root / "candidate-first")
        first_receipt_path = self.root / "candidate-first/receipt.json"
        first_receipt_sha = hashlib.sha256(first_receipt_path.read_bytes()).hexdigest()
        second = self._run("legacy-openalex-v1", self.root / "legacy-next")
        self.assertEqual(hashlib.sha256(first_receipt_path.read_bytes()).hexdigest(), first_receipt_sha)
        self.assertEqual(first["context"]["adapter_id"], "e37-source-snapshot-v1")
        self.assertEqual(second["context"]["adapter_id"], "legacy-openalex-v1")
        self.assertNotEqual(first["context"]["episode_id"], "")
        self.assertFalse(first["rollback"]["same_run_fallback"])
        self.assertEqual(first["rollback"]["existing_nonempty_output_directory"], "rejected")


if __name__ == "__main__":
    unittest.main()
