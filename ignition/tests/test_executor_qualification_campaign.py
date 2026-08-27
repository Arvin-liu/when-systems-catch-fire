from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from agent_federation.qualification_campaign import QualificationCampaignError, blocker_fingerprint, validate_campaign


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "data/operations/iterations/143/executor-qualification-campaign-r1.json"


class ExecutorQualificationCampaignTests(unittest.TestCase):
    def test_initial_campaign_is_valid_and_bounded(self) -> None:
        document = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
        summary = validate_campaign(document)
        self.assertTrue(summary["safe"])
        self.assertEqual(summary["attempt_budget"], 3)
        self.assertEqual(summary["target_families_qualifying"], 3)

    def test_blocker_fingerprint_is_order_independent(self) -> None:
        self.assertEqual(blocker_fingerprint(["B", "A"]), blocker_fingerprint(["A", "B"]))

    def test_codex_cannot_be_reclassified_as_live_in_initial_ledger(self) -> None:
        document = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
        codex = next(row for row in document["families"] if row["executor_id"] == "external.codex")
        codex["state"] = "LIVE_SELECTABLE"
        codex["blockers"] = []
        codex["blocker_fingerprint"] = blocker_fingerprint([])
        with self.assertRaisesRegex(QualificationCampaignError, "Codex"):
            validate_campaign(document)

    def test_secret_like_field_is_rejected(self) -> None:
        document = copy.deepcopy(json.loads(CAMPAIGN.read_text(encoding="utf-8")))
        document["families"][0]["token_presence"] = False
        with self.assertRaisesRegex(QualificationCampaignError, "secret-like"):
            validate_campaign(document)


if __name__ == "__main__":
    unittest.main()
