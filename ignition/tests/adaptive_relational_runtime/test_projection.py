"""PART C (b): projection emits all 8 reject codes, each present in and
matching the projection-routes registry.

No license header: matches repo tests/ convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

from tools.adaptive_relational_runtime import runtime  # noqa: E402
from helpers import base_relation, full_temporal_scope  # noqa: E402

PSD = {"system_boundary": "b", "probability_value": 0.5, "obs_not_do": True}


def _registry_reject_codes(eng):
    return {rc["code"] for rc in
            eng.contract.registries["projection-routes"]["reject_codes"]}


# One canonical trigger per reject code.
TRIGGERS = {
    "not_a_relation_record": {"record_kind": "Source", "scope": {"domain": "x"}},
    "relation_schema_invalid": base_relation(endpoints=[{"role": "subject", "ref": "x"}]),
    "psd_boundary_incomplete": base_relation(relation_type="probabilistic"),
    "decorative_probability": base_relation(relation_type="foo",
                                            extensions={"x_probability_value": 0.9}),
    "observation_intervention_conflated": base_relation(
        relation_type="intervention",
        extensions={"x_obs_distribution": {"p": 0.5}, "x_int_distribution": {"p": 0.5}}),
    "overclaim_upgrade_attempt": base_relation(relation_type="references",
                                               claim_ceiling="PRIMARY_VERIFIED"),
    "time_impossible_path": base_relation(
        relation_type="temporal",
        temporal_scope=full_temporal_scope("2026-07-25", "2026-07-24")),
    "psd_causal_escape_attempt": base_relation(
        relation_type="probabilistic",
        extensions={"x_psd": PSD, "x_causal_status": "established"}),
}


@pytest.mark.parametrize("code", list(TRIGGERS.keys()))
def test_each_reject_code_present_in_registry_and_emitted(code):
    eng = runtime.ARRRuntime()
    reg_codes = _registry_reject_codes(eng)
    assert code in reg_codes, f"{code} not in projection-routes.reject_codes"
    decision = eng._project(TRIGGERS[code])
    assert decision["reject_code"] == code, (
        f"expected {code}, got {decision['reject_code']}")
    assert decision["target"] == "REJECT"
    assert decision["reject_code"] in reg_codes


def test_projection_iterates_rules_by_priority_and_applies_guards():
    eng = runtime.ARRRuntime()
    # A valid adjacency relation must route to ARN (R12), not be rejected.
    d = eng._project(base_relation(relation_type="references"))
    assert d["rule_id"] == "R12"
    assert d["target"] == "ARN"
    assert d["reject_code"] is None
    # PSD with complete boundary routes to PSD_WITH_BOUNDARY (R3 + G_PSD ok).
    d2 = eng._project(base_relation(relation_type="probabilistic",
                                    extensions={"x_psd": PSD}))
    assert d2["rule_id"] == "R3"
    assert d2["target"] == "PSD_WITH_BOUNDARY"
    assert d2["reject_code"] is None
