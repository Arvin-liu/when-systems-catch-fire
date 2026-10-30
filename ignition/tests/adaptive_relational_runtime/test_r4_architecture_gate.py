"""Architecture-candidate gate mutation tests (R4 task §7, §10).

The gate MUST reject a would-be candidate when ANY of the eight conditions is
removed or falsified. These tests are the proof: each condition is mutated in
isolation and the gate must flip to NO_EVOLVE. This is the core guarantee that
R4 cannot accidentally promote a lower-level defect to an architecture candidate.
"""

import pytest

from arr_r4_self_reflection.arch_gate import ArchitectureCandidateGate, decide
from arr_r4_self_reflection.schemas import ArchitectureCandidate
from arr_r4_self_reflection.taxonomy import (
    ARCH_CANDIDATE_DISPOSITION,
    ARCH_GATE_CONDITIONS,
    DEFAULT_ARCH_DISPOSITION,
)

ALL_TRUE = {c: True for c in ARCH_GATE_CONDITIONS}


def test_all_conditions_true_passes():
    disp, failed = decide(ALL_TRUE)
    assert disp == ARCH_CANDIDATE_DISPOSITION
    assert failed == []


@pytest.mark.parametrize("cond", ARCH_GATE_CONDITIONS)
def test_mutate_single_condition_false_fails(cond):
    conds = dict(ALL_TRUE)
    conds[cond] = False
    disp, failed = decide(conds)
    assert disp == DEFAULT_ARCH_DISPOSITION
    assert cond in failed


@pytest.mark.parametrize("cond", ARCH_GATE_CONDITIONS)
def test_mutate_single_condition_missing_fails(cond):
    conds = dict(ALL_TRUE)
    del conds[cond]
    disp, failed = decide(conds)
    assert disp == DEFAULT_ARCH_DISPOSITION
    assert cond in failed


def test_two_conditions_false_still_fails():
    conds = dict(ALL_TRUE)
    conds["primitives_cannot_represent"] = False
    conds["lower_cost_adapter_insufficient"] = False
    disp, failed = decide(conds)
    assert disp == DEFAULT_ARCH_DISPOSITION
    assert len(failed) == 2


def test_gate_sets_disposition_on_candidate_object():
    cand = ArchitectureCandidate(
        candidate_id="X", observation="gap", conditions=dict(ALL_TRUE),
        disposition="NO_EVOLVE", failed_conditions=[], evidence_refs=[])
    ArchitectureCandidateGate().evaluate(cand)
    assert cand.disposition == ARCH_CANDIDATE_DISPOSITION
    assert cand.failed_conditions == []


def test_gate_rejects_single_case_defect():
    # A single-case observation cannot satisfy cross_source_or_class_breadth.
    conds = dict(ALL_TRUE)
    conds["cross_source_or_class_breadth"] = False
    cand = ArchitectureCandidate(
        candidate_id="Y", observation="single case", conditions=conds,
        disposition="NO_EOLVE", failed_conditions=[], evidence_refs=[])
    ArchitectureCandidateGate().evaluate(cand)
    assert cand.disposition == DEFAULT_ARCH_DISPOSITION
    assert "cross_source_or_class_breadth" in cand.failed_conditions


def test_gate_rejects_lower_level_defect():
    # A metric-definition bug is explained by a lower-level class.
    conds = dict(ALL_TRUE)
    conds["not_explained_by_lower_level"] = False
    disp, failed = decide(conds)
    assert disp == DEFAULT_ARCH_DISPOSITION
    assert "not_explained_by_lower_level" in failed
