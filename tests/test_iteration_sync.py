import copy

import pytest

from tools.validate_iteration_sync import validate_all, validate_custom


def test_iteration_sync_manifest_validates():
    result = validate_all()
    assert result["status"] == "PASS"
    assert result["checked"] >= 1


def test_current_draft_status_is_rejected():
    manifest = {
        "method_version": "1.0.0",
        "task_id": "BAD",
        "change_classification": ["OPERATIONS_METHOD"],
        "verified_start": {
            "main_head": "0" * 40,
            "source": "test",
            "verified_at": "2026-07-16",
        },
        "branch_pr": {
            "branch": "test",
            "pr_number": 1,
            "base": "main",
            "draft": True,
            "merged": False,
        },
        "gap": {
            "summary": "gap",
            "evidence": ["evidence"],
            "smallest_material_action": "action",
        },
        "claim_ceiling": "candidate_only",
        "status": {
            "candidate": True,
            "ready_for_gpt_verification": False,
            "accepted": False,
            "merged": False,
            "current": True,
        },
        "impact_matrix": [
            {"surface": surface, "decision": "CHANGE", "reason": "needed"}
            for surface in [
                "README.md",
                "docs/project-current-state.md",
                "AI-HANDOFF.md",
                "AI-START-HERE.md",
                "llms.txt",
                "SUMMARY.md",
                "CHANGELOG.md",
            ]
        ],
        "changed_surfaces": ["ITERATION.md", "tools/validate_iteration_sync.py"],
        "required_synchronization_decisions": ["README links to method"],
        "schema_tools_tests_workflows_reports_changed": ["tools/validate_iteration_sync.py"],
        "validation": {"local": [], "remote": []},
        "rollback_strategy": "close PR",
        "remaining_limitations": ["candidate only"],
        "receipt_location": "agent-results/BAD.md",
    }
    with pytest.raises(AssertionError, match="current cannot be true"):
        validate_custom(manifest, __file__)


def test_front_door_decision_is_required_for_operations_method():
    valid = {
        "method_version": "1.0.0",
        "task_id": "BAD2",
        "change_classification": ["OPERATIONS_METHOD"],
        "verified_start": {
            "main_head": "1" * 40,
            "source": "test",
            "verified_at": "2026-07-16",
        },
        "branch_pr": {
            "branch": "test",
            "pr_number": None,
            "base": "main",
            "draft": True,
            "merged": False,
        },
        "gap": {
            "summary": "gap",
            "evidence": ["evidence"],
            "smallest_material_action": "action",
        },
        "claim_ceiling": "candidate_only",
        "status": {
            "candidate": True,
            "ready_for_gpt_verification": False,
            "accepted": False,
            "merged": False,
            "current": False,
        },
        "impact_matrix": [
            {"surface": surface, "decision": "CHANGE", "reason": "needed"}
            for surface in [
                "README.md",
                "docs/project-current-state.md",
                "AI-HANDOFF.md",
                "AI-START-HERE.md",
                "llms.txt",
                "SUMMARY.md",
            ]
        ],
        "changed_surfaces": ["ITERATION.md", "tools/validate_iteration_sync.py"],
        "required_synchronization_decisions": ["README links to method"],
        "schema_tools_tests_workflows_reports_changed": ["tools/validate_iteration_sync.py"],
        "validation": {"local": [], "remote": []},
        "rollback_strategy": "close PR",
        "remaining_limitations": ["candidate only"],
        "receipt_location": "agent-results/BAD2.md",
    }
    missing = copy.deepcopy(valid)
    with pytest.raises(AssertionError, match="CHANGELOG.md"):
        validate_custom(missing, __file__)
