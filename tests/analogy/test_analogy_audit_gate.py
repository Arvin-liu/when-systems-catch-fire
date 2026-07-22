#!/usr/bin/env python3
"""Q37-I1 gate tests — drive the REAL fail-closed validator CLI over the Q37 analogy-audit
fixture matrix (data/analogy/fixtures/01-30-*.json) and assert the machine-readable exit code.

Every test invokes tools/analogy/validate_analogy_audit_gate.py via subprocess with the same
frozen exact head the fixtures are bound to. No constant assertions, no string-presence-only
checks: the asserted value is the validator's deterministic exit code. Mirrors
tests/intervention/test_intervention_failure_gate.py.

The matrix covers spec §六 (1-24 enumerated attack/positive cases) plus the full set of 20
validator check families (25-30 add DOMAIN_UNRESOLVABLE, RELATION_PRESERVATION_OVERCLAIM,
COUNTERANALOGY_SUPPRESSED, Q38_START_FORBIDDEN, NEGATIVE_AUDIT_DELETED,
SEMANTIC_CONSISTENCY_MISMATCH). Transportability shift/invariance completeness is enforced at the
schema boundary (exit 2), so cases 9/10/15/16 (undeclared shift / incomplete transportability)
assert exit 2 — the gate still fails closed; TRANSPORTABILITY_INCOMPLETE (12) remains defense-in-depth.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VALIDATOR = ROOT / "tools" / "analogy" / "validate_analogy_audit_gate.py"
FX_DIR = ROOT / "data" / "analogy" / "fixtures"
CURRENT_HEAD = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
).strip()

# fixture number -> expected validator exit code
EXPECTED = {
    1: 0,   # STRUCTURAL_ANALOGY, full mapping, limited ceiling            -> PASS
    2: 9,   # SURFACE_SIMILARITY claims mechanism identity                 -> MECHANISM_UPGRADE_FORBIDDEN
    3: 5,   # declared 1:1 but 2 source -> 1 target                       -> CARDINALITY_DIRECTION_MISMATCH
    4: 5,   # correspondence present but directionality 'none'            -> CARDINALITY_DIRECTION_MISMATCH
    5: 7,   # suspiciously clean mapping (no mismatch/omitted/hidden)     -> NEGATIVE_EVIDENCE_SUPPRESSED
    6: 0,   # TRANSPORTABILITY_CANDIDATE, full transportability assess     -> PASS
    7: 10,  # MECHANISM_CANDIDATE, all evidence INSUFFICIENT              -> MECHANISM_EVIDENCE_INSUFFICIENT
    8: 18,  # claim_ceiling asserts universal causal regularity           -> CLAIM_CEILING_OVERREACH
    9: 0,   # COUNTERANALOGY preserved, Q38 not allowed                   -> PASS
    10: 0,  # MECHANISM_CANDIDATE downgraded to STRUCTURAL_ANALOGY        -> PASS (allowed downgrade)
    11: 4,  # correspondence target not in declared entities             -> CORRESPONDENCE_REF_INVALID
    12: 17, # stale / wrong exact_head                                    -> UNRESOLVABLE_REF
    13: 18, # Q36-INT repo intervention upgraded to universal mechanism   -> CLAIM_CEILING_OVERREACH
    14: 8,  # cross-domain mapping with undeclared scale/time diff        -> SHIFT_UNDECLARED
    15: 2,  # transportability missing concept/measurement shift         -> SCHEMA_ERROR (boundary)
    16: 2,  # transportability missing scale/time/regime shift            -> SCHEMA_ERROR (boundary)
    17: 10, # mechanism evidence circular self-reference                  -> MECHANISM_EVIDENCE_INSUFFICIENT
    18: 11, # Q36 residual written as shared-cause proof                  -> RESIDUAL_AS_CAUSE
    19: 2,  # transportability missing invariances/overlap/boundary       -> SCHEMA_ERROR (boundary)
    20: 2,  # transportability missing covariate shift                    -> SCHEMA_ERROR (boundary)
    21: 14, # Q34 claim not committed_current                             -> Q14_CLAIM_NOT_COMMITTED
    22: 15, # Q35 grant scope mismatch                                     -> Q35_AUTHORITY_INVALID
    23: 16, # Q33 rights gate bypassed (external material not clear)       -> Q33_RIGHTS_BYPASS
    24: 14, # real-repo pilot: Q34 ANALOGY_AS_MECHANISM replay            -> Q14_CLAIM_NOT_COMMITTED
    25: 3,  # mechanism evidence domain swapped (concept substitution)   -> DOMAIN_UNRESOLVABLE
    26: 6,  # relation-preservation overclaims beyond correspondence     -> RELATION_PRESERVATION_OVERCLAIM
    27: 13, # counteranalogy marked SUPPRESSED_DETECTED                   -> COUNTERANALOGY_SUPPRESSED
    28: 19, # Q38 case retrieval started before audit passes             -> Q38_START_FORBIDDEN
    29: 20, # counteranalogy candidate with no preserved audit decision  -> NEGATIVE_AUDIT_DELETED
    30: 21, # audit classification inconsistent (not allowed downgrade)  -> SEMANTIC_CONSISTENCY_MISMATCH
    32: 22, # fictional canonical source path                              -> CONTENT_BINDING_INVALID
    33: 23, # declared mapping digest does not bind canonical JSON         -> MAPPING_DIGEST_INVALID
    34: 22, # caller-invented authority grant                              -> CONTENT_BINDING_INVALID
    35: 22, # caller self-promotes candidate claim                         -> CONTENT_BINDING_INVALID
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
    22: "CONTENT_BINDING_INVALID", 23: "MAPPING_DIGEST_INVALID", 24: "CURRENT_HEAD_INVALID",
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


def test_all_fixture_files_present():
    for n, _ in _fixtures():
        assert n in EXPECTED


def test_fixture_matrix_exhaustive():
    """One parametrized assertion over the whole matrix — guarantees no fixture drifts."""
    for n, path in _fixtures():
        r = _run(path)
        exp = EXPECTED[n]
        assert r.returncode == exp, (
            f"fixture {n:02d} {path.name}: expected exit {exp} ({EXIT_NAMES.get(exp)}), "
            f"got {r.returncode} ({EXIT_NAMES.get(r.returncode)})\n{r.stdout}"
        )


# Representative individual tests (the exhaustive matrix above is authoritative; these
# document the canonical spec §六 spine plus the extra family-coverage fixtures).
def test_structural_analogy_passes():
    assert _run(_fixtures()[0][1]).returncode == 0

def test_surface_similarity_mechanism_upgrade_fails():
    assert _run(_fixtures()[1][1]).returncode == 9

def test_cardinality_direction_mismatch_fails():
    assert _run(_fixtures()[2][1]).returncode == 5

def test_transportability_candidate_passes():
    assert _run(_fixtures()[5][1]).returncode == 0

def test_counteranalogy_preserved_passes():
    assert _run(_fixtures()[8][1]).returncode == 0

def test_mechanism_downgrade_passes():
    assert _run(_fixtures()[9][1]).returncode == 0

def test_correspondence_dangling_ref_fails():
    assert _run(_fixtures()[10][1]).returncode == 4

def test_stale_exact_head_fails():
    assert _run(_fixtures()[11][1]).returncode == 17

def test_residual_as_common_cause_fails():
    assert _run(_fixtures()[17][1]).returncode == 11

def test_q14_claim_not_committed_fails():
    assert _run(_fixtures()[20][1]).returncode == 14

def test_q35_scope_mismatch_fails():
    assert _run(_fixtures()[21][1]).returncode == 15

def test_q33_rights_bypass_fails():
    assert _run(_fixtures()[22][1]).returncode == 16

def test_real_repo_pilot_q34_analogy_as_mechanism_fails():
    # honest repository replay of Q34's ANALOGY_AS_MECHANISM fixture (commitment_candidate,
    # not committed_current) -> Q37 correctly refuses to promote it (Q14 gate).
    assert _run(_fixtures()[23][1]).returncode == 14

def test_domain_construct_swap_fails():
    assert _run(_fixtures()[24][1]).returncode == 3

def test_relation_preservation_overclaim_fails():
    assert _run(_fixtures()[25][1]).returncode == 6

def test_counteranalogy_suppressed_fails():
    assert _run(_fixtures()[26][1]).returncode == 13

def test_q38_start_forbidden_fails():
    assert _run(_fixtures()[27][1]).returncode == 19

def test_negative_audit_deleted_fails():
    assert _run(_fixtures()[28][1]).returncode == 20

def test_semantic_consistency_mismatch_fails():
    assert _run(_fixtures()[29][1]).returncode == 21


def test_positive_pilot_is_bound_to_current_checkout():
    assert _run(ROOT / "data" / "analogy" / "pilot-real-repo-analogy-audit.json").returncode == 0


def test_wrong_cli_head_is_rejected_even_when_object_exists():
    cmd = [sys.executable, str(VALIDATOR), "--bundle", str(_fixtures()[0][1]),
           "--current-head", "e4ca5350a3c68e61031e3205eaca9f2665799a08"]
    assert subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).returncode == 24


def test_fictional_source_binding_fails():
    assert _run(next(FX_DIR.glob("32-*.json"))).returncode == 22


def test_mapping_digest_mismatch_fails():
    assert _run(next(FX_DIR.glob("33-*.json"))).returncode == 23


def test_fictional_grant_fails():
    assert _run(next(FX_DIR.glob("34-*.json"))).returncode == 22


def test_self_promoted_candidate_claim_fails():
    assert _run(next(FX_DIR.glob("35-*.json"))).returncode == 22
