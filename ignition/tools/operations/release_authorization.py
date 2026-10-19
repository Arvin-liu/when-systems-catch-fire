"""Fail-closed review-state checks for component release authorization."""
from __future__ import annotations

from typing import Any


def latest_owner_review(reviews: list[dict[str, Any]], owner: str, head_sha: str) -> dict[str, Any] | None:
    """Return the latest Owner review event bound to this exact PR head."""
    matching = [
        review for review in reviews
        if review.get("user", {}).get("login", "").casefold() == owner.casefold()
        and review.get("commit_id") == head_sha
    ]
    if not matching:
        return None
    if any(not isinstance(review.get("id"), int) for review in matching):
        raise ValueError("Owner review evidence is missing a numeric GitHub review ID")
    return max(matching, key=lambda review: review["id"])


def owner_approval_is_current(reviews: list[dict[str, Any]], owner: str, head_sha: str) -> bool:
    latest = latest_owner_review(reviews, owner, head_sha)
    return latest is not None and latest.get("state") == "APPROVED"
