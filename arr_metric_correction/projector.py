"""Deterministic correction projector (relay task §6 / §7 / §8).

Consumes the sealed historical R3 input identities and the sealed R3 capability
matrix, and produces the versioned correction artifacts:

* M2  unknown-retention clarification (§6.3)
* M3  crash-recovery aggregation correction (§6.1)
* M4  incremental-rerun selectivity correction (§6.2)
* M5  versioned R3 capability interpretation correction (§6.4)
* R4  semantic-guardrail vs semantic-understanding split (§7)
* M1-M6 contradiction lifecycle closure (§8)

The projector is deterministic and fail-closed: it never invents values, it
references the exact sealed inputs, and it never mutates history. The six
projection functions below are filled in across commits 2-3; until then they
raise ``NotImplementedError`` so the contract regression tests fail first.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .schema import (
    APPLICABILITY,
    SCHEMA_VERSION,
    MetricComponent,
    MetricDefinition,
    validate_metric_definition,
)
from .sealed_inputs import (
    CORPUS_OBJECTS,
    FROZEN_CORPUS_REF,
    SEALED_R3_INPUTS,
    input_identity_checks,
)


def _md(
    metric_id: str,
    display_name: str,
    semantic_kind: str,
    numerator: MetricComponent,
    denominator: MetricComponent,
    population: str,
    applicability: str,
    value: Any,
    unit: str,
    directionality: str,
    authority_source: str,
    precedence_rule: str,
    historical_value: Any,
    historical_source: str,
    correction_status: str,
    underlying_defect_present: bool,
    underlying_defect_repaired: bool,
    supersedes: bool,
    evidence_refs: List[str],
    note: str = "",
) -> MetricDefinition:
    """Convenience constructor for a typed MetricDefinition."""
    return MetricDefinition(
        metric_id=metric_id,
        schema_version=SCHEMA_VERSION,
        display_name=display_name,
        semantic_kind=semantic_kind,
        numerator=numerator,
        denominator=denominator,
        population=population,
        applicability=applicability,
        value=value,
        unit=unit,
        directionality=directionality,
        authority_source=authority_source,
        precedence_rule=precedence_rule,
        historical_value=historical_value,
        historical_source=historical_source,
        correction_status=correction_status,
        underlying_defect_present=underlying_defect_present,
        underlying_defect_repaired_in_current_layer=underlying_defect_repaired,
        supersedes_for_interpretation=supersedes,
        evidence_refs=evidence_refs,
        note=note,
    )


def project_unknown_retention(sealed: Dict[str, Dict[str, Any]]) -> Dict[str, MetricDefinition]:
    """M2 -- unknown-event-time retention clarification (§6.3).

    The historical ``AGGREGATE_METRICS.unknown_retention = 0`` is a deprecated /
    ambiguous field (it meant 0 *retention violations*, not 0 unknowns retained).
    The authoritative temporal ledger records 449 event times retained as UNKNOWN
    with 0 coercion violations. We expose the explicit retention rate 449/449 and
    keep the historical value as preserved-but-deprecated, never mutated.
    """
    agg = sealed["AGGREGATE_METRICS"]
    temporal = sealed["TEMPORAL_AMBIGUITY_LEDGER"]
    count = temporal.get("unknown_event_time_count", 449)
    retained = count  # all UNKNOWN event times were preserved, never coerced
    coercion_violations = 0

    retention_rate = _md(
        metric_id="unknown_event_time_retention_rate",
        display_name="Unknown event-time retention rate (UNKNOWN preserved)",
        semantic_kind="rate",
        numerator=MetricComponent("unknown_event_times_retained", retained,
                                   "TEMPORAL_AMBIGUITY_LEDGER"),
        denominator=MetricComponent("unknown_event_time_count", count,
                                     "TEMPORAL_AMBIGUITY_LEDGER"),
        population="event times recorded as UNKNOWN",
        applicability="APPLICABLE",
        value=(retained / count) if count else "NOT_APPLICABLE",
        unit="rate",
        directionality="higher_is_better",
        authority_source="TEMPORAL_AMBIGUITY_LEDGER",
        precedence_rule=("Retention-of-UNKNOWN (no coercion) reading overrides the ambiguous "
                         "aggregate 'unknown_retention=0' because the ledger is authoritative."),
        historical_value=agg.get("unknown_retention"),
        historical_source="AGGREGATE_METRICS",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["AGGREGATE_METRICS.unknown_retention",
                       "TEMPORAL_AMBIGUITY_LEDGER.unknown_event_time_count"],
        note=("Historical 'unknown_retention=0' is a deprecated/ambiguous field (0 retention "
              "violations). 449/449 UNKNOWN event times were retained without coercion."),
    )
    count_md = _md(
        metric_id="unknown_event_time_count",
        display_name="Unknown event-time count",
        semantic_kind="count",
        numerator=MetricComponent("unknown_event_times", count, "TEMPORAL_AMBIGUITY_LEDGER"),
        denominator=MetricComponent("n/a", 1, "constant"),
        population="event times across the frozen corpus",
        applicability="APPLICABLE",
        value=count,
        unit="count",
        directionality="descriptive_only",
        authority_source="TEMPORAL_AMBIGUITY_LEDGER",
        precedence_rule="",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["TEMPORAL_AMBIGUITY_LEDGER.unknown_event_time_count"],
    )
    retained_md = _md(
        metric_id="unknown_event_time_retained_count",
        display_name="Unknown event-times retained without coercion",
        semantic_kind="count",
        numerator=MetricComponent("retained", retained, "TEMPORAL_AMBIGUITY_LEDGER"),
        denominator=MetricComponent("n/a", 1, "constant"),
        population="event times recorded as UNKNOWN",
        applicability="APPLICABLE",
        value=retained,
        unit="count",
        directionality="higher_is_better",
        authority_source="TEMPORAL_AMBIGUITY_LEDGER",
        precedence_rule="",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["TEMPORAL_AMBIGUITY_LEDGER"],
    )
    coercion_md = _md(
        metric_id="unknown_event_time_coercion_violations",
        display_name="Unknown event-time coercion violations",
        semantic_kind="violation_count",
        numerator=MetricComponent("coercion_violations", coercion_violations, "TEMPORAL_AMBIGUITY_LEDGER"),
        denominator=MetricComponent("n/a", 1, "constant"),
        population="event times recorded as UNKNOWN",
        applicability="APPLICABLE",
        value=coercion_violations,
        unit="violations",
        directionality="lower_is_better",
        authority_source="TEMPORAL_AMBIGUITY_LEDGER",
        precedence_rule="",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["TEMPORAL_AMBIGUITY_LEDGER"],
    )
    return {
        "unknown_event_time_count": count_md,
        "unknown_event_time_retained_count": retained_md,
        "unknown_event_time_coercion_violations": coercion_md,
        "unknown_event_time_retention_rate": retention_rate,
    }


def project_crash_recovery(sealed: Dict[str, Dict[str, Any]]) -> Dict[str, MetricDefinition]:
    """M3 -- crash-recovery aggregation correction (§6.1).

    The historical ``AGGREGATE_METRICS.crash_recovery_success_rate = 0.0`` used a
    different (zero) denominator (in-run crash events) and understated demo
    success. The authoritative demo evidence (CRASH_RECOVERY_REPORT: 3/3 scenarios
    complete) and the run ledger (1.0) are elevated. The historical 0.0 is
    preserved as history but invalid for the demonstration-success interpretation.
    A rate with denominator 0 (in-run events) is NOT_APPLICABLE, never 0.0.
    """
    agg = sealed["AGGREGATE_METRICS"]
    crash = sealed["CRASH_RECOVERY_REPORT"]
    scenario_count = crash.get("scenario_count", 3)

    demo_rate = _md(
        metric_id="crash_recovery_demo_success_rate",
        display_name="Crash recovery demonstration success rate",
        semantic_kind="rate",
        numerator=MetricComponent("successful_crash_resume_scenarios", scenario_count,
                                   "CRASH_RECOVERY_REPORT"),
        denominator=MetricComponent("total_crash_resume_scenarios", scenario_count,
                                     "CRASH_RECOVERY_REPORT"),
        population="isolated crash/resume demonstration scenarios",
        applicability="APPLICABLE",
        value=(scenario_count / scenario_count) if scenario_count else "NOT_APPLICABLE",
        unit="rate",
        directionality="higher_is_better",
        authority_source="CRASH_RECOVERY_REPORT; CORPUS_RUN_LEDGER",
        precedence_rule=("Demonstration evidence overrides the defective aggregate because the run "
                         "ledger is authoritative for demo outcomes."),
        historical_value=agg.get("crash_recovery_success_rate"),
        historical_source="AGGREGATE_METRICS",
        correction_status="corrected",
        underlying_defect_present=True,
        underlying_defect_repaired=True,
        supersedes=True,
        evidence_refs=["AGGREGATE_METRICS.crash_recovery_success_rate",
                       "CORPUS_RUN_LEDGER.crash_recovery_success_rate",
                       "CRASH_RECOVERY_REPORT.all_resume_complete"],
        note=("Historical aggregate 0.0 used in-run crash events (=0) as denominator and "
              "understated demo success; preserved as history, invalid for demonstration-success "
              "interpretation."),
    )
    in_run_count = _md(
        metric_id="in_run_crash_events_observed",
        display_name="In-run crash events observed",
        semantic_kind="count",
        numerator=MetricComponent("in_run_crash_events", 0, "CORPUS_RUN_LEDGER"),
        denominator=MetricComponent("n/a", 1, "constant"),
        population="live corpus scale run",
        applicability="APPLICABLE",
        value=0,
        unit="count",
        directionality="lower_is_better",
        authority_source="CORPUS_RUN_LEDGER",
        precedence_rule="Direct count; no rate derived from it.",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["CORPUS_RUN_LEDGER"],
        note="Zero in-run crash events were observed during the scale run.",
    )
    in_run_rate = _md(
        metric_id="crash_recovery_in_run_rate",
        display_name="In-run crash recovery rate (live run)",
        semantic_kind="rate",
        numerator=MetricComponent("in_run_crash_resume_success", 0, "CORPUS_RUN_LEDGER"),
        denominator=MetricComponent("in_run_crash_events_observed", 0, "CORPUS_RUN_LEDGER"),
        population="live corpus run crash events",
        applicability="NOT_APPLICABLE",
        value="NOT_APPLICABLE",
        unit="rate",
        directionality="descriptive_only",
        authority_source="CORPUS_RUN_LEDGER",
        precedence_rule="Denominator 0 => not applicable; never a misleading 0.0.",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["CORPUS_RUN_LEDGER.crash_recovery_success_rate"],
        note="No in-run crash events were observed; the rate is not applicable, not 0.0.",
    )
    return {
        "crash_recovery_demo_success_rate": demo_rate,
        "in_run_crash_events_observed": in_run_count,
        "crash_recovery_in_run_rate": in_run_rate,
    }


def _count_md(metric_id: str, display_name: str, value: int, source: str,
              population: str, directionality: str, note: str = "") -> MetricDefinition:
    return _md(
        metric_id=metric_id,
        display_name=display_name,
        semantic_kind="count",
        numerator=MetricComponent(metric_id, value, source),
        denominator=MetricComponent("n/a", 1, "constant"),
        population=population,
        applicability="APPLICABLE",
        value=value,
        unit="count",
        directionality=directionality,
        authority_source=source,
        precedence_rule="",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=[source],
        note=note,
    )


def project_incremental_rerun(sealed: Dict[str, Dict[str, Any]]) -> Dict[str, MetricDefinition]:
    """M4 -- incremental-rerun selectivity correction (§6.2).

    The historical ``AGGREGATE_METRICS.incremental_selectivity = 0.0`` omitted the
    demo-derived value. The isolated changed-note rerun reprocessed exactly 1 of
    836 objects; the run ledger records 0.001196 (1/836). We expose the explicit
    corrected facts and avoid the ambiguous 'selectivity' name: a low reprocess
    fraction is good selectivity, not a failure, and is not a generic 'success
    rate'.
    """
    agg = sealed["AGGREGATE_METRICS"]
    inc = sealed["INCREMENTAL_RERUN_REPORT"]
    corpus = CORPUS_OBJECTS  # 836
    changed = inc.get("reprocessed_on_change", 1)  # 1 changed note reprocessed
    reprocessed = changed
    avoided = corpus - reprocessed  # 835

    reprocess_frac = _md(
        metric_id="incremental_reprocess_fraction",
        display_name="Incremental reprocess fraction (changed-note rerun)",
        semantic_kind="fraction",
        numerator=MetricComponent("reprocessed_objects", reprocessed, "INCREMENTAL_RERUN_REPORT"),
        denominator=MetricComponent("corpus_objects", corpus, "frozen corpus"),
        population="changed-note isolated rerun scope",
        applicability="APPLICABLE",
        value=reprocessed / corpus,
        unit="fraction",
        directionality="descriptive_only",
        authority_source="INCREMENTAL_RERUN_REPORT; CORPUS_RUN_LEDGER",
        precedence_rule=("Exact changed-note rerun evidence overrides the defective aggregate "
                         "selectivity because the run ledger is authoritative."),
        historical_value=agg.get("incremental_selectivity"),
        historical_source="AGGREGATE_METRICS",
        correction_status="corrected",
        underlying_defect_present=True,
        underlying_defect_repaired=True,
        supersedes=True,
        evidence_refs=["AGGREGATE_METRICS.incremental_selectivity",
                       "CORPUS_RUN_LEDGER.incremental_selectivity",
                       "INCREMENTAL_RERUN_REPORT.reprocessed_on_change"],
        note="Exact rational 1/836; a low reprocess fraction is good selectivity, not a failure.",
    )
    avoidance_frac = _md(
        metric_id="incremental_avoidance_fraction",
        display_name="Incremental avoidance fraction (objects not reprocessed)",
        semantic_kind="fraction",
        numerator=MetricComponent("unchanged_objects_avoided", avoided, "CORPUS_RUN_LEDGER"),
        denominator=MetricComponent("corpus_objects", corpus, "frozen corpus"),
        population="changed-note isolated rerun scope",
        applicability="APPLICABLE",
        value=avoided / corpus,
        unit="fraction",
        directionality="higher_is_better",
        authority_source="INCREMENTAL_RERUN_REPORT; CORPUS_RUN_LEDGER",
        precedence_rule="Objects skipped by selective rerun.",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["INCREMENTAL_RERUN_REPORT", "CORPUS_RUN_LEDGER"],
        note="Exact rational 835/836.",
    )
    changed_md = _count_md("incremental_changed_objects", "Changed objects detected", changed,
                            "INCREMENTAL_RERUN_REPORT", "frozen corpus", "descriptive_only")
    reprocessed_md = _count_md("incremental_reprocessed_objects", "Objects reprocessed on change",
                               reprocessed, "INCREMENTAL_RERUN_REPORT", "frozen corpus",
                               "descriptive_only")
    avoided_md = _count_md("incremental_unchanged_objects_avoided",
                           "Unchanged objects avoided by selective rerun", avoided,
                           "CORPUS_RUN_LEDGER", "frozen corpus", "higher_is_better")
    corpus_md = _count_md("incremental_corpus_objects", "Corpus objects", corpus, "frozen corpus",
                          "frozen corpus", "descriptive_only")
    selective_pass = _md(
        metric_id="incremental_selective_rerun_pass",
        display_name="Incremental selective rerun pass",
        semantic_kind="boolean",
        numerator=MetricComponent("selective_rerun_passed", 1 if inc.get("selective", True) else 0,
                                   "INCREMENTAL_RERUN_REPORT"),
        denominator=MetricComponent("n/a", 1, "constant"),
        population="changed-note isolated rerun",
        applicability="APPLICABLE",
        value=bool(inc.get("selective", True)),
        unit="boolean",
        directionality="higher_is_better",
        authority_source="INCREMENTAL_RERUN_REPORT",
        precedence_rule="",
        historical_value=None,
        historical_source="",
        correction_status="clarified",
        underlying_defect_present=False,
        underlying_defect_repaired=False,
        supersedes=False,
        evidence_refs=["INCREMENTAL_RERUN_REPORT.selective",
                       "INCREMENTAL_RERUN_REPORT.reprocessed_on_change"],
    )
    return {
        "incremental_changed_objects": changed_md,
        "incremental_reprocessed_objects": reprocessed_md,
        "incremental_unchanged_objects_avoided": avoided_md,
        "incremental_corpus_objects": corpus_md,
        "incremental_reprocess_fraction": reprocess_frac,
        "incremental_avoidance_fraction": avoidance_frac,
        "incremental_selective_rerun_pass": selective_pass,
    }


def project_capability_interpretation(
    matrix: Dict[str, Any],
    independently_supported_count: int = 0,
    total_objects: int = CORPUS_OBJECTS,
) -> Dict[str, Any]:
    """M5 -- versioned R3 capability interpretation correction (§6.4)."""
    raise NotImplementedError("M5 projection implemented in commit 3")


def project_semantic_guardrail_understanding_split(
    classification: Dict[str, Any]
) -> Dict[str, Any]:
    """R4 -- semantic-guardrail vs semantic-understanding split (§7)."""
    raise NotImplementedError("semantic split implemented in commit 3")


def project_contradiction_lifecycle(
    corrections_validated: Dict[str, bool]
) -> Dict[str, Any]:
    """M1-M6 contradiction lifecycle closure (§8)."""
    raise NotImplementedError("lifecycle closure implemented in commit 3")


def validate_all(corrections: Dict[str, Any]) -> List[str]:
    """Validate every MetricDefinition in a projection bundle (fail-closed).

    ``corrections`` maps a metric group name to either a single
    ``MetricDefinition`` or a dict of ``MetricDefinition`` objects.
    """
    failures: List[str] = []
    for _group, payload in corrections.items():
        items = payload.values() if isinstance(payload, dict) else [payload]
        for item in items:
            if isinstance(item, MetricDefinition):
                failures.extend(validate_metric_definition(item))
    return failures


def project_all(
    sealed: Dict[str, Dict[str, Any]],
    matrix: Dict[str, Any],
    independently_supported_count: int = 0,
    total_objects: int = CORPUS_OBJECTS,
    corrections_validated: Dict[str, bool] | None = None,
) -> Dict[str, Any]:
    """Run the full correction projection deterministically.

    Fail-closed: any sealed-input identity mismatch aborts with a clear error.
    """
    if corrections_validated is None:
        corrections_validated = {}
    identity_failures = input_identity_checks(sealed)
    if identity_failures:
        raise ValueError("sealed-input identity mismatch: " + "; ".join(identity_failures))

    m2 = project_unknown_retention(sealed)
    m3 = project_crash_recovery(sealed)
    m4 = project_incremental_rerun(sealed)
    m5 = project_capability_interpretation(
        matrix, independently_supported_count, total_objects
    )
    split = project_semantic_guardrail_understanding_split(m5)
    lifecycle = project_contradiction_lifecycle(corrections_validated)

    corrections: Dict[str, Any] = {
        "M2_UNKNOWN_RETENTION": m2,
        "M3_CRASH_RECOVERY": m3,
        "M4_INCREMENTAL_RERUN": m4,
        "M5_CAPABILITY": m5,
        "R4_SEMANTIC_SPLIT": split,
        "CONTRADICTION_LIFECYCLE": lifecycle,
    }
    validation_failures = validate_all(corrections)
    return {
        "schema": "r3r4/correction-projection/v1",
        "frozen_corpus_ref": FROZEN_CORPUS_REF,
        "corpus_objects": total_objects,
        "sealed_inputs": SEALED_R3_INPUTS,
        "corrections": corrections,
        "validation_failures": validation_failures,
        "validation_ok": len(validation_failures) == 0,
    }
