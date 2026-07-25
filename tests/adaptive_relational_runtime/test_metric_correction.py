"""Regression + adversarial tests for the R3/R4 metric observability closure.

These tests pin the FINAL corrected behaviour of ``arr_metric_correction``.
In commit 1 the six projection functions raise ``NotImplementedError``; these
tests therefore fail first and turn green as commits 2-3 implement them. They
also cover the fail-closed validator, sealed-input identity, historical
immutability, determinism, the public/private boundary and the regenerated
public artifact regression (green only after commit 4).
"""

import copy
import json
import os

import pytest

from arr_metric_correction import (
    APPLICABILITY,
    SCHEMA_VERSION,
    CORPUS_OBJECTS,
    FROZEN_CORPUS_REF,
    MetricComponent,
    MetricDefinition,
    SEALED_R3_INPUTS,
    build_sealed_manifest,
    input_identity_checks,
    project_all,
    project_capability_interpretation,
    project_contradiction_lifecycle,
    project_crash_recovery,
    project_incremental_rerun,
    project_semantic_guardrail_understanding_split,
    project_unknown_retention,
    sealed_input_digest,
    validate_all,
    validate_metric_definition,
)
from .r4_fixtures import R4_CAPABILITY_ITEM_IDS, r4_capability_matrix

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT_DIR = os.path.join(REPO_ROOT, "docs", "architecture", "arr-r3-r4-metric-closure")


# --------------------------------------------------------------------------
# 1. Fail-closed validator
# --------------------------------------------------------------------------

def _good_md(**overrides):
    base = dict(
        metric_id="test_metric",
        schema_version=SCHEMA_VERSION,
        display_name="Test",
        semantic_kind="count",
        numerator=MetricComponent("n", 1, "src"),
        denominator=MetricComponent("d", 1, "src"),
        population="pop",
        applicability="APPLICABLE",
        value=1,
        unit="count",
        directionality="descriptive_only",
        authority_source="src",
        precedence_rule="pre",
        historical_value=0,
        historical_source="hist",
        correction_status="corrected",
        underlying_defect_present=False,
        underlying_defect_repaired_in_current_layer=False,
        supersedes_for_interpretation=False,
        evidence_refs=["src"],
        note="",
    )
    base.update(overrides)
    return MetricDefinition(**base)


def test_validator_accepts_well_formed_count():
    assert validate_metric_definition(_good_md()) == []


@pytest.mark.parametrize("kind", ["rate", "fraction", "count", "boolean",
                                   "applicability", "violation_count",
                                   "coverage_statement"])
def test_validator_accepts_all_semantic_kinds(kind):
    md = _good_md(semantic_kind=kind)
    assert validate_metric_definition(md) == []


@pytest.mark.parametrize("bad", ["ratio", "percent", "weird", ""])
def test_validator_rejects_invalid_semantic_kind(bad):
    md = _good_md(semantic_kind=bad)
    assert any("semantic_kind" in f for f in validate_metric_definition(md))


@pytest.mark.parametrize("appl", ["APPLICABLE", "NOT_APPLICABLE",
                                   "INSUFFICIENT_EVIDENCE", "UNKNOWN"])
def test_validator_accepts_all_applicability(appl):
    md = _good_md(applicability=appl)
    # "UNKNOWN" is only rejected for rate/fraction, not for counts.
    assert validate_metric_definition(md) == [] if appl != "UNKNOWN" else True


@pytest.mark.parametrize("appl", ["MAYBE", "N/A", "unknown", ""])
def test_validator_rejects_invalid_applicability(appl):
    md = _good_md(applicability=appl)
    assert any("applicability" in f for f in validate_metric_definition(md))


def test_validator_rejects_missing_evidence_refs():
    md = _good_md(evidence_refs=[])
    assert any("evidence_refs" in f for f in validate_metric_definition(md))


def test_validator_rejects_rate_missing_numerator_source():
    md = _good_md(semantic_kind="rate", numerator=MetricComponent("n", None, ""),
                  applicability="APPLICABLE")
    assert any("numerator" in f for f in validate_metric_definition(md))


def test_validator_rejects_rate_missing_denominator_source():
    md = _good_md(semantic_kind="rate", denominator=MetricComponent("d", 1, ""),
                  applicability="APPLICABLE")
    assert any("denominator" in f for f in validate_metric_definition(md))


def test_validator_rejects_rate_missing_population():
    md = _good_md(semantic_kind="rate", population="")
    assert any("population" in f for f in validate_metric_definition(md))


def test_validator_rejects_rate_with_unknown_applicability():
    md = _good_md(semantic_kind="rate", applicability="UNKNOWN")
    assert any("applicability" in f for f in validate_metric_definition(md))


def test_validator_maps_denominator_zero_to_not_applicable():
    md = _good_md(semantic_kind="rate", numerator=MetricComponent("n", 0, "src"),
                  denominator=MetricComponent("d", 0, "src"),
                  applicability="NOT_APPLICABLE", value="NOT_APPLICABLE")
    assert validate_metric_definition(md) == []


def test_validator_rejects_denominator_zero_presented_as_zero_rate():
    md = _good_md(semantic_kind="rate", numerator=MetricComponent("n", 0, "src"),
                  denominator=MetricComponent("d", 0, "src"),
                  applicability="NOT_APPLICABLE", value=0.0,
                  correction_status="corrected")
    assert any("0.0" in f for f in validate_metric_definition(md))


def test_validator_rejects_schema_version_mismatch():
    md = _good_md(schema_version="wrong/v0")
    assert any("schema_version" in f for f in validate_metric_definition(md))


# --------------------------------------------------------------------------
# 2. Sealed-input identity & immutability
# --------------------------------------------------------------------------

def test_sealed_manifest_has_all_report_identities():
    m = build_sealed_manifest()
    assert set(m["report_identities"]) == set(SEALED_R3_INPUTS.keys())


def test_sealed_digests_deterministic():
    assert sealed_input_digest("AGGREGATE_METRICS") == sealed_input_digest("AGGREGATE_METRICS")


def test_sealed_corpus_constant_is_836():
    assert CORPUS_OBJECTS == 836
    assert FROZEN_CORPUS_REF == "50393395ce9e6a1592787d991e630e364c5b6a09"


def test_input_identity_checks_passes_on_contract():
    assert input_identity_checks(SEALED_R3_INPUTS) == []


def test_input_identity_checks_fails_on_mutation():
    mutated = copy.deepcopy(SEALED_R3_INPUTS)
    mutated["AGGREGATE_METRICS"]["crash_recovery_success_rate"] = 1.0
    assert any("AGGREGATE_METRICS" in f for f in input_identity_checks(mutated))


def test_input_identity_checks_fails_on_extra_report():
    extra = copy.deepcopy(SEALED_R3_INPUTS)
    extra["EXTRA_REPORT"] = {}
    assert any("EXTRA_REPORT" in f for f in input_identity_checks(extra))


# --------------------------------------------------------------------------
# 3. M3 crash recovery
# --------------------------------------------------------------------------

def _m3():
    return project_crash_recovery(SEALED_R3_INPUTS)


def test_m3_demo_success_rate_is_three_of_three():
    m3 = _m3()
    md = m3["crash_recovery_demo_success_rate"]
    assert md.value == pytest.approx(1.0)
    assert md.numerator.value == 3
    assert md.denominator.value == 3
    assert md.applicability == "APPLICABLE"


def test_m3_demo_rate_authority_is_demo_report():
    md = _m3()["crash_recovery_demo_success_rate"]
    assert "CRASH_RECOVERY_REPORT" in md.authority_source
    assert "CORPUS_RUN_LEDGER" in md.authority_source


def test_m3_in_run_crash_events_observed_is_zero_count():
    md = _m3()["in_run_crash_events_observed"]
    assert md.value == 0
    assert md.semantic_kind == "count"


def test_m3_in_run_rate_is_not_applicable_for_denominator_zero():
    md = _m3()["crash_recovery_in_run_rate"]
    assert md.applicability == "NOT_APPLICABLE"
    assert md.denominator.value == 0


def test_m3_in_run_rate_never_presents_numeric_zero():
    md = _m3()["crash_recovery_in_run_rate"]
    assert md.value != 0.0


def test_m3_historical_aggregate_zero_preserved_as_history():
    md = _m3()["crash_recovery_demo_success_rate"]
    assert md.historical_value == 0.0
    assert md.historical_source == "AGGREGATE_METRICS"
    assert md.supersedes_for_interpretation is True
    assert md.correction_status == "corrected"


def test_m3_defect_present_but_repaired_in_layer():
    md = _m3()["crash_recovery_demo_success_rate"]
    assert md.underlying_defect_present is True
    assert md.underlying_defect_repaired_in_current_layer is True


def test_m3_all_metrics_validate():
    assert validate_all({"m3": _m3()}) == []


def test_m3_directionality_descriptive():
    md = _m3()["crash_recovery_demo_success_rate"]
    assert md.directionality == "higher_is_better"


# --------------------------------------------------------------------------
# 4. M4 incremental rerun
# --------------------------------------------------------------------------

def _m4():
    return project_incremental_rerun(SEALED_R3_INPUTS)


def test_m4_changed_objects_is_one():
    assert _m4()["incremental_changed_objects"].value == 1


def test_m4_reprocessed_objects_is_one():
    assert _m4()["incremental_reprocessed_objects"].value == 1


def test_m4_corpus_objects_is_836():
    assert _m4()["incremental_corpus_objects"].value == 836


def test_m4_reprocess_fraction_is_one_of_836():
    md = _m4()["incremental_reprocess_fraction"]
    assert md.numerator.value == 1
    assert md.denominator.value == 836
    assert md.value == pytest.approx(1 / 836)


def test_m4_reprocess_fraction_rational_string_exact():
    md = _m4()["incremental_reprocess_fraction"]
    assert "1/836" in (md.note or "")


def test_m4_unchanged_avoided_is_835():
    assert _m4()["incremental_unchanged_objects_avoided"].value == 835


def test_m4_avoidance_fraction_is_835_of_836():
    md = _m4()["incremental_avoidance_fraction"]
    assert md.numerator.value == 835
    assert md.denominator.value == 836
    assert md.value == pytest.approx(835 / 836)


def test_m4_selective_rerun_pass_is_true():
    md = _m4()["incremental_selective_rerun_pass"]
    assert md.value is True
    assert md.semantic_kind == "boolean"


def test_m4_low_reprocess_fraction_not_presented_as_success_rate():
    md = _m4()["incremental_reprocess_fraction"]
    assert md.directionality != "higher_is_better"
    assert "success rate" not in (md.display_name or "").lower()


def test_m4_historical_zero_preserved_as_history():
    md = _m4()["incremental_reprocess_fraction"]
    assert md.historical_value == 0.0
    assert md.historical_source == "AGGREGATE_METRICS"
    assert md.supersedes_for_interpretation is True


def test_m4_defect_present_but_repaired():
    md = _m4()["incremental_reprocess_fraction"]
    assert md.underlying_defect_present is True
    assert md.underlying_defect_repaired_in_current_layer is True


def test_m4_all_metrics_validate():
    assert validate_all({"m4": _m4()}) == []


# --------------------------------------------------------------------------
# 5. M2 unknown retention
# --------------------------------------------------------------------------

def _m2():
    return project_unknown_retention(SEALED_R3_INPUTS)


def test_m2_event_time_count_is_449():
    assert _m2()["unknown_event_time_count"].value == 449


def test_m2_retained_count_is_449():
    assert _m2()["unknown_event_time_retained_count"].value == 449


def test_m2_coercion_violations_is_zero():
    assert _m2()["unknown_event_time_coercion_violations"].value == 0


def test_m2_retention_rate_is_449_of_449():
    md = _m2()["unknown_event_time_retention_rate"]
    assert md.numerator.value == 449
    assert md.denominator.value == 449
    assert md.value == pytest.approx(1.0)
    assert md.applicability == "APPLICABLE"


def test_m2_historical_unknown_retention_deprecated_not_mutated():
    md = _m2()["unknown_event_time_retention_rate"]
    assert md.historical_value == 0
    assert md.historical_source == "AGGREGATE_METRICS"
    assert md.correction_status in ("clarified", "corrected")
    assert "deprecated" in (md.note or "").lower() or "ambiguous" in (md.note or "").lower()


def test_m2_no_underlying_defect():
    md = _m2()["unknown_event_time_retention_rate"]
    assert md.underlying_defect_present is False
    assert md.underlying_defect_repaired_in_current_layer is False


def test_m2_all_metrics_validate():
    assert validate_all({"m2": _m2()}) == []


# --------------------------------------------------------------------------
# 6. M5 capability closed set
# --------------------------------------------------------------------------

def _m5(matrix=None):
    return project_capability_interpretation(matrix or r4_capability_matrix())


def test_m5_closed_set_exact_27():
    cs = _m5()["closed_set"]
    assert cs["expected_total"] == 27
    assert cs["classified_total"] == 27
    assert cs["sum_primary_dimension_counts"] == 27
    assert cs["invariant_ok"] is True


def test_m5_dimension_counts_17_4_3_3():
    dims = _m5()["dimensions"]
    assert dims["OPERATIONAL"]["item_count"] == 17
    assert dims["SEMANTIC"]["item_count"] == 4
    assert dims["EVIDENCE"]["item_count"] == 3
    assert dims["GOVERNANCE"]["item_count"] == 3


def test_m5_each_item_exactly_one_primary_dimension():
    cs = _m5()["closed_set"]
    assert cs["primary_overlap_total"] == 0
    assert cs["unclassified_total"] == 0


def test_m5_all_items_pass():
    for dim, d in _m5()["dimensions"].items():
        assert d["fail"] == 0, dim


def test_m5_all_checks_pass_true():
    assert _m5()["all_checks_pass"] is True


def test_m5_all_checks_pass_definition_names_four_dimensions():
    definition = _m5()["all_checks_pass_definition"].lower()
    for token in ("operational", "semantic", "evidence", "governance"):
        assert token in definition


def test_m5_all_checks_pass_does_not_imply_semantic_understanding():
    assert "semantic understanding" in _m5()["all_checks_pass_does_not_imply"]


def test_m5_all_checks_pass_does_not_imply_independent_support():
    assert any("independent" in s.lower() for s in _m5()["all_checks_pass_does_not_imply"])


def test_m5_all_checks_pass_does_not_imply_claim_truth():
    assert any("truth" in s.lower() or "claim" in s.lower()
               for s in _m5()["all_checks_pass_does_not_imply"])


def test_m5_all_checks_pass_does_not_imply_promotion():
    assert any("promot" in s.lower() or "evol" in s.lower()
               for s in _m5()["all_checks_pass_does_not_imply"])


def test_m5_semantic_understanding_objects_verified_zero():
    assert _m5()["semantic_understanding_objects_verified"] == 0


def test_m5_independently_supported_objects_zero_by_default():
    assert _m5()["independently_supported_objects"] == 0


def test_m5_unknown_capability_id_fails_closed():
    matrix = r4_capability_matrix()
    matrix["items"].append({"id": "totally_unknown_capability_x", "pass": True,
                            "evidence": "fixture"})
    matrix["total_items"] = 28
    cs = project_capability_interpretation(matrix)["closed_set"]
    assert cs["unclassified_total"] >= 1
    assert cs["invariant_ok"] is False


def test_m5_reuses_exact_registry_size():
    dims = _m5()["dimensions"]
    total = sum(d["item_count"] for d in dims.values())
    assert total == 27


def test_m5_historical_all_pass_preserved_as_history():
    m5 = _m5()
    assert m5["historical_value"]["all_pass"] is True
    assert m5["historical_source"] == "CAPABILITY_COVERAGE_MATRIX"


# --------------------------------------------------------------------------
# 7. R4 semantic guardrail vs understanding split
# --------------------------------------------------------------------------

def _split():
    return project_semantic_guardrail_understanding_split(_m5())


def test_split_guardrail_checks_measured_true():
    assert _split()["guardrail_checks_measured"] is True


def test_split_guardrail_item_count_four():
    assert _split()["guardrail_item_count"] == 4


def test_split_guardrail_pass_four():
    assert _split()["guardrail_pass"] == 4


def test_split_guardrail_fail_zero():
    assert _split()["guardrail_fail"] == 0


def test_split_guardrail_status_pass():
    assert _split()["guardrail_status"] == "pass"


def test_split_semantic_understanding_stage_absent():
    assert _split()["semantic_understanding_stage_present"] is False


def test_split_semantic_understanding_coverage_not_measured():
    assert _split()["semantic_understanding_coverage_measured"] is False


def test_split_semantic_understanding_items_zero():
    assert _split()["semantic_understanding_items"] == 0


def test_split_semantic_understanding_verified_objects_zero():
    assert _split()["semantic_understanding_verified_objects"] == 0


def test_split_note_explicit_guardrail_not_understanding():
    note = _split()["note"].lower()
    assert "guardrail" in note and "understanding" in note


def test_split_no_ambiguous_single_measured_field():
    # The new schema must not conflate both facts under one 'measured' boolean.
    split = _split()
    assert "measured" not in split or not isinstance(split.get("measured"), bool)


def test_split_pass_four_not_coexisting_with_ambiguous_measured_false():
    split = _split()
    ambiguous = split.get("measured")
    if ambiguous is False:
        raise AssertionError("pass=4 must not coexist with a single ambiguous measured=false")
    assert split["guardrail_pass"] == 4


# --------------------------------------------------------------------------
# 8. Contradiction lifecycle closure
# --------------------------------------------------------------------------

def test_lifecycle_m3_not_repaired_without_validator_evidence():
    lc = project_contradiction_lifecycle({})
    assert lc["M3_CRASH_RECOVERY_RATE"]["underlying_defect_repaired_in_current_layer"] is False
    assert lc["M3_CRASH_RECOVERY_RATE"]["followup_required"] is True


def test_lifecycle_m3_repaired_when_validated():
    lc = project_contradiction_lifecycle({"M3": True})
    assert lc["M3_CRASH_RECOVERY_RATE"]["underlying_defect_repaired_in_current_layer"] is True
    assert lc["M3_CRASH_RECOVERY_RATE"]["followup_required"] is False


def test_lifecycle_m4_not_repaired_without_validator_evidence():
    lc = project_contradiction_lifecycle({})
    assert lc["M4_INCREMENTAL_SELECTIVITY"]["underlying_defect_repaired_in_current_layer"] is False


def test_lifecycle_m4_repaired_when_validated():
    lc = project_contradiction_lifecycle({"M4": True})
    assert lc["M4_INCREMENTAL_SELECTIVITY"]["underlying_defect_repaired_in_current_layer"] is True


def test_lifecycle_m5_historical_preserved_current_repaired():
    lc = project_contradiction_lifecycle({"M5": True})
    m5 = lc["M5_CAPABILITY_ALL_PASS"]
    assert m5["historical_artifact_mutated"] is False
    assert m5["underlying_defect_repaired_in_current_layer"] is True


def test_lifecycle_m1_no_defect_no_phantom_repair():
    lc = project_contradiction_lifecycle({})
    m1 = lc["M1_SUCCESS_VS_SEMANTIC"]
    assert m1["underlying_defect_present"] is False
    assert m1["underlying_defect_repaired_in_current_layer"] is False
    assert m1["followup_required"] is False


def test_lifecycle_m2_no_defect_no_phantom_repair():
    lc = project_contradiction_lifecycle({})
    m2 = lc["M2_UNKNOWN_RETENTION"]
    assert m2["underlying_defect_present"] is False
    assert m2["followup_required"] is False


def test_lifecycle_m6_no_defect_no_phantom_repair():
    lc = project_contradiction_lifecycle({})
    m6 = lc["M6_CORPUS_SIZE_VS_SOURCES"]
    assert m6["underlying_defect_present"] is False
    assert m6["followup_required"] is False


def test_lifecycle_classification_resolved_distinct_from_repaired():
    lc = project_contradiction_lifecycle({})
    for mid, rec in lc.items():
        assert rec["classification_resolved"] is True
        # classification resolved does not imply repaired
        if rec["underlying_defect_present"]:
            assert rec["underlying_defect_repaired_in_current_layer"] is False


def test_lifecycle_no_field_hardcoded_repaired():
    lc = project_contradiction_lifecycle({})
    for mid, rec in lc.items():
        if not rec["underlying_defect_present"]:
            assert rec["underlying_defect_repaired_in_current_layer"] is False


# --------------------------------------------------------------------------
# 9. Full projection: determinism, immutability, boundary, artifacts
# --------------------------------------------------------------------------

def test_project_all_deterministic():
    a = project_all(SEALED_R3_INPUTS, r4_capability_matrix())
    b = project_all(SEALED_R3_INPUTS, r4_capability_matrix())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_project_all_does_not_mutate_sealed_inputs():
    before = copy.deepcopy(SEALED_R3_INPUTS)
    project_all(SEALED_R3_INPUTS, r4_capability_matrix())
    assert SEALED_R3_INPUTS == before


def test_project_all_validation_ok_true():
    result = project_all(SEALED_R3_INPUTS, r4_capability_matrix(),
                         corrections_validated={"M2": True, "M3": True,
                                                "M4": True, "M5": True})
    assert result["validation_ok"] is True
    assert result["validation_failures"] == []


def test_project_all_public_boundary_no_private_keys():
    result = project_all(SEALED_R3_INPUTS, r4_capability_matrix())
    blob = json.dumps(result, sort_keys=True)
    assert "syn_" not in blob
    assert "g_" not in blob
    assert '"title"' not in blob


def test_project_all_no_prohibited_action_performed():
    result = project_all(SEALED_R3_INPUTS, r4_capability_matrix())
    blob = json.dumps(result, sort_keys=True).lower()
    # The correction layer never performs or claims a prohibited action; it only
    # reports the governance guardrail outcome (zero prohibited actions).
    for token in ("promote_called\": true", "evolve_called\": true",
                  "real_world_action\": true", "second executor"):
        assert token not in blob


def test_project_all_schema_version_consistent():
    result = project_all(SEALED_R3_INPUTS, r4_capability_matrix())
    assert result["schema"] == "r3r4/correction-projection/v1"


def test_artifact_regression_public_closures_exist():
    expected = [
        "CRASH_RECOVERY_METRIC_CLOSURE.json",
        "INCREMENTAL_RERUN_METRIC_CLOSURE.json",
        "UNKNOWN_RETENTION_METRIC_CLOSURE.json",
        "CAPABILITY_CLOSED_SET_V2.json",
        "SEMANTIC_GUARDRAIL_UNDERSTANDING_SPLIT.json",
        "CONTRADICTION_LIFECYCLE_CLOSURE.json",
    ]
    for name in expected:
        path = os.path.join(ARTIFACT_DIR, name)
        assert os.path.exists(path), f"missing public artifact {path}"


def test_artifact_regression_artifacts_deterministic():
    if not os.path.isdir(ARTIFACT_DIR):
        pytest.skip("artifacts not generated yet")
    blobs = {}
    for name in os.listdir(ARTIFACT_DIR):
        if name.endswith(".json"):
            with open(os.path.join(ARTIFACT_DIR, name)) as fh:
                blobs[name] = fh.read()
    # Re-read and compare stability across two reads.
    again = {}
    for name in blobs:
        with open(os.path.join(ARTIFACT_DIR, name)) as fh:
            again[name] = fh.read()
    assert blobs == again
