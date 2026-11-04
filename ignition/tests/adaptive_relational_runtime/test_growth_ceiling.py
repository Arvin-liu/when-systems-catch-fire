"""PART C (c) + self-checks 2 & 3: the growth gate and the claim ceiling are
driven by the committed registries. Mutating a TEMP COPY of the registry
changes runtime behaviour (proving registry-driven, not hard-coded).

No license header: matches repo tests/ convention.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402

from tools.adaptive_relational_runtime import runtime  # noqa: E402


def _growth_status(eng):
    gs = eng._build_growth_signal("fb_" + "a" * 32, "obj_" + "b" * 32,
                                  "src_" + "c" * 32)
    return gs["status"], [it["gate_id"] for it in gs["gate_evaluation"]["items"]]


def test_growth_gate_registry_driven():
    eng = runtime.ARRRuntime()
    # Full registry: only G5g passes in the demo signal -> SIGNAL_ONLY.
    status_full, gates_full = _growth_status(eng)
    assert status_full == "SIGNAL_ONLY"
    assert "G1" in gates_full and "G6" in gates_full

    # Mutate a TEMP copy: keep only G5g. Now the single evaluated gate passes
    # -> EVOLVE_CANDIDATE. Behaviour changed because the gate SET is sourced
    # from the registry.
    eng.contract.registries["growth-signal-gates"] = copy.deepcopy(
        eng.contract.registries["growth-signal-gates"])
    eng.contract.registries["growth-signal-gates"]["gate_criteria"] = [
        g for g in eng.contract.registries["growth-signal-gates"]["gate_criteria"]
        if g["gate_id"] == "G5g"
    ]
    status_mut, gates_mut = _growth_status(eng)
    assert gates_mut == ["G5g"]
    assert status_mut == "EVOLVE_CANDIDATE"
    # The two runs disagree -> behaviour is registry-driven.
    assert status_full != status_mut


def test_ceiling_registry_driven():
    eng = runtime.ARRRuntime()
    # Baseline: source tier SECONDARY_DERIVED -> ceiling SECONDARY via registry.
    eng._max_ceiling = eng._max_ceiling_for_tier("SECONDARY_DERIVED")
    assert eng._max_ceiling == "SECONDARY"
    # A PRIMARY_VERIFIED claim exceeds the SECONDARY ceiling -> rejected.
    with pytest.raises(runtime.ContractValidationError):
        eng._assert_ceiling_within_tier({"claim_ceiling": "PRIMARY_VERIFIED"})

    # Mutate a TEMP copy of evidence-tiers so SECONDARY maps to PRIMARY_VERIFIED.
    eng.contract.registries["evidence-tiers"] = copy.deepcopy(
        eng.contract.registries["evidence-tiers"])
    for row in eng.contract.registries["evidence-tiers"]["tier_to_ceiling"]:
        if row["tier"] == "SECONDARY_ACADEMIC_INTERPRETATION":
            row["ceiling"] = "PRIMARY_VERIFIED"
    eng._max_ceiling = eng._max_ceiling_for_tier("SECONDARY_DERIVED")
    assert eng._max_ceiling == "PRIMARY_VERIFIED"
    # Now the same PRIMARY_VERIFIED claim is within the (raised) ceiling.
    eng._assert_ceiling_within_tier({"claim_ceiling": "PRIMARY_VERIFIED"})
