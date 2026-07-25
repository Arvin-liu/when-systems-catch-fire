# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Embodied-agent multi-view projection contract (R5-A, Commit 1 skeleton).

Commit 1 provides the full API surface and closed-set guarantees only. The
validation logic raises NotImplementedError and is implemented in Commit 2.

Design contract (task §6, §5.1):
  * all seven views carry the same subject identity and provenance boundary;
  * each view has observations, confidence, time scope and UNKNOWN fields;
  * cross-view relations are typed and do NOT imply causality;
  * contradictory views may coexist and must be surfaced;
  * the subject has autonomy/consent fields not reducible to a view score;
  * representation never claims to exhaust the person.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .registries import EMBODIED_VIEW_IDS, is_valid_embodied_view


class EmbodiedViewError(Exception):
    """Base error for embodied-view contract violations."""


class WholePersonClaimError(EmbodiedViewError):
    """Raised when a single view or projection claims the whole person."""


class CrossViewCausalityError(EmbodiedViewError):
    """Raised when a cross-view relation asserts causality."""


class MissingViewError(EmbodiedViewError):
    """Raised when a required view is absent and not disclosed as UNKNOWN."""


@dataclass
class EmbodiedViewProjection:
    view_id: str
    subject_identity: str
    observations: list[Any] = field(default_factory=list)
    confidence: float = 0.0
    time_scope: str = "UNKNOWN"
    unknown: bool = True
    provenance: str = ""

    def __post_init__(self) -> None:
        if not is_valid_embodied_view(self.view_id):
            raise EmbodiedViewError(f"unknown embodied view id: {self.view_id!r}")
        if not isinstance(self.subject_identity, str) or not self.subject_identity:
            raise EmbodiedViewError("subject_identity must be a non-empty string")


@dataclass
class CrossViewRelation:
    relation_type: str
    source_view: str
    target_view: str
    asserts_causality: bool = False
    notes: str = ""


@dataclass
class Contradiction:
    view_a: str
    view_b: str
    description: str = ""


class EmbodiedAgent:
    """A subject represented across exactly the seven closed-set views."""

    def __init__(self, subject_identity: str, provenance_boundary: str = "") -> None:
        if not isinstance(subject_identity, str) or not subject_identity:
            raise EmbodiedViewError("subject_identity must be a non-empty string")
        self.subject_identity = subject_identity
        self.provenance_boundary = provenance_boundary
        self._views: dict[str, EmbodiedViewProjection] = {}
        self._relations: list[CrossViewRelation] = []
        self._contradictions: list[Contradiction] = []
        self.autonomy_consent = "UNKNOWN"

    # --- API surface (implemented in Commit 2) -----------------------------
    def add_view(self, projection: EmbodiedViewProjection) -> None:  # pragma: no cover
        raise NotImplementedError("EmbodiedAgent.add_view implemented in Commit 2")

    def get_view(self, view_id: str) -> EmbodiedViewProjection:  # pragma: no cover
        raise NotImplementedError("EmbodiedAgent.get_view implemented in Commit 2")

    def missing_views(self) -> list[str]:  # pragma: no cover
        raise NotImplementedError("EmbodiedAgent.missing_views implemented in Commit 2")

    def assert_single_view_not_whole_person(self, view_id: str) -> None:  # pragma: no cover
        raise NotImplementedError(
            "EmbodiedAgent.assert_single_view_not_whole_person implemented in Commit 2"
        )

    def require_whole_person_disclosure(
        self,
        claimed_views: list[str],
        missing_disclosed: bool,
        contradictions_surfaced: bool,
    ) -> None:  # pragma: no cover
        raise NotImplementedError(
            "EmbodiedAgent.require_whole_person_disclosure implemented in Commit 2"
        )

    def add_cross_view_relation(self, relation: CrossViewRelation) -> None:  # pragma: no cover
        raise NotImplementedError(
            "EmbodiedAgent.add_cross_view_relation implemented in Commit 2"
        )

    def record_contradiction(self, contradiction: Contradiction) -> None:  # pragma: no cover
        raise NotImplementedError(
            "EmbodiedAgent.record_contradiction implemented in Commit 2"
        )

    def surface_contradictions(self) -> list[Contradiction]:  # pragma: no cover
        raise NotImplementedError(
            "EmbodiedAgent.surface_contradictions implemented in Commit 2"
        )


def embodied_view_closed_set_complete() -> bool:
    """The exact seven views must be present and no extras."""
    return (
        len(EMBODIED_VIEW_IDS) == 7
        and all(is_valid_embodied_view(v) for v in EMBODIED_VIEW_IDS)
    )
