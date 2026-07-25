# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Machine-readable candidate charter manifest for R5-A.

Every public R5-A artifact must visibly declare these flags. They are the
non-impact and non-activation surface: this candidate does NOT activate a
charter, does NOT enable human intervention, does NOT authorize medical
claims, does NOT start the Modern Wuzhen domain pack, does NOT start a domain
pack / federation runtime, and does NOT claim external acceptance.
"""

from __future__ import annotations

from .registries import (
    CONTROL_COMMIT,
    FORMAL_PREDECESSOR,
    FROZEN_HEAD,
    SCHEMA_VERSION,
    TASK_ID,
)

# The exact flag set every R5-A public artifact must carry (and assert).
MANIFEST_REQUIRED_FLAGS = (
    "activation_status",
    "human_intervention_enabled",
    "medical_claims_authorized",
    "modern_wuzhen_pack_started",
    "domain_pack_federation_started",
    "external_acceptance_claimed",
)

CANDIDATE_MANIFEST = {
    "schema": "r5a/candidate-charter-manifest/v1",
    "schema_version": SCHEMA_VERSION,
    "task_id": TASK_ID,
    "control_commit": CONTROL_COMMIT,
    "formal_predecessor": FORMAL_PREDECESSOR,
    "frozen_head": FROZEN_HEAD,
    "title": "Life Integrity Charter Candidate R1",
    "activation_status": "CANDIDATE_ONLY",
    "human_intervention_enabled": False,
    "medical_claims_authorized": False,
    "modern_wuzhen_pack_started": False,
    "domain_pack_federation_started": False,
    "external_acceptance_claimed": False,
    "authorized_next_iteration": False,
    "supreme_charter": "LifeCommunityValueCharter",
    "not_authorized": [
        "R5-B Embodied Life System runtime",
        "R5-C Modern Wuzhen Domain Pack implementation",
        "source-text ingestion / new religious corpus",
        "practice instructions for a real person",
        "medical / psychiatric / diagnostic / treatment claims",
        "collection of human health data",
        "human-profile database",
        "real-world experiments",
        "domain-pack federation implementation",
        "L7 / second executor",
        "PROMOTE",
        "EVOLVE",
        "Ready",
        "merge",
        "Main change",
        "force push",
        "history rewrite",
        "public release of private / reconstructive content",
    ],
    "artifacts": [
        "docs/governance/life-integrity-charter-candidate-r1.md",
        "docs/architecture/ignition-life-integrity-r5a-r1.md",
        "docs/architecture/tradition-translation-pipeline-r1.md",
        "docs/architecture/life-integrity-non-impact-proof-r1.md",
        "docs/architecture/life-integrity-future-activation-boundary-r1.md",
        "docs/architecture/ignition-r5a-life-integrity-r1/candidate-charter-manifest.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/embodied-view-registry.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/tradition-claim-class-registry.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/concept-mapping-lifecycle-registry.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/life-integrity-assessment-schema.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/embodied-view-projection-schema.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/translated-claim-schema.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/practice-safety-envelope-schema.json",
        "docs/architecture/ignition-r5a-life-integrity-r1/concept-mapping-transition-schema.json",
    ],
}


def manifest_flags_consistent(manifest: dict | None = None) -> bool:
    """Fail-closed: every required flag must be present and the candidate-only
    values must be exactly the non-activation defaults."""
    m = manifest if manifest is not None else CANDIDATE_MANIFEST
    for flag in MANIFEST_REQUIRED_FLAGS:
        if flag not in m:
            return False
    return (
        m["activation_status"] == "CANDIDATE_ONLY"
        and m["human_intervention_enabled"] is False
        and m["medical_claims_authorized"] is False
        and m["modern_wuzhen_pack_started"] is False
        and m["domain_pack_federation_started"] is False
        and m["external_acceptance_claimed"] is False
    )
