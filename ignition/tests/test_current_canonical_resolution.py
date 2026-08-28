from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools/foundation"))
import resolve_current_canonical_asset as resolver  # noqa: E402


class CurrentCanonicalResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cards = resolver.load_jsonl(resolver.IDENTITY_CARDS_PATH)
        cls.aliases = resolver.load_jsonl(resolver.ALIAS_INDEX_PATH)
        cls.corrections = resolver.load_jsonl(resolver.CORRECTIONS_PATH)
        cls.mappings = resolver.load_jsonl(resolver.LEGACY_MAPPINGS_PATH)

    def test_all_twelve_current_authority_fixtures_pass(self) -> None:
        fixtures = json.loads(resolver.FIXTURE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(fixtures["cases"]), 12)
        self.assertEqual(resolver.validate_fixtures(fixtures), [])

    def test_exposed_legacy_labels_preserve_current_quarantine(self) -> None:
        for reference in ("D1", "D2", "D5", "T7", "A5"):
            result = resolver.resolve_reference(reference)
            self.assertEqual(result["resolution_status"], resolver.RESOLVED)
            self.assertEqual(result["canonical_id"], reference)
            self.assertEqual(result["final_disposition"], "QUARANTINE_UNTIL_DEFINED")
            self.assertFalse(result["resolution_establishes_external_truth"])

    def test_d127_identity_correction_uses_alias_and_correction_authority(self) -> None:
        direct = resolver.resolve_reference("D127")
        corrected = resolver.resolve_reference("D127 乘法归零律")
        self.assertEqual(direct["canonical_id"], "D127")
        self.assertEqual(direct["primary_identity"], "STRUCTURAL_METAPHOR")
        self.assertEqual(corrected["canonical_id"], "T2")
        self.assertEqual(corrected["match_kind"], "IDENTITY_CORRECTED_ALIAS")
        self.assertEqual(
            [row["correction_id"] for row in corrected["corrections"]],
            ["CORR-98-D127", "CORR-98-T2"],
        )
        self.assertIn(resolver.CORRECTION_AUTHORITY, corrected["authority_sources"])

    def test_historical_path_and_near_match_fail_closed(self) -> None:
        for reference in ("统一函数总表/0012-T2-乘法归零律.md", "D127 乘法清零律"):
            result = resolver.resolve_reference(reference)
            self.assertEqual(result["resolution_status"], resolver.UNRESOLVED)
            self.assertIsNone(result["canonical_id"])
            self.assertFalse(result["memory_or_fuzzy_resolution_used"])
            self.assertFalse(result["historical_file_used_as_identity"])

    def test_duplicate_title_is_ambiguous_not_arbitrarily_selected(self) -> None:
        cards = copy.deepcopy(self.cards)
        duplicate = copy.deepcopy(next(row for row in cards if row["canonical_id"] == "D1"))
        duplicate["canonical_id"] = "SYNTHETIC-DUPLICATE"
        duplicate["historical_ids"] = ["SYNTHETIC-DUPLICATE"]
        cards.append(duplicate)
        result = resolver.resolve_reference_from_rows(
            "锁定强度函数", cards, [], self.corrections, self.mappings
        )
        self.assertEqual(result["resolution_status"], resolver.AMBIGUOUS)
        self.assertEqual(
            result["candidate_canonical_ids"], ["D1", "SYNTHETIC-DUPLICATE"]
        )

    def test_corrected_alias_without_current_correction_fails_closed(self) -> None:
        aliases = [{
            "alias": "legacy wrong label",
            "alias_id": "SYNTHETIC-ALIAS",
            "destination": "RESULTS/CORRECTIONS.md",
            "lineage_key": "FUNCTION_IDENTITY_UNKNOWN_D1",
            "replacement": "canonical ID 是 D1",
            "status": "IDENTITY_CORRECTED",
        }]
        result = resolver.resolve_reference_from_rows(
            "legacy wrong label", self.cards, aliases, [], self.mappings
        )
        self.assertEqual(result["resolution_status"], resolver.UNRESOLVED)
        self.assertEqual(result["failure_reason"], "CORRECTED_ALIAS_WITHOUT_CURRENT_CORRECTION")

    def test_duplicate_canonical_id_invalidates_authority(self) -> None:
        cards = copy.deepcopy(self.cards)
        cards.append(copy.deepcopy(cards[0]))
        with self.assertRaises(resolver.CanonicalAuthorityError):
            resolver.resolve_reference_from_rows("D1", cards, self.aliases, self.corrections, self.mappings)


if __name__ == "__main__":
    unittest.main()
