from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "tools/research/junction_vs_local_predicates_task157.py"
SPEC = importlib.util.spec_from_file_location("task157_experiment", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class JunctionVsLocalPredicatesTask157Tests(unittest.TestCase):
    def test_frozen_corpus_shape_and_blind_separation(self) -> None:
        packets, answers, manifests, splits = MODULE.make_corpus()
        self.assertEqual([], MODULE.validate_corpus(packets, answers, manifests))
        self.assertEqual(192, len(packets))
        self.assertEqual(192, len(answers))
        self.assertEqual(96, len(manifests))
        self.assertEqual(96, len(splits))
        self.assertEqual(8, len({row["family"] for row in manifests}))
        self.assertEqual(24, sum(row["novel_composition"] for row in manifests))

    def test_scoring_is_deterministic_without_answer_key(self) -> None:
        packets, _, _, _ = MODULE.make_corpus()
        first = MODULE.score_packets(packets)
        second = MODULE.score_packets(packets)
        self.assertEqual(MODULE.jsonl_bytes(first), MODULE.jsonl_bytes(second))
        self.assertEqual([], MODULE.validate_score_rows(first))

    def test_mj_catches_binding_families_that_ml_does_not_all_cover(self) -> None:
        packets, answers, _, _ = MODULE.make_corpus()
        by_id = {packet["fixture_id"]: packet for packet in packets}
        answer_map = {row["fixture_id"]: row for row in answers}
        primary_f2 = next(packet for packet in packets if packet["pair_id"] == "F2-P10" and answer_map[packet["fixture_id"]]["member_role"] == "PRIMARY")
        self.assertEqual("flag", MODULE.model_record("MJ", primary_f2)["decision"])
        primary_f8 = next(row["fixture_id"] for row in answers if row["pair_id"] == "F8-P10" and row["member_role"] == "PRIMARY")
        self.assertEqual("flag", MODULE.model_record("MJ", by_id[primary_f8])["decision"])

    def test_controls_keep_unknown_distinct_and_migration_typed(self) -> None:
        packets, answers, _, _ = MODULE.make_corpus()
        by_answer = {row["fixture_id"]: row for row in answers}
        unknown = next(packet for packet in packets if by_answer[packet["fixture_id"]]["control_variant"] == "unknown_contract" and by_answer[packet["fixture_id"]]["member_role"] == "MATCHED_CONTROL")
        migration = next(packet for packet in packets if by_answer[packet["fixture_id"]]["control_variant"] == "alias_migration" and by_answer[packet["fixture_id"]]["member_role"] == "MATCHED_CONTROL")
        self.assertEqual("abstain", MODULE.model_record("MJ", unknown)["decision"])
        self.assertEqual("no_flag", MODULE.model_record("MJ", migration)["decision"])

    def test_metamorphic_suite_is_violation_free(self) -> None:
        packets, answers, _, _ = MODULE.make_corpus()
        rows = MODULE.metamorphic_rows(packets, answers)
        self.assertGreaterEqual(len(rows), 300)
        self.assertEqual([], [row for row in rows if not row["passed"]])


if __name__ == "__main__":
    unittest.main()
