# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Embodied-agent multi-view projection contract (R5-A, implemented Commit 2).

Design contract (task §6, §5.1):
  * all seven views carry the same subject identity and provenance boundary;
  * each view has observations, confidence, time scope and UNKNOWN fields;
  * cross-view relations are typed and do NOT imply causality;
  * contradictory views may coexist and must be surfaced;
  * the subject has autonomy/consent fields not reducible to a view score;
  * representation never claims to exhaust the person;
  * a single view, score, diagnosis, behavior or self-report may NEVER assert
    WHOLE_PERSON_COMPLETE.
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

    # --- Implemented in Commit 2 -------------------------------------------
    def add_view(self, projection: EmbodiedViewProjection) -> None:
        if projection.subject_identity != self.subject_identity:
            raise EmbodiedViewError(
                "view subject_identity must match the agent subject_identity"
            )
        if not is_valid_embodied_view(projection.view_id):
            raise EmbodiedViewError(f"unknown embodied view id: {projection.view_id!r}")
        self._views[projection.view_id] = projection

    def get_view(self, view_id: str) -> EmbodiedViewProjection:
        if view_id not in self._views:
            raise MissingViewError(f"view not present: {view_id!r}")
        return self._views[view_id]

    def missing_views(self) -> list[str]:
        """Views not yet provided are treated as UNKNOWN / NOT_OBSERVED and must
        not be inferred from any other view."""
        return [v for v in EMBODIED_VIEW_IDS if v not in self._views]

    def assert_single_view_not_whole_person(self, view_id: str) -> None:
        """A single view can NEVER claim the whole person. This always refuses:
        a projection is a partial view of one subject, not a complete subject."""
        if view_id not in self._views and view_id not in EMBODIED_VIEW_IDS:
            raise EmbodiedViewError(f"unknown embodied view id: {view_id!r}")
        raise WholePersonClaimError(
            f"single view {view_id!r} may not assert WHOLE_PERSON_COMPLETE"
        )

    def require_whole_person_disclosure(
        self,
        claimed_views: list[str],
        missing_disclosed: bool,
        contradictions_surfaced: bool,
    ) -> None:
        """A whole-person conclusion requires explicit view coverage, missing-view
        disclosure as UNKNOWN, and contradiction/UNKNOWN handling. Anything less
        fails closed."""
        for v in claimed_views:
            if v not in self._views:
                raise MissingViewError(f"claimed view not present: {v!r}")
        if not (missing_disclosed and contradictions_surfaced):
            raise WholePersonClaimError(
                "whole-person conclusion requires missing-view disclosure and "
                "contradiction/UNKNOWN handling"
            )

    def add_cross_view_relation(self, relation: CrossViewRelation) -> None:
        if relation.asserts_causality:
            raise CrossViewCausalityError(
                "cross-view relations are typed and must not imply causality"
            )
        if not is_valid_embodied_view(relation.source_view):
            raise EmbodiedViewError(f"unknown source view: {relation.source_view!r}")
        if not is_valid_embodied_view(relation.target_view):
            raise EmbodiedViewError(f"unknown target view: {relation.target_view!r}")
        self._relations.append(relation)

    def record_contradiction(self, contradiction: Contradiction) -> None:
        if not is_valid_embodied_view(contradiction.view_a):
            raise EmbodiedViewError(f"unknown view: {contradiction.view_a!r}")
        if not is_valid_embodied_view(contradiction.view_b):
            raise EmbodiedViewError(f"unknown view: {contradiction.view_b!r}")
        self._contradictions.append(contradiction)

    def surface_contradictions(self) -> list[Contradiction]:
        """Contradictory views are preserved and surfaced, never silently merged."""
        return list(self._contradictions)


def embodied_view_closed_set_complete() -> bool:
    """The exact seven views must be present and no extras."""
    return (
        len(EMBODIED_VIEW_IDS) == 7
        and all(is_valid_embodied_view(v) for v in EMBODIED_VIEW_IDS)
    )
