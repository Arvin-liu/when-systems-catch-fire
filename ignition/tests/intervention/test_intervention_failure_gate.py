#!/usr/bin/env python3
"""Q36-INT P2 gate tests — drive the REAL fail-closed validator CLI over the 23 attack/positive
fixtures (data/intervention/fixtures/01-23-*.json) and assert the machine-readable exit code.

Every test invokes tools/intervention/validate_intervention_failure_gate.py via subprocess with the
same supporting inputs the production bundle would carry (Q34 claims registry, Q33 rejected-sources
registry, frozen OBS exact head, reference 'now'). No constant assertions, no string-presence-only
checks: the asserted value is the validator's deterministic exit code. Mirrors
tests/intervention/test_intervention_failure_core.py.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = ROOT / "tools" / "intervention" / "validate_intervention_failure_gate.py"
CLAIMS = ROOT / "data" / "agent" / "q34-claims-registry.json"
REJECTS = ROOT / "data" / "agent" / "q33-publication-rejects.json"
FX_DIR = ROOT / "data" / "intervention" / "fixtures"
CURRENT_HEAD = "9087e494c782b405b5bbdb0d1ae4bd1707792d95"
NOW = "2026-07-21T12:00:00+00:00"

# fixture number -> expected validator exit code (per instruction §六)
EXPECTED = {
    1: 0, 2: 6, 3: 7, 4: 15, 5: 18, 6: 4, 7: 9, 8: 9, 9: 9, 10: 11, 11: 12, 12: 19, 13: 10,
    14: 14, 15: 13, 16: 16, 17: 16, 18: 15, 19: 8, 20: 17, 21: 0, 22: 0, 23: 0,
}

# lookup table: exit_code -> human exit name (for readable failures)
EXIT_NAMES = {
    0: "GATE_PASS", 2: "SCHEMA_ERROR", 3: "TEMPORAL_LEAK", 4: "TARGET_MISMATCH",
    5: "UNRESOLVABLE_REF", 6: "Q14_CLAIM_NOT_COMMITTED", 7: "Q35_AUTHORITY_INVALID",
    8: "Q33_GATE_BYPASS", 9: "SAFETY_ENVELOPE_INCOMPLETE", 10: "EXTERNAL_ACTION_FORBIDDEN",
    11: "ENVELOPE_EXCEEDED", 12: "STOP_CONDITION_VIOLATED", 13: "FAILURE_REWRITE_FORBIDDEN",
    14: "EXPECTED_EFFECT_REWRITE", 15: "CAUSAL_OVERCLAIM", 16: "ROLLBACK_INCOMPLETE",
    17: "SINGLE_OWNER_FORGED", 18: "OBS_NOT_VALIDATED", 19: "SEPARATION_OF_DUTY_VIOLATION",
    20: "BASELINE_MISSING", 21: "PLACEHOLDER_DIGEST", 22: "CONTENT_BINDING_INVALID",
    23: "CANONICAL_AUTHORITY_INVALID",
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
           "--claims", str(CLAIMS), "--q33-rejects", str(REJECTS),
           "--current-head", CURRENT_HEAD, "--now", NOW]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_all_fixture_files_present():
    for n, _ in _fixtures():
        assert n in EXPECTED


def test_fixture_01_legal_controlled_dry_run_passes():
    r = _run(_fixtures()[0][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_02_uncommitted_q34_claim_fails():
    r = _run(_fixtures()[1][1])
    assert r.returncode == 6, r.stdout


def test_fixture_03_expired_q35_grant_fails():
    r = _run(_fixtures()[2][1])
    assert r.returncode == 7, r.stdout


def test_fixture_04_residual_as_causation_fails():
    r = _run(_fixtures()[3][1])
    assert r.returncode == 15, r.stdout


def test_fixture_05_obs_not_validated_fails():
    r = _run(_fixtures()[4][1])
    assert r.returncode == 18, r.stdout


def test_fixture_06_target_scope_mismatch_fails():
    r = _run(_fixtures()[5][1])
    assert r.returncode == 4, r.stdout


def test_fixture_07_missing_safety_envelope_fails():
    r = _run(_fixtures()[6][1])
    assert r.returncode == 9, r.stdout


def test_fixture_08_missing_stop_conditions_fails():
    r = _run(_fixtures()[7][1])
    assert r.returncode == 9, r.stdout


def test_fixture_09_missing_rollback_plan_fails():
    r = _run(_fixtures()[8][1])
    assert r.returncode == 9, r.stdout


def test_fixture_10_envelope_exceeded_fails():
    r = _run(_fixtures()[9][1])
    assert r.returncode == 11, r.stdout


def test_fixture_11_continue_after_stop_fails():
    r = _run(_fixtures()[10][1])
    assert r.returncode == 12, r.stdout


def test_fixture_12_self_all_roles_high_risk_fails():
    r = _run(_fixtures()[11][1])
    assert r.returncode == 19, r.stdout


def test_fixture_13_external_action_real_world_fails():
    r = _run(_fixtures()[12][1])
    assert r.returncode == 10, r.stdout


def test_fixture_14_expected_effect_rewrite_fails():
    r = _run(_fixtures()[13][1])
    assert r.returncode == 14, r.stdout


def test_fixture_15_failure_deleted_only_success_fails():
    r = _run(_fixtures()[14][1])
    assert r.returncode == 13, r.stdout


def test_fixture_16_rollback_silent_overwrite_fails():
    r = _run(_fixtures()[15][1])
    assert r.returncode == 16, r.stdout


def test_fixture_17_rollback_partial_claimed_full_fails():
    r = _run(_fixtures()[16][1])
    assert r.returncode == 16, r.stdout


def test_fixture_18_universal_capability_overclaim_fails():
    r = _run(_fixtures()[17][1])
    assert r.returncode == 15, r.stdout


def test_fixture_19_q33_rights_bypass_fails():
    r = _run(_fixtures()[18][1])
    assert r.returncode == 8, r.stdout


def test_fixture_20_single_owner_forged_fails():
    r = _run(_fixtures()[19][1])
    assert r.returncode == 17, r.stdout


def test_fixture_21_negative_result_preserved_passes():
    r = _run(_fixtures()[20][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_22_legal_abort_abandon_passes():
    r = _run(_fixtures()[21][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_23_controlled_pilot_replay_passes():
    r = _run(_fixtures()[22][1])
    assert r.returncode == 0, r.stdout + r.stderr


def test_fixture_matrix_exhaustive():
    """One parametrized assertion over the whole §六 matrix — guarantees no fixture drifts."""
    for n, path in _fixtures():
        r = _run(path)
        exp = EXPECTED[n]
        assert r.returncode == exp, (
            f"fixture {n:02d} {path.name}: expected exit {exp} ({EXIT_NAMES.get(exp)}), "
            f"got {r.returncode} ({EXIT_NAMES.get(r.returncode)})\n{r.stdout}"
        )


def test_fixture_24_original_placeholder_authority_bypass_fails():
    r = _run(FX_DIR / "24-placeholder-digests-self-declared-authority.json")
    assert r.returncode == 21, r.stdout


def test_fixture_25_actual_byte_digest_mismatch_fails():
    r = _run(FX_DIR / "25-q36-source-digest-mismatch.json")
    assert r.returncode == 22, r.stdout


def test_fixture_26_wrong_exact_git_head_fails():
    r = _run(FX_DIR / "26-q35-source-wrong-exact-head.json")
    assert r.returncode == 22, r.stdout


def test_fixture_27_repository_path_traversal_fails():
    r = _run(FX_DIR / "27-source-path-traversal.json")
    assert r.returncode == 22, r.stdout


def test_fixture_28_embedded_unresolvable_grant_fails():
    r = _run(FX_DIR / "28-embedded-unresolvable-grant.json")
    assert r.returncode == 22, r.stdout
