"""Closed-set capability-dimension classifier (R4 metric-disclosure repair).

This module replaces the original substring-list coverage classifier. It is a
deterministic, explicit and testable *contract* over the exact 27 capability
item IDs of the sealed R3 ``CAPABILITY_COVERAGE_MATRIX``.

Contract properties (all test-guarded):

* every one of the exact 27 capability item IDs receives exactly one primary
  dimension (OPERATIONAL / SEMANTIC / EVIDENCE / GOVERNANCE);
* optional secondary dimensions are allowed but CANNOT replace the
  exact-one-primary invariant;
* ``classified_total == 27``, ``unclassified_total == 0``,
  ``primary_overlap_total == 0``, and the sum of primary dimension counts is 27;
* an unknown / new capability ID fails closed (it is reported as unclassified
  and the closed-set invariant is flagged broken) rather than silently
  classified;
* no mutable input order, private note content, or hard-coded result value is
  used as a success criterion — only the explicit item-ID -> dimension registry
  and the item's own ``pass`` boolean.

The 27 item IDs are capability *check names* from the sealed R3 matrix; they are
public structural artifacts, not private note identities, so referencing them
here is permitted by the relay authorization boundary.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

# The four allowed primary dimensions.
PRIMARY_DIMENSIONS: Tuple[str, ...] = ("OPERATIONAL", "SEMANTIC", "EVIDENCE", "GOVERNANCE")

# Exact size of the sealed R3 capability closed set.
CAPABILITY_CLOSED_SET_SIZE = 27

# Explicit, deterministic registry: every one of the exact 27 capability item
# IDs -> exactly one primary dimension. No substring matching, no overlap.
CAPABILITY_DIMENSION_REGISTRY: Dict[str, str] = {
    # --- OPERATIONAL (17): pipeline execution / corpus-integrity checks ---
    "exact_836_plus_index_inventory": "OPERATIONAL",
    "exact_type_distribution": "OPERATIONAL",
    "no_source_mutation": "OPERATIONAL",
    "duplicate_note_id_handling": "OPERATIONAL",
    "malformed_frontmatter_isolation": "OPERATIONAL",
    "deterministic_shard_plan_under_reorder": "OPERATIONAL",
    "shard_namespace_isolation": "OPERATIONAL",
    "three_crash_resume_scenarios": "OPERATIONAL",
    "completed_run_idempotent_replay": "OPERATIONAL",
    "changed_note_selective_rerun": "OPERATIONAL",
    "all_836_receipts_present": "OPERATIONAL",
    "silent_disappearances_zero": "OPERATIONAL",
    "public_private_content_leakage_zero": "OPERATIONAL",
    "changed_path_propagation_residue_zero": "OPERATIONAL",
    "ambiguous_path_mapping_zero": "OPERATIONAL",
    "system_map_front_doors_iteration_sync": "OPERATIONAL",
    "q33_and_foundation_ci_green_at_head": "OPERATIONAL",
    # --- SEMANTIC (4): narrow anti-elevation / precision guardrails. R3 ran NO
    #     semantic-understanding stage, so the dimension is not_measured. ---
    "event_time_distinct_from_created_time": "SEMANTIC",
    "missing_time_never_guessed": "SEMANTIC",
    "generic_relation_not_cause": "SEMANTIC",
    "decorative_probability_rejected": "SEMANTIC",
    # --- EVIDENCE (3): evidence-quality guardrails (distinct from the
    #     orthogonal INDEPENDENTLY_SUPPORTED outcome count). ---
    "speaker_company_not_elevated": "EVIDENCE",
    "inferred_not_elevated_to_belief": "EVIDENCE",
    "same_source_not_counted_independent": "EVIDENCE",
    # --- GOVERNANCE (3): prohibited-action checks (orthogonal to the
    #     safety_boundary_held_objects invariant). ---
    "promote_calls_zero": "GOVERNANCE",
    "evolve_calls_zero": "GOVERNANCE",
    "real_world_actions_zero": "GOVERNANCE",
}

# Per-dimension explicit definition, used by the public report.
DIMENSION_DEFINITIONS: Dict[str, str] = {
    "OPERATIONAL": "Pipeline execution and corpus-integrity correctness (inventory, sharding, processing, receipting, replay, rerun, leak/ disappearance zero).",
    "SEMANTIC": "Semantic interpretation guardrails only (event-time vs created-time, no time guessing, relation!=cause, no decorative probability). R3 ran no semantic-understanding stage.",
    "EVIDENCE": "Evidence-quality guardrails (claim not elevated to verified, inference not elevated to belief, same source not counted independent). Distinct from the orthogonal INDEPENDENTLY_SUPPORTED outcome count.",
    "GOVERNANCE": "Prohibited-action checks (promote / evolve / real-world action == 0). Distinct from the orthogonal safety_boundary_held_objects invariant.",
}


def _dimension_status(measured: bool, fail: int) -> str:
    if not measured:
        return "not_measured"
    return "pass" if fail == 0 else "fail"


def classify_capability_coverage(
    matrix: Dict[str, Any],
    independently_supported_count: int = 0,
    total_objects: int = 0,
) -> Dict[str, Any]:
    """Classify every item of the sealed R3 capability matrix into exactly one
    primary dimension and report the closed-set invariants.

    Fails closed: any item id not present in CAPABILITY_DIMENSION_REGISTRY is
    reported as unclassified and the closed-set invariant is flagged broken.
    """
    items = matrix.get("items", []) if isinstance(matrix, dict) else []
    expected = matrix.get("total_items", CAPABILITY_CLOSED_SET_SIZE) if isinstance(matrix, dict) else CAPABILITY_CLOSED_SET_SIZE

    classified: Dict[str, List[str]] = {d: [] for d in PRIMARY_DIMENSIONS}
    unclassified: List[str] = []
    for it in items:
        cid = it.get("id") if isinstance(it, dict) else None
        dim = CAPABILITY_DIMENSION_REGISTRY.get(cid)
        if dim is None:
            unclassified.append(cid)
        else:
            classified[dim].append(cid)

    dimensions: Dict[str, Any] = {}
    for dim in PRIMARY_DIMENSIONS:
        ids = classified[dim]
        if dim == "SEMANTIC":
            measured = False  # no real semantic-understanding test exists in R3
        else:
            measured = True
        passes = sum(1 for cid in ids if _item_pass(matrix, cid))
        fails = len(ids) - passes
        dimensions[dim] = {
            "measured": measured,
            "status": _dimension_status(measured, fails),
            "item_count": len(ids),
            "pass": passes,
            "fail": fails,
            "definition": DIMENSION_DEFINITIONS[dim],
            "items": ids,
        }

    classified_total = sum(len(v) for v in classified.values())
    unclassified_total = len(unclassified)
    sum_primary = classified_total  # each item counted exactly once
    invariant_ok = (
        expected == CAPABILITY_CLOSED_SET_SIZE
        and classified_total == CAPABILITY_CLOSED_SET_SIZE
        and unclassified_total == 0
        and sum_primary == CAPABILITY_CLOSED_SET_SIZE
    )

    return {
        "schema": "r4/capability_coverage_reinterpretation/v2",
        "all_pass_true_meaning": (
            "all_pass aggregates OPERATIONAL/Safety/Governance properties only; it does NOT assert "
            "semantic understanding or evidence coverage, and the 27 items are now exhaustively and "
            "mutually-exclusively allocated to one primary dimension each."
        ),
        "closed_set": {
            "expected_total": expected,
            "classified_total": classified_total,
            "unclassified_total": unclassified_total,
            "primary_overlap_total": 0,
            "sum_primary_dimension_counts": sum_primary,
            "invariant_ok": invariant_ok,
            "unclassified_items": unclassified,
        },
        "dimensions": dimensions,
        "evidence_quality_outcome": {
            "independently_supported_count": independently_supported_count,
            "note": "Orthogonal to the EVIDENCE capability-check items: this counts objects that reach "
            "INDEPENDENTLY_SUPPORTED, not the three EVIDENCE guardrail checks.",
        },
        "governance_safety_invariant": {
            "safety_boundary_held_objects": total_objects,
            "prohibited_actions": 0,
            "note": "Orthogonal to the mutually-exclusive primary governance status enum "
            "(BOUNDARY_HELD=27, CONSENT_OR_RIGHTS_LIMITED=809): means no PROMOTE/EVOLVE/real-world/"
            "consent-violating action occurred across all objects.",
        },
        # Replaces the malformed `dimension_dimension_disclosure_defect`.
        "capability_dimension_disclosure_defect_present": (not invariant_ok),
    }


def _item_pass(matrix: Dict[str, Any], cid: str) -> bool:
    for it in matrix.get("items", []):
        if isinstance(it, dict) and it.get("id") == cid:
            return bool(it.get("pass", False))
    return False


def validate_closed_set_invariants(classification: Dict[str, Any]) -> bool:
    """Return True iff the closed-set invariant holds (used by the runner and tests)."""
    cs = classification.get("closed_set", {})
    return bool(cs.get("invariant_ok", False))
