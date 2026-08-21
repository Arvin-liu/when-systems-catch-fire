from __future__ import annotations

from tools import validate_iteration_boundary_semantics


def test_iteration_boundary_semantics_model_is_explicit_and_valid() -> None:
    assert validate_iteration_boundary_semantics.validate() == []


def test_compatibility_alias_is_not_an_independent_ordinal() -> None:
    model = validate_iteration_boundary_semantics.load_json(validate_iteration_boundary_semantics.MODEL_PATH)
    alias = model["fields"]["current_iteration_boundary"]
    assert alias["status"] == "DEPRECATED_COMPATIBILITY_ALIAS"
    assert alias["source_role"] == "current_formal_task_ordinal"
    assert alias["must_equal"] == "current_formal_task_ordinal"


def test_formal_and_architecture_roles_are_allowed_to_differ() -> None:
    model = validate_iteration_boundary_semantics.load_json(validate_iteration_boundary_semantics.MODEL_PATH)
    assert model["separation"]["formal_and_architecture_ordinals_are_independent"] is True
    assert model["separation"]["equality_required"] is False
