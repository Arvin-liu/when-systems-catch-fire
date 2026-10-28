from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


IGNITION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IGNITION_ROOT / "tools"))
import validate_current_task_lineage as validator  # noqa: E402


class CurrentTaskLineageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = validator.load_json(validator.STATUS_PATH)

    def test_canonical_lineage_passes(self) -> None:
        self.assertEqual(validator.validate(self.source), [])

    def test_unexecuted_predecessor_carries_successor_lineage(self) -> None:
        predecessor = self.source["lineages"][0]["predecessor"]
        self.assertEqual(predecessor["task_file_status"], "HISTORICAL_UNEXECUTED")
        self.assertEqual(predecessor["requirement_lineage_status"], "REBASED_INTO_127")
        self.assertEqual(predecessor["canonical_status"], "HISTORICAL_UNEXECUTED_REBASED_INTO_127")

    def test_wrong_predecessor_status_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.source)
        mutated["lineages"][0]["predecessor"]["canonical_status"] = "COMPLETED"
        self.assertTrue(validator.validate(mutated))

    def test_epistemic_boundary_is_unchanged(self) -> None:
        self.assertEqual(self.source["current_state"]["current_state_status"], "CURRENT_WITH_OPEN_OBLIGATIONS")
        self.assertEqual(self.source["current_state"]["epistemically_accepted"], 0)

    def test_negative_fixture_manifest_covers_four_required_failures(self) -> None:
        fixture = validator.load_json(validator.FIXTURE_PATH)
        ids = {row["id"] for row in fixture["fixtures"]}
        self.assertTrue({
            "stale-deferred-current-surface",
            "old-task-marked-completed",
            "successor-lineage-missing",
            "historical-record-misclassified-current",
        }.issubset(ids))

    def test_stale_deferred_surface_is_rejected(self) -> None:
        text = "HISTORICAL_UNEXECUTED REBASED_INTO_127 COMPLETED_WITH_CLASSIFIED_RESIDUALS DEFERRED_PENDING_REBASE"
        errors = validator.validate_surface_text(self.source, text, "fixture")
        self.assertTrue(any(error.startswith("TASK_LINEAGE_STALE_DEFERRED") for error in errors))

    def test_old_task_completed_surface_is_rejected(self) -> None:
        text = "REBASED_INTO_127 COMPLETED_WITH_CLASSIFIED_RESIDUALS TASK125_FILE_STATUS=COMPLETED"
        errors = validator.validate_surface_text(self.source, text, "fixture")
        self.assertTrue(any(error.startswith("TASK_LINEAGE_OLD_TASK_COMPLETED") for error in errors))

    def test_successor_without_lineage_is_rejected(self) -> None:
        text = "HISTORICAL_UNEXECUTED COMPLETED_WITH_CLASSIFIED_RESIDUALS"
        errors = validator.validate_surface_text(self.source, text, "fixture")
        self.assertTrue(any(error.startswith("TASK_LINEAGE_SUCCESSOR_LINEAGE_MISSING") for error in errors))

    def test_protected_history_cannot_be_classified_as_current(self) -> None:
        path = self.source["protected_historical_paths"][0]
        errors = validator.validate_history_classification(self.source, path, "CURRENT_SURFACE")
        self.assertTrue(any(error.startswith("TASK_LINEAGE_HISTORICAL_MISCLASSIFIED_CURRENT") for error in errors))

    def test_publication_projection_is_ref_derived(self) -> None:
        text = validator.resolve_repo_path("ignition/AI-START-HERE.md").read_text(encoding="utf-8")
        self.assertEqual(validator.validate_publication_projection(text, "ignition/AI-START-HERE.md"), [])

    def test_static_publication_state_is_rejected_from_current_block(self) -> None:
        text = "<!-- CURRENT-SNAPSHOT:BEGIN profile=ai schema=current-snapshot-r1 -->\nREMOTE_REF_OBSERVATION refs/heads/main NOT_PUBLISHED\n<!-- CURRENT-SNAPSHOT:END -->"
        errors = validator.validate_publication_projection(text, "ignition/AI-START-HERE.md")
        self.assertTrue(any("STATIC_PUBLICATION_STATE" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
