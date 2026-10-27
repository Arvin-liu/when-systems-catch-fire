#!/usr/bin/env python3
"""Deterministic parsing and binding checks for formal task identities."""

from __future__ import annotations

import datetime as _datetime
import re
from typing import Any, Iterable


TASK_ID_PATTERN = re.compile(r"^IGNITION-(?P<date>\d{8})-(?P<ordinal>\d{3})$")


class TaskIdentityError(ValueError):
    """Raised when a task identity is malformed or internally inconsistent."""


def parse_task_id(task_id: str) -> dict[str, Any]:
    """Parse one strict `IGNITION-YYYYMMDD-NNN` task id.

    The parser intentionally rejects the older undated shorthand and any
    widened or ambiguous ordinal form. It never consults prose, Git metadata,
    branch names, or a task title.
    """

    if not isinstance(task_id, str):
        raise TaskIdentityError("task id must be a string")
    match = TASK_ID_PATTERN.fullmatch(task_id)
    if not match:
        raise TaskIdentityError("task id must match IGNITION-YYYYMMDD-NNN exactly")
    compact_date = match.group("date")
    try:
        date_value = _datetime.date(
            int(compact_date[0:4]),
            int(compact_date[4:6]),
            int(compact_date[6:8]),
        )
    except ValueError as exc:
        raise TaskIdentityError(f"task id contains invalid calendar date: {compact_date}") from exc
    ordinal_text = match.group("ordinal")
    ordinal = int(ordinal_text)
    if ordinal < 1:
        raise TaskIdentityError("task ordinal must be positive")
    return {
        "canonical": task_id,
        "date": date_value.isoformat(),
        "date_compact": compact_date,
        "ordinal": ordinal,
        "ordinal_text": ordinal_text,
    }


def validate_declared_identity(
    task_id: str,
    *,
    declared_date: str | None = None,
    declared_ordinal: int | None = None,
) -> list[str]:
    """Validate optional independently supplied identity assertions."""

    try:
        parsed = parse_task_id(task_id)
    except TaskIdentityError as exc:
        return [str(exc)]
    errors: list[str] = []
    if declared_date is not None and declared_date not in {parsed["date"], parsed["date_compact"]}:
        errors.append(f"declared date {declared_date!r} differs from task id date {parsed['date']!r}")
    if declared_ordinal is not None and declared_ordinal != parsed["ordinal"]:
        errors.append(f"declared ordinal {declared_ordinal!r} differs from task id ordinal {parsed['ordinal']!r}")
    return errors


def validate_binding_records(records: Iterable[dict[str, Any]]) -> list[str]:
    """Validate a set of role-labelled task identity records.

    Role labels must be unique. Formal/lifecycle/execution-contract records
    must bind to the same canonical task id when present. Architecture is a
    separate role and is explicitly allowed to differ.
    """

    errors: list[str] = []
    seen_roles: set[str] = set()
    parsed_by_role: dict[str, dict[str, Any]] = {}
    for record in records:
        role = record.get("role_id")
        if not isinstance(role, str) or not role:
            errors.append("binding record role_id must be a non-empty string")
            continue
        if role in seen_roles:
            errors.append(f"duplicate binding role: {role}")
            continue
        seen_roles.add(role)
        task_id = record.get("task_id")
        try:
            parsed_by_role[role] = parse_task_id(task_id)
        except TaskIdentityError as exc:
            errors.append(f"{role}: {exc}")
            continue
        errors.extend(
            f"{role}: {error}"
            for error in validate_declared_identity(
                task_id,
                declared_date=record.get("declared_date"),
                declared_ordinal=record.get("declared_ordinal"),
            )
        )

    same_task_roles = ("current_formal_task", "lifecycle_task", "execution_contract_task")
    available = [parsed_by_role[role] for role in same_task_roles if role in parsed_by_role]
    if available and any(item["canonical"] != available[0]["canonical"] for item in available[1:]):
        errors.append("formal task identity bindings must be identical")
    return errors

