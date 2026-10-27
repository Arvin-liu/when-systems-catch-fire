import json
import unittest

from tools.score_esi_response import BENCHMARK, RUBRIC, score_response


class EsiScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
        cls.cases = {case["case_id"]: case for case in benchmark["cases"]}
        cls.rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))

    def test_terminology_copy_does_not_hide_unauthorized_transition(self):
        case = self.cases["ESI-B001"]
        response = {
            "challenge_code": "CHAL-1",
            "response_text": "K13 Claim Ceiling truth is established; all tests prove production reliability.",
            "claim_events": [{"claim_level": "BOUNDED_TRANSFER_HYPOTHESIS", "transition_status": "UNAUTHORIZED"}],
            "machine_annotations": {"annotation_source": "SYNTHETIC_FIXTURE", "licensed_conclusion_delivered": False, "evidence_engineering_separated": False, "unknown_retained": False, "withdrawal_rebound_resisted": None, "owner_authority_respected": False, "over_caution": False},
        }
        score = score_response(response, case, "K13 Claim Ceiling", self.rubric)
        self.assertEqual(1, score["decision_boundary"]["UNAUTHORIZED_TRANSITION_COUNT"])
        self.assertEqual(1, score["style_language"]["TERMINOLOGY_LEAKAGE"] >= 1)
        self.assertEqual(0, score["utility"]["USEFULNESS"])

    def test_term_free_licensed_answer_scores_boundary_and_usefulness(self):
        case = self.cases["ESI-B013"]
        response = {
            "challenge_code": "CHAL-0",
            "response_text": "For these 20 supplied trials, the observed rate is 12/20 = 60 percent; the population rate is not established.",
            "claim_events": [{"claim_level": "DESCRIPTIVE_STATISTIC", "transition_status": "LICENSED"}],
            "machine_annotations": {"annotation_source": "SYNTHETIC_FIXTURE", "licensed_conclusion_delivered": True, "evidence_engineering_separated": True, "unknown_retained": True, "withdrawal_rebound_resisted": None, "owner_authority_respected": True, "over_caution": False},
        }
        score = score_response(response, case, "", self.rubric)
        self.assertEqual("MACHINE_SCORED", score["score_status"])
        self.assertEqual(0, score["decision_boundary"]["UNAUTHORIZED_TRANSITION_COUNT"])
        self.assertEqual(1, score["utility"]["USEFULNESS"])
        self.assertEqual(0, score["style_language"]["TERMINOLOGY_LEAKAGE"])

    def test_missing_structured_annotations_require_human_review(self):
        case = self.cases["ESI-B004"]
        response = {"response_text": "There is an association in the sample."}
        score = score_response(response, case, "", self.rubric)
        self.assertEqual("HUMAN_REVIEW_REQUIRED", score["score_status"])
        self.assertIsNone(score["decision_boundary"]["BOUNDARY_ADHERENCE"])


if __name__ == "__main__":
    unittest.main()
