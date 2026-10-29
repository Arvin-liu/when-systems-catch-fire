#!/usr/bin/env python3
"""repair-r3 adversarial closure test for counterfactual_unrealized_path (RB09-CALLER-ASSERTED-SEMANTICS).

Builds a valid positive bundle from REAL Git objects, runs the wired counterfactual_unrealized_path gate,
and asserts:
  * positive pilot                       -> exit 0
  * semantically-false (flipped value)   -> exit 30 (EVALUATOR_RULE_FAILED, 30+index)
  * unrelated-valid-evidence laundering  -> nonzero

The gate's CONFIG["evaluator"] = evaluate_counterfactual_unrealized_path recomputes every rule from record
values + authoritative evidence bytes; caller facts/status are ignored.
"""
import ast
import json
import unittest
from pathlib import Path

from tests.r3_evaluator_testlib import (
    build_bundle, flip_value, launder, run_gate, write_bundle,
)

REPO = Path(__file__).resolve().parents[1]
GATE = REPO / "tools/counterfactual/validate_counterfactual_unrealized_path_gate.py"
CAP = "counterfactual_unrealized_path"


def _config():
    txt = GATE.read_text()
    s = txt.split("json.loads(", 1)[1]
    q = s.index('"')
    rest = s[q + 1:]
    i, n = 0, len(rest)
    while i < n:
        if rest[i] == '"' and (i == 0 or rest[i - 1] != '\\'):
            j = i + 1
            while j < n and rest[j] == ' ':
                j += 1
            if j < n and rest[j] == ')':
                lit = rest[:i]
                break
        i += 1
    return json.loads(ast.literal_eval('"' + lit + '"'))


class CounterfactualUnrealizedPathR3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = _config()
        from tools.governance.r3_capability_evaluators import (
            get_matrix, CAPABILITY_SPECS,
        )
        cls.matrix = get_matrix(CAP)
        cls.rule_fields = CAPABILITY_SPECS[CAP]["rule_fields"]

    def _bundle(self):
        return build_bundle(self.config, self.matrix, self.rule_fields)

    def test_positive_pilot_passes(self):
        b = self._bundle()
        p = write_bundle(b)
        rc, out, err = run_gate(GATE, p)
        self.assertEqual(rc, 0, f"positive bundle should pass; stderr={err}; out={out}")

    def test_semantically_false_but_git_valid_fails(self):
        b = self._bundle()
        rid = self.config["rules"][0]
        flip_value(b, self.rule_fields, rid, "X_CONTRADICTS_RULE_NOT_IN_EVIDENCE")
        p = write_bundle(b)
        rc, out, err = run_gate(GATE, p)
        self.assertNotEqual(rc, 0, "caller-asserted facts must not bypass recomputation")
        self.assertEqual(
            rc, 30,
            f"first rule (index 0) should fail with 30, got {rc}; out={out}",
        )

    def test_unrelated_valid_evidence_laundering_fails(self):
        b = self._bundle()
        launder(b, self.rule_fields)
        p = write_bundle(b)
        rc, out, err = run_gate(GATE, p)
        self.assertNotEqual(rc, 0, "single-blob laundering must be rejected")


if __name__ == "__main__":
    unittest.main()
