"""Fail-closed review-state checks for component release authorization."""
from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} is malformed") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def current_independent_approvals(
    reviews: list[dict[str, Any]], author: str, head_sha: str, merged_at: str,
) -> list[dict[str, Any]]:
    """Return exact-head non-author approvals that existed and were current at merge time."""
    if not isinstance(author, str) or not author.strip() or not isinstance(head_sha, str) or not head_sha:
        return []
    merge_time = _parse_timestamp(merged_at, "merged_at")
    matching: list[tuple[dict[str, Any], datetime]] = []
    for review in reviews:
        reviewer = review.get("user")
        login = reviewer.get("login") if isinstance(reviewer, dict) else None
        if not isinstance(login, str) or not login.strip():
            continue
        if (login.casefold() == author.casefold() or review.get("commit_id") != head_sha
                or review.get("state") not in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}):
            continue
        if not isinstance(review.get("id"), int) or isinstance(review.get("id"), bool) or review["id"] <= 0:
            raise ValueError("independent review evidence is missing a positive numeric GitHub review ID")
        matching.append((review, _parse_timestamp(review.get("submitted_at"), "review submitted_at")))
    if not matching:
        return []

    # Comments do not resolve an approval or a change request. Only a new
    # approval or an explicit dismissal changes that reviewer's decision.
    by_reviewer: dict[str, list[tuple[dict[str, Any], datetime]]] = {}
    for review, submitted_at in matching:
        login = review["user"]["login"].casefold()
        by_reviewer.setdefault(login, []).append((review, submitted_at))

    current_decisions = {
        login: max(events, key=lambda item: (item[1], item[0]["id"]))[0]
        for login, events in by_reviewer.items()
    }
    if any(review.get("state") == "CHANGES_REQUESTED" for review in current_decisions.values()):
        return []

    approvals = []
    for login, events in by_reviewer.items():
        before_merge = [item for item in events if item[1] < merge_time]
        if not before_merge:
            continue
        merge_decision = max(before_merge, key=lambda item: (item[1], item[0]["id"]))[0]
        if merge_decision.get("state") != "APPROVED":
            continue
        if current_decisions[login].get("state") != "DISMISSED":
            approvals.append(merge_decision)
    return sorted(approvals, key=lambda review: review["user"]["login"].casefold())


def independent_approval_is_current(reviews: list[dict[str, Any]], author: str, head_sha: str, merged_at: str) -> bool:
    return bool(current_independent_approvals(reviews, author, head_sha, merged_at))
