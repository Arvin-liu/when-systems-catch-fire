# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Aggregate fail-closed validator for the R5-A candidate and narrow repair."""

from __future__ import annotations

from . import attack_gate
from . import concept_mapping as CM
from . import embodied_view as EV
from . import fixtures as FX
from . import life_integrity as LI
from . import longitudinal as LG
from . import manifest
from . import non_impact as NI
from . import registries as R
from . import safety_envelope as SE
from . import tradition_translation as TT


def validate_all() -> tuple[bool, list[str]]:
    failures: list[str] = []

    declarative_checks = (
        (R.charter_hierarchy_respects_supremacy(), "charter hierarchy does not respect supremacy"),
        (EV.embodied_view_closed_set_complete(), "embodied view closed set incomplete"),
        (TT.claim_class_closed_set_complete(), "tradition claim-class closed set incomplete"),
        (CM.concept_state_closed_set_complete(), "concept-mapping state closed set incomplete"),
        (len(R.NORMATIVE_EMPIRICAL_TYPE_TAGS) == 10, "normative/empirical type-tag set is not exact"),
        (manifest.manifest_flags_consistent(), "candidate manifest flags inconsistent"),
        (NI.proof_items_consistent(), "non-impact proof inconsistent"),
        (
            CM.transition_graph_has_no_direct_jump_to_partially_supported(),
            "transition graph allows a direct jump to PARTIALLY_SUPPORTED",
        ),
        (SE.envelope_field_set_complete(), "safety envelope field set incomplete"),
        (LI.local_optimization_field_set_complete(), "local-optimization field set incomplete"),
    )
    failures.extend(message for ok, message in declarative_checks if not ok)

    # Positive contract paths are real objects, not counts.
    try:
        R.validate_charter_hierarchy(list(R.CHARTER_HIERARCHY))
        SE.validate_envelope(FX.sample_safety_envelope())
        LI.LifeIntegrityGate().validate_proposal(FX.sample_local_optimization_proposal())
        LG.validate_longitudinal_contract(FX.sample_longitudinal_contract())
        agent = FX.sample_embodied_agent()
        agent.require_whole_person_disclosure(
            claimed_views=list(R.EMBODIED_VIEW_IDS),
            missing_disclosed=True,
            contradictions_surfaced=True,
            evidence_objects=[FX.sample_multi_view_evidence()],
        )
        FX.sample_concept_mapping()
        FX.sample_translated_claim()
    except Exception as exc:
        failures.append(f"valid concrete contract object rejected: {type(exc).__name__}: {exc}")

    # The narrow-repair acceptance surface is the exact instance gate.  Every
    # stable id is executed and binds a distinct evidence object.
    receipt = attack_gate.run_attack_gate()
    if receipt["status"] != "PASS":
        failures.extend(receipt["identity_errors"])
        failures.extend(
            f"attack case failed: {case_id}" for case_id in receipt["failed_case_ids"]
        )

    return (not failures, failures)
