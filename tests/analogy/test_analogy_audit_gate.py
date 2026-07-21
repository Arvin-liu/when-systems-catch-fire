#!/usr/bin/env python3
"""Q37-I1 P1 gate tests — drive the REAL fail-closed validator CLI over the 10 core
classification & mapping-consistency fixtures (data/analogy/fixtures/01-10-*.json) and assert the
machine-readable exit code.

Every test invokes tools/analogy/validate_analogy_audit_gate.py via subprocess with the same
frozen exact head the fixtures are bound to. No constant assertions, no string-presence-only
checks: the asserted value is the validator's deterministic exit code. Mirrors
tests/intervention/test_intervention_failure_gate.py.

The full 24-fixture attack matrix (spec §六) is completed in P2 (T5); this file covers the
core classification & mapping-consistency spine (spec §五 / §六 items 1,2,3,5,6,7,21,22,23
plus the §五 claim-ceiling-overreach gate).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = ROOT / "tools" / "analogy" / "validate_analogy_audit_gate.py"
FX_DIR = ROOT / "data" / "analogy" / "fixtures"
CURRENT_HEAD = "e302459e721149cc5a42a4ae506b473a1cd92693"

# fixture number -> expected validator exit code (per spec §五 / §六 core items)
EXPECTED = {
    1: 0,   # STRUCTURAL_ANALOGY, full mapping, limited ceiling        -> PASS
    2: 9,   # SURFACE_SIMILARITY claims mechanism identity             -> MECHANISM_UPGRADE_FORBIDDEN
    3: 5,   # declared 1:1 but 2 source -> 1 target                   -> CARDINALITY_DIRECTION_MISMATCH
    4: 5,   # correspondence present but directionality 'none'        -> CARDINALITY_DIRECTION_MISMATCH
    5: 7,   # suspiciously clean mapping (no mismatch/omitted/hidden) -> NEGATIVE_EVIDENCE_SUPPRESSED
    6: 0,   # TRANSPORTABILITY_CANDIDATE, full transportability assess -> PASS
    7: 10,  # MECHANISM_CANDIDATE, all evidence INSUFFICIENT          -> MECHANISM_EVIDENCE_INSUFFICIENT
    8: 18,  # claim_ceiling asserts universal causal regularity       -> CLAIM_CEILING_OVERREACH
    9: 0,   # COUNTERANALOGY preserved, Q38 not allowed               -> PASS
    10: 0,  # MECHANISM_CANDIDATE downgraded to STRUCTURAL_ANALOGY    -> PASS (allowed downgrade)
}

EXIT_NAMES = {
    0: "GATE_PASS", 2: "SCHEMA_ERROR", 3: "DOMAIN_UNRESOLVABLE",
    4: "CORRESPONDENCE_REF_INVALID", 5: "CARDINALITY_DIRECTION_MISMATCH",
    6: "RELATION_PRESERVATION_OVERCLAIM", 7: "NEGATIVE_EVIDENCE_SUPPRESSED",
    8: "SHIFT_UNDECLARED", 9: "MECHANISM_UPGRADE_FORBIDDEN",
    10: "MECHANISM_EVIDENCE_INSUFFICIENT", 11: "RESIDUAL_AS_CAUSE",
    12: "TRANSPORTABILITY_INCOMPLETE", 13: "COUNTERANALOGY_SUPPRESSED",
    14: "Q14_CLAIM_NOT_COMMITTED", 15: "Q35_AUTHORITY_INVALID",
    16: "Q33_RIGHTS_BYPASS", 17: "UNRESOLVABLE_REF", 18: "CLAIM_CEILING_OVERREACH",
    19: "Q38_START_FORBIDDEN", 20: "NEGATIVE_AUDIT_DELETED", 21: "SEMANTIC_CONSISTENCY_MISMATCH",
}


def _fixtures():
    items = []
    for n in sorted(EXPECTED):
        matches = sorted(FX_DIR.glob(f"{n:02d}-*.json"))
        assert matches, f"fixture {n:02d} missing"
        items.append((n, matches[0]))
    return items


def _run(bundle_path):
    cmd = [sys.executable, str(VALIDATOR), "--bundle", str(bundle_path),
           "--current-head", CURRENT_HEAD]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_all_core_fixture_files_present():
    for n, _ in _fixtures():
        assert n in EXPECTED


def test_fixture_01_structural_analogy_passes():
    r = _run(_fixtures()[0][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_02_surface_similarity_mechanism_upgrade_fails():
    r = _run(_fixtures()[1][1])
    assert r.returncode == 9, r.stdout


def test_fixture_03_cardinality_mismatch_fails():
    r = _run(_fixtures()[2][1])
    assert r.returncode == 5, r.stdout


def test_fixture_04_directionality_none_fails():
    r = _run(_fixtures()[3][1])
    assert r.returncode == 5, r.stdout


def test_fixture_05_negative_evidence_suppressed_fails():
    r = _run(_fixtures()[4][1])
    assert r.returncode == 7, r.stdout


def test_fixture_06_transportability_candidate_passes():
    r = _run(_fixtures()[5][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_07_mechanism_evidence_insufficient_fails():
    r = _run(_fixtures()[6][1])
    assert r.returncode == 10, r.stdout


def test_fixture_08_claim_ceiling_overreach_fails():
    r = _run(_fixtures()[7][1])
    assert r.returncode == 18, r.stdout


def test_fixture_09_counteranalogy_preserved_passes():
    r = _run(_fixtures()[8][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_10_mechanism_downgrade_passes():
    r = _run(_fixtures()[9][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_core_fixture_matrix_exhaustive():
    """One parametrized assertion over the whole core matrix — guarantees no fixture drifts."""
    for n, path in _fixtures():
        r = _run(path)
        exp = EXPECTED[n]
        assert r.returncode == exp, (
            f"fixture {n:02d} {path.name}: expected exit {exp} ({EXIT_NAMES.get(exp)}), "
            f"got {r.returncode} ({EXIT_NAMES.get(r.returncode)})\n{r.stdout}"
        )
