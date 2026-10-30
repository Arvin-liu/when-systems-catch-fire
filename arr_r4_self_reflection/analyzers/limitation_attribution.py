"""Primary limitation attribution with exclusion reasoning (R4 task §6, §8).

Every observed weakness receives one primary class and an exclusion record
explaining why adjacent classes do not fit. A primary class must be supported
by an exclusion record. Evidence missing from the corpus is NOT an architecture
defect; a metric definition bug is NOT a runtime defect; a pipeline-complete
object with weak source support is NOT a processing failure; a repeated source
is NOT independent corroboration.
"""

from __future__ import annotations

from typing import Any, Dict, List


def analyze_limitation_attribution(reports: Dict[str, Any], four_axis_summary: Dict[str, Any]) -> Dict[str, Any]:
    temporal = reports.get("TEMPORAL_AMBIGUITY_LEDGER", {})
    fc = reports.get("FALSE_CONSENSUS_CASES", {})
    est = reports.get("INDEPENDENT_SOURCE_ESTIMATE", {})
    agg = reports.get("AGGREGATE_METRICS", {})

    limitations: List[Dict[str, Any]] = []

    # 1. Temporal ambiguity
    limitations.append({
        "limitation_id": "L1_TEMPORAL_AMBIGUITY",
        "primary_class": "TEMPORAL_LIMITATION",
        "secondary_factors": ["SOURCE_DEPENDENCY_LIMITATION"],
        "exclusion": {
            "MATERIAL_OR_SOURCE_LIMITATION": "dates are absent in the source material, not corrupted by ingestion",
            "RUNTIME_DEFECT": "pipeline never guessed a time; missing_time_never_guessed passed",
            "ARCHITECTURE_CANDIDATE": "absent time is a property of the source, not a system design gap",
            "EXTRACTION_LIMITATION": "extraction correctly refused to invent dates",
        },
        "evidence_refs": [
            f"TEMPORAL_AMBIGUITY_LEDGER.unknown_event_time_count={temporal.get('unknown_event_time_count')}",
            f"TEMPORAL_AMBIGUITY_LEDGER.temporal_ambiguity_rate={temporal.get('temporal_ambiguity_rate')}",
        ],
    })

    # 2. Source concentration / false consensus
    limitations.append({
        "limitation_id": "L2_SOURCE_CONCENTRATION",
        "primary_class": "SOURCE_DEPENDENCY_LIMITATION",
        "secondary_factors": ["FALSE_CONSENSUS_RISK"],
        "exclusion": {
            "RUNTIME_DEFECT": "concentration is in the source host map, not in runtime behavior",
            "ARCHITECTURE_CANDIDATE": "no primitive failed to represent or route; it is material concentration",
            "MATERIAL_OR_SOURCE_LIMITATION": "adjacent but source-dependency is the precise class for provenance",
        },
        "evidence_refs": [
            f"INDEPENDENT_SOURCE_ESTIMATE.estimate={est.get('estimate')}",
            f"FALSE_CONSENSUS_CASES.false_consensus_risk={fc.get('false_consensus_risk')}",
            "SOURCE_DEPENDENCY_GRAPH.host_map",
        ],
    })

    # 3. Semantic not attempted
    sem = four_axis_summary.get("semantic", {})
    limitations.append({
        "limitation_id": "L3_SEMANTIC_NOT_ATTEMPTED",
        "primary_class": "REPRESENTATION_LIMITATION",
        "secondary_factors": ["EXTRACTION_LIMITATION"],
        "exclusion": {
            "RUNTIME_DEFECT": "no runtime error; representation completed",
            "ARCHITECTURE_CANDIDATE": "R3 contract was measurement-only; absence of understanding is by design, not a gap",
            "MATERIAL_OR_SOURCE_LIMITATION": "not about source material but about what the pipeline computed",
        },
        "evidence_refs": [
            f"FOUR_AXIS_OBJECT_LEDGER.semantic.SEMANTIC_NOT_ATTEMPTED={sem.get('SEMANTIC_NOT_ATTEMPTED', 0)}",
            f"FOUR_AXIS_OBJECT_LEDGER.semantic.SEMANTIC_REPRESENTATION_LIMITED={sem.get('SEMANTIC_REPRESENTATION_LIMITED', 0)}",
            "R4 task §4 fact: independently verified claim class = 0",
        ],
    })

    # 4. Metric observability defects (M2/M3/M4/M5)
    limitations.append({
        "limitation_id": "L4_METRIC_OBSERVABILITY",
        "primary_class": "METRIC_OR_OBSERVABILITY_DEFECT",
        "secondary_factors": ["AGGREGATION_DEFECT", "REPORTING_DEFECT"],
        "exclusion": {
            "RUNTIME_DEFECT": "the pipeline behaved correctly; only the reported metrics are defective/incomplete",
            "ARCHITECTURE_CANDIDATE": "fixing metric definitions is a reporting change, not a system redesign",
            "TEST_OR_CI_DEBT": "not a missing test; the metrics are mis-defined/mis-aggregated",
        },
        "evidence_refs": [
            f"AGGREGATE_METRICS.unknown_retention={agg.get('unknown_retention')}",
            f"AGGREGATE_METRICS.crash_recovery_success_rate={agg.get('crash_recovery_success_rate')}",
            f"AGGREGATE_METRICS.incremental_selectivity={agg.get('incremental_selectivity')}",
            "CORPUS_RUN_LEDGER (authoritative, contradicts aggregate)",
        ],
    })

    # 5. Consent/rights unverifiable for source-less notes (governance axis)
    gov = four_axis_summary.get("governance", {})
    limitations.append({
        "limitation_id": "L5_CONSENT_UNVERIFIABLE",
        "primary_class": "RIGHTS_OR_ACCESS_LIMITATION",
        "secondary_factors": ["GOVERNANCE_CONSTRAINT"],
        "exclusion": {
            "ARCHITECTURE_CANDIDATE": "provenance absence is a source-property, not a system gap",
            "RUNTIME_DEFECT": "pipeline handled rights_boundary=private correctly",
            "GOVERNANCE_CONSTRAINT": "boundary held (no prohibited action); this is the narrower consent-verify gap",
        },
        "evidence_refs": [
            f"FOUR_AXIS_OBJECT_LEDGER.governance.CONSENT_OR_RIGHTS_LIMITED={gov.get('CONSENT_OR_RIGHTS_LIMITED', 0)}",
            f"AGGREGATE_METRICS.source_link_completeness={agg.get('source_link_completeness')}",
        ],
    })

    return {
        "schema": "r4/limitation_attribution_ledger/v1",
        "limitations": limitations,
        "count": len(limitations),
        "architecture_candidates": 0,
    }
