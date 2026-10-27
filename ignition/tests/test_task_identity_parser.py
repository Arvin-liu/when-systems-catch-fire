from __future__ import annotations

from tools import task_identity, validate_task_identity_parser


def test_task_identity_fixtures_pass() -> None:
    assert validate_task_identity_parser.validate() == []


def test_standard_task_id_derives_ordinal() -> None:
    parsed = task_identity.parse_task_id("IGNITION-20260822-133")
    assert parsed["date"] == "2026-08-22"
    assert parsed["ordinal"] == 133


def test_architecture_task_may_differ_from_formal_task() -> None:
    assert task_identity.validate_binding_records([
        {"role_id": "current_formal_task", "task_id": "IGNITION-20260822-133"},
        {"role_id": "lifecycle_task", "task_id": "IGNITION-20260822-133"},
        {"role_id": "architecture_task", "task_id": "IGNITION-20260821-129"},
    ]) == []
