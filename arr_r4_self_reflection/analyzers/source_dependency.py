"""Source-dependency and independent-source estimation review (R4 task §4 C6, §8)."""

from __future__ import annotations

from typing import Any, Dict, List


def analyze_source_dependency(reports: Dict[str, Any]) -> Dict[str, Any]:
    est = reports.get("INDEPENDENT_SOURCE_ESTIMATE", {})
    graph = reports.get("SOURCE_DEPENDENCY_GRAPH", {})
    host_map = graph.get("host_map", {})

    independent_sources = est.get("estimate", 0)
    distinct_hosts = est.get("distinct_source_hosts", 0)
    notes_with_source = est.get("notes_with_source", 0)

    # Host concentration: how many notes each host contributes.
    host_counts = {h: len(ks) for h, ks in host_map.items()}
    total_indexed = sum(host_counts.values())
    top_hosts = sorted(host_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]

    # Repeated notes across hosts do NOT inflate independent corroboration.
    note_to_hosts: Dict[str, List[str]] = {}
    for h, ks in host_map.items():
        for k in ks:
            note_to_hosts.setdefault(k, []).append(h)
    repeated_note_keys = sorted([k for k, hs in note_to_hosts.items() if len(hs) > 1])

    return {
        "schema": "r4/source_dependency_audit/v1",
        "independent_source_estimate": independent_sources,
        "distinct_source_hosts": distinct_hosts,
        "notes_with_source_ref": notes_with_source,
        "host_concentration": {
            "distinct_hosts": len(host_counts),
            "notes_indexed_to_host": total_indexed,
            "top_hosts": [{"host": h, "note_count": c} for h, c in top_hosts],
        },
        "repeated_note_keys_across_hosts": repeated_note_keys,
        "repeated_note_count": len(repeated_note_keys),
        "conclusion": (
            f"Corpus of {notes_with_source + (estimated_remainder(reports))} indexed notes resolves to "
            f"~{independent_sources} independent sources ({distinct_hosts} distinct hosts). Source "
            f"concentration is high; {len(repeated_note_keys)} notes appear under more than one host "
            f"derivative and must not inflate corroboration. Corpus size is not evidence count."
        ),
        "primary_limitation_class": "SOURCE_DEPENDENCY_LIMITATION",
    }


def estimated_remainder(reports: Dict[str, Any]) -> int:
    # Notes without any source reference: total selected minus notes_with_source.
    agg = reports.get("AGGREGATE_METRICS", {})
    selected = agg.get("corpus_notes_selected", 0)
    est = reports.get("INDEPENDENT_SOURCE_ESTIMATE", {})
    return max(0, selected - est.get("notes_with_source", 0))
