from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools/research/cross_contract_prospective_experiment.py"
SPEC = importlib.util.spec_from_file_location("task156_experiment", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CrossContractProspectiveExperimentTests(unittest.TestCase):
    def test_frozen_corpus_has_required_pairs_and_separation(self) -> None:
        packets, answers, manifests, _ = MODULE.make_corpus()
        self.assertEqual([], MODULE.validate_corpus_structure(packets, answers, manifests))
        self.assertEqual(96, len(packets))
        self.assertEqual(96, len(answers))
        self.assertEqual(48, len(manifests))
        self.assertGreaterEqual(sum(item["novel_recombination"] for item in manifests), 16)
        self.assertGreaterEqual(sum(item["distractor_fields_present"] for item in manifests), 16)
        self.assertGreaterEqual(sum(item["cross_object_family"] for item in manifests), 16)

    def test_scoring_is_deterministic_and_does_not_need_answer_key(self) -> None:
        packets, _, _, _ = MODULE.make_corpus()
        first = MODULE.score_packets(packets)
        second = MODULE.score_packets(packets)
        self.assertEqual(MODULE.jsonl_bytes(first), MODULE.jsonl_bytes(second))
        self.assertEqual([], MODULE.validate_score_rows(first))
        self.assertEqual(96 * 4, len(first))

    def test_research_predicates_keep_m3_m3r_and_m4b_distinct(self) -> None:
        packets, _, _, _ = MODULE.make_corpus()
        by_id = {packet["fixture_id"]: packet for packet in packets}

        # A consequence junction is visible to M3; the matched control is not.
        self.assertEqual("FLAG", MODULE.model_record("M3", by_id["F1-P04-A"])["result"])
        self.assertEqual("NO_FLAG", MODULE.model_record("M3", by_id["F1-P04-B"])["result"])

        # The CC-020-shaped source/projection defect is on M3R's refined claim edge.
        self.assertEqual("NO_FLAG", MODULE.model_record("M3", by_id["F3-P02-A"])["result"])
        self.assertEqual("FLAG", MODULE.model_record("M3R", by_id["F3-P02-A"])["result"])

        # The lifecycle binding challenge is invisible to M3R but visible to M4B.
        self.assertEqual("NO_FLAG", MODULE.model_record("M3R", by_id["F2-P01-A"])["result"])
        self.assertEqual("FLAG", MODULE.model_record("M4B", by_id["F2-P01-A"])["result"])

        # Signer-only incompleteness does not become an actionable failure.
        self.assertNotEqual("FLAG", MODULE.model_record("M4B", by_id["F6-P07-A"])["result"])

    def test_command_score_reads_only_blind_inputs(self) -> None:
        payloads = MODULE.frozen_payloads()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, payload in payloads.items():
                (root / name).write_bytes(payload)
            old_research = MODULE.RESEARCH
            MODULE.RESEARCH = root
            try:
                output = root / "score.jsonl"
                self.assertEqual(0, MODULE.command_score(output))
                self.assertTrue(output.is_file())
            finally:
                MODULE.RESEARCH = old_research

    def test_metamorphic_suite_is_explicit_and_violation_free(self) -> None:
        packets, answers, _, _ = MODULE.make_corpus()
        score_rows = MODULE.score_packets(packets)
        score_map = MODULE.output_map(score_rows)
        results = [MODULE.classification_for(score_map, answer) for answer in sorted(answers, key=lambda item: item["fixture_id"])]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            MODULE.write_bytes(root / "blind-packets.jsonl", MODULE.jsonl_bytes(packets))
            old_research = MODULE.RESEARCH
            MODULE.RESEARCH = root
            try:
                metamorphic = MODULE.metamorphic_rows(results)
            finally:
                MODULE.RESEARCH = old_research
        self.assertEqual([], [row for row in metamorphic if not row["passed"]])
        self.assertGreaterEqual(len(metamorphic), 6 * 4)
        self.assertTrue(
            {
                "repair_exact_missing_junction_flips_flag_to_no_flag",
                "binding_change_flips_only_covering_models",
                "irrelevant_evidence_does_not_upgrade_claim_scope",
                "valid_signature_does_not_repair_consequence_gap",
                "rollback_label_does_not_repair_irreversible_effect",
                "safe_authorized_alternative_may_change_abstention",
                "deadline_passage_does_not_create_new_failure",
            }.issubset({row["property"] for row in metamorphic})
        )


if __name__ == "__main__":
    unittest.main()
