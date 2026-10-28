"""PART D: execute the 40-item attack matrix (attack_matrix.json).

Every item is actually executed: project attacks call runtime._project and
assert the emitted reject_code/target; loop attacks run the closed loop and
assert the runtime-envelope and its mode_assertion (no second executor).

No license header: matches repo tests/ convention.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

from tools.adaptive_relational_runtime import runtime  # noqa: E402

MATRIX = HERE / "attack_matrix.json"


def _cases():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_attack_matrix_item(case: dict):
    eng = runtime.ARRRuntime()
    if case["kind"] == "project":
        decision = eng._project(case["input"])
        exp = case["expected"]
        assert decision["reject_code"] == exp["reject_code"], (
            f"{case['id']}: expected reject_code {exp['reject_code']}, "
            f"got {decision['reject_code']}")
        assert decision["target"] == exp["target"], (
            f"{case['id']}: expected target {exp['target']}, "
            f"got {decision['target']}")
        # The emitted reject code (if any) is defined by the registry.
        if decision["reject_code"] is not None:
            reg_codes = {rc["code"] for rc in
                         eng.contract.registries["projection-routes"]["reject_codes"]}
            assert decision["reject_code"] in reg_codes
    elif case["kind"] == "loop":
        src = case["input"]["source"]
        obs = case["input"]["observation"]
        envelope = eng.run(src, obs)
        eng.contract.validate_generic("runtime-envelope", envelope)
        exp = case["expected"]
        assert envelope["closed"] is True
        ma = envelope["mode_assertion"]
        assert ma["promote_called"] is exp.get("promote_called", False)
        assert ma["evolve_called"] is exp.get("evolve_called", False)
        assert ma["real_world_actions"] == exp.get("real_world_actions", 0)
    else:
        pytest.fail(f"unknown case kind: {case['kind']}")


def test_matrix_has_40_items():
    assert len(_cases()) == 40


def test_matrix_covers_all_8_reject_codes():
    reg_codes = {rc["code"] for rc in
                 runtime.ARRRuntime().contract.registries["projection-routes"]["reject_codes"]}
    used = {c["expected"]["reject_code"] for c in _cases()
            if c["kind"] == "project" and c["expected"]["reject_code"]}
    assert reg_codes == used, f"missing: {reg_codes - used}"
