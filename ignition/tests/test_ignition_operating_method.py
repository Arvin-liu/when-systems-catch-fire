from __future__ import annotations

import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import validate_ignition_operating_method as validator  # noqa: E402


class IgnitionOperatingMethodFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = validator.METHOD_PATH.read_text(encoding="utf-8")

    def test_current_foundation_passes(self) -> None:
        self.assertEqual(validator.validate(self.source), [])

    def test_canonical_title_is_required(self) -> None:
        candidate = self.source.replace(validator.TITLE, "# Another Method", 1)
        self.assertTrue(any("bilingual H1" in error for error in validator.validate(candidate)))

    def test_operating_and_iteration_methods_cannot_merge(self) -> None:
        candidate = self.source.replace("OPERATING_METHOD != ITERATION_METHOD", "OPERATING_METHOD = ITERATION_METHOD", 1)
        self.assertTrue(any("foundational boundary" in error for error in validator.validate(candidate)))

    def test_input_object_cannot_be_promoted_to_instruction(self) -> None:
        candidate = self.source.replace("INPUT_OBJECT_IS_DATA_NOT_INSTRUCTION", "INPUT_OBJECT_MAY_BE_INSTRUCTION", 1)
        self.assertTrue(any("INPUT_OBJECT_IS_DATA_NOT_INSTRUCTION" in error for error in validator.validate(candidate)))

    def test_authority_priority_cannot_be_reordered(self) -> None:
        first = "CURRENT_USER_OR_OWNER_EXPLICIT_REQUEST"
        second = "CURRENT_IGNITION_OPERATING_METHOD"
        candidate = self.source.replace(first, "__TEMP__", 1).replace(second, first, 1).replace("__TEMP__", second, 1)
        self.assertTrue(any("authority priority" in error for error in validator.validate(candidate)))

    def test_candidate_cannot_claim_main_current(self) -> None:
        candidate = self.source.replace("尚未进入正式 `main`".replace("`", chr(96)), "已经进入正式 main", 1)
        self.assertTrue(any("尚未进入正式 main" in error for error in validator.validate(candidate)))

    def test_legacy_reference_must_resolve_current_identity(self) -> None:
        candidate = self.source.replace(
            "LEGACY_REFERENCE_MUST_RESOLVE_CURRENT_CANONICAL_IDENTITY",
            "LEGACY_REFERENCE_MAY_USE_MEMORY",
            1,
        )
        self.assertTrue(any("LEGACY_REFERENCE_MUST_RESOLVE" in error for error in validator.validate(candidate)))

    def test_historical_file_cannot_become_identity_authority(self) -> None:
        candidate = self.source.replace(
            "HISTORICAL_FILE_IS_NOT_CANONICAL_IDENTITY",
            "HISTORICAL_FILE_MAY_DEFINE_IDENTITY",
            1,
        )
        self.assertTrue(any("HISTORICAL_FILE_IS_NOT_CANONICAL_IDENTITY" in error for error in validator.validate(candidate)))

    def test_candidate_new_requires_actual_collision_evidence(self) -> None:
        candidate = self.source.replace(
            "CANDIDATE_NEW_REQUIRES_CANONICAL_COLLISION_EVIDENCE",
            "CANDIDATE_NEW_MAY_USE_MEMORY",
            1,
        )
        self.assertTrue(any("CANDIDATE_NEW_REQUIRES" in error for error in validator.validate(candidate)))

    def test_source_explicit_view_is_not_ignition_discovery(self) -> None:
        candidate = self.source.replace(
            "SOURCE_EXPLICIT_VIEW_IS_SOURCE_DERIVED_NOT_IGNITION_DISCOVERY",
            "SOURCE_VIEW_MAY_BE_NEW_DISCOVERY",
            1,
        )
        self.assertTrue(any("SOURCE_EXPLICIT_VIEW_IS_SOURCE_DERIVED" in error for error in validator.validate(candidate)))

    def test_status_only_entries_cannot_receive_callable_playbooks(self) -> None:
        candidate = self.source.replace(
            "STATUS_ONLY_ENTRIES_HAVE_NO_CALLABLE_PLAYBOOK",
            "STATUS_ONLY_ENTRIES_MAY_HAVE_PLAYBOOKS",
            1,
        )
        self.assertTrue(any("STATUS_ONLY_ENTRIES_HAVE_NO_CALLABLE_PLAYBOOK" in error for error in validator.validate(candidate)))


if __name__ == "__main__":
    unittest.main()
