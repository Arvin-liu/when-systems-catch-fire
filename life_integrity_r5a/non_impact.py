# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Mandatory non-impact proof for R5-A (task §13).

R5-A is a candidate governance/architecture overlay. It must prove it does NOT:
  * alter the existing Life Community Value Charter text or authority;
  * change Foundation axioms;
  * change ARR runtime semantics;
  * change Function OS execution authority;
  * add a second executor;
  * enable human intervention;
  * provide individual medical or psychological advice;
  * implement the Modern Wuzhen domain pack;
  * implement a general Domain Pack spec or federation runtime;
  * modify PR #109-#129 or predecessor frozen tags;
  * alter Main;
  * call PROMOTE or EVOLVE.

This module is declarative and deterministic; it does not read or modify any
repository file. The formal evidence (commit #99) verifies the actual diff
against this list.
"""

from __future__ import annotations

from .registries import CONTROL_COMMIT, FORMAL_PREDECESSOR, TASK_ID

NON_IMPACT_ITEMS = (
    "life_community_value_charter_text_and_authority",
    "foundation_axioms",
    "arr_runtime_semantics",
    "function_os_execution_authority",
    "second_executor_added",
    "human_intervention_enabled",
    "individual_medical_or_psychological_advice",
    "modern_wuzhen_domain_pack_implemented",
    "domain_pack_spec_or_federation_runtime_implemented",
    "predecessor_prs_or_frozen_tags_modified",
    "main_modified",
    "promote_or_evolve_called",
)


def build_non_impact_proof() -> dict:
    """Return the declarative non-impact proof (all items NOT altered)."""
    return {
        "schema": "r5a/non-impact-proof/v1",
        "task_id": TASK_ID,
        "control_commit": CONTROL_COMMIT,
        "formal_predecessor": FORMAL_PREDECESSOR,
        "predicate": "R5-A does not alter any of the listed surfaces",
        "items": [
            {"item": item, "status": "NOT_ALTERED_BY_R5A"} for item in NON_IMPACT_ITEMS
        ],
        "unavoidable_propagation": (
            "Any cross-file propagation is limited to registry / map / "
            "documentation / CI synchronization and is itemized in the "
            "external-review package."
        ),
    }


def proof_items_consistent(proof: dict | None = None) -> bool:
    p = proof if proof is not None else build_non_impact_proof()
    declared = {item["item"] for item in p["items"]}
    if declared != set(NON_IMPACT_ITEMS):
        return False
    return all(item["status"] == "NOT_ALTERED_BY_R5A" for item in p["items"])
