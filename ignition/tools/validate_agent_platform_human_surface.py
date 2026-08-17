#!/usr/bin/env python3
"""Validate the current Agent Platform/Federation human/AI surface projection.

This is a read-only navigation and wording gate.  It does not adjudicate
truth, causality, prose quality, Owner acceptance, or external validity.
"""

from __future__ import annotations

import json
from pathlib import Path


# ``ignition`` is the application root; the formal worktree also owns
# ``.github/`` one level above it.
ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent

SURFACE_RULES = {
    "AGENTS.md": (
        "Agent Platform R2",
        "Knowledge Governance is its first large",
        "Kernel ≠ Knowledge",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    ".github/README.md": (
        "Agent Platform R2",
        "第一个大型 Domain Pack",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    "ignition/AI-START-HERE.md": (
        "Agent Platform",
        "Domain Pack",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    "ignition/AI-HANDOFF.md": (
        "Agent Platform R2",
        "Reasoner ≠ Executor",
        "EPISTEMICALLY_ACCEPTED",
    ),
    "ignition/ARCHITECTURE.md": (
        "Agent Platform R2",
        "91",
        "79",
        "84",
        "79",
        "12",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    "ignition/llms.txt": (
        "Agent Platform R2",
        "bounded, auditable and recoverable Agent Platform prototype",
        "not general intelligence",
    ),
    "ignition/docs/project-current-state.md": (
        "Task 121 current Agent Platform R2 spine",
        "第一个大型 Domain Pack",
        "EPISTEMICALLY_ACCEPTED",
    ),
    "ignition/HUMAN-READING.md": (
        "Agent Platform R2",
        "第一个大型 Domain Pack",
        "EPISTEMICALLY_ACCEPTED",
    ),
    "ignition/RESULTS/LATEST.md": (
        "Agent Platform R2",
        "第一个大型 Domain Pack",
        "EPISTEMICALLY_ACCEPTED",
    ),
    "ignition/PUBLICATIONS/pointfire-results-book/09-正式仓库最新成果.md": (
        "Agent Platform R2",
        "第一个大型 Domain Pack",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    "ignition/docs/architecture/agent-platform-r2.md": (
        "Agent Platform R2",
        "有界、可审计、可恢复的 Agent Platform 原型",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    "ignition/docs/architecture/external-agent-federation-r1.md": (
        "External Agent Federation R1",
        "Reference Executor freeze",
        "NOT_RUN_LIVE_EXTERNAL_INVOCATION",
        "agent_platform.federation",
    ),
    "ignition/agent_kernel/README.md": (
        "Agent Platform R2",
        "KERNEL_NON_ESCALATION",
    ),
    "ignition/agent_runtime/README.md": (
        "Agent Platform Runtime R0 / R1 with R2 coordination",
        "EXPERIMENTAL_AGENT_PLATFORM_R2_WITH_OPEN_OBLIGATIONS",
        "EPISTEMICALLY_ACCEPTED=0",
    ),
    "ignition/packs/knowledge/README.md": (
        "Knowledge Domain Pack",
        "不是 Generic Kernel 的内容",
        "source admission",
    ),
    "ignition/packs/research/README.md": (
        "REOS LIGHT",
        "Pack-aware proposal/validation",
        "EPISTEMICALLY_ACCEPTED",
    ),
    "ignition/packs/writing/README.md": (
        "之元写作法 0.5.0",
        "Agent Platform R2",
        "epistemic status",
    ),
    "ignition/packs/maintenance/README.md": (
        "Repository Maintenance Pack",
        "R2 night-shift fixture",
        "network_allowed=false",
    ),
}

PRIVATE_MARKERS = ("/Users/", "/home/", "file://", "PRIVATE_PROVENANCE")


def _path(relative: str) -> Path:
    if relative.startswith(".github/"):
        return REPO_ROOT / relative
    if relative == "AGENTS.md":
        return REPO_ROOT / relative
    if relative.startswith("ignition/"):
        return ROOT / relative.removeprefix("ignition/")
    return ROOT / relative


def validate() -> list[str]:
    issues: list[str] = []

    for relative, required in SURFACE_RULES.items():
        path = _path(relative)
        if not path.is_file():
            issues.append(f"missing surface: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        for marker in required:
            if marker not in content:
                issues.append(f"{relative}: missing required marker {marker!r}")
        if any(marker in content for marker in PRIVATE_MARKERS):
            issues.append(f"{relative}: private provenance marker/path leaked")

    map_path = ROOT / "data/architecture/interactive-system-map.json"
    try:
        system_map = json.loads(map_path.read_text(encoding="utf-8"))
        coverage = system_map["component_coverage"]
        expected_coverage = {
            "registry_components": 91,
            "visible_nodes": 79,
            "hidden_components": 12,
        }
        for key, expected in expected_coverage.items():
            if coverage.get(key) != expected:
                issues.append(f"system map coverage {key}={coverage.get(key)!r}, expected {expected!r}")
        if system_map.get("map_version") != "0.9.0":
            issues.append(f"system map version is {system_map.get('map_version')!r}, expected '0.9.0'")
        if len(system_map.get("edges", [])) != 84:
            issues.append(f"system map edge count is {len(system_map.get('edges', []))}, expected 84")
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        issues.append(f"system map cannot be read: {exc}")

    changelog = ROOT / "STATE-CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8") if changelog.is_file() else ""
    for marker in (
        "IGNITION-20260816-121-AGENT-PLATFORM-R2-NIGHT-SHIFT-PRE-RELEASE",
        "task-branch pre-release projection",
        "Step 11 adversarial/full regression",
        "Step 12 fresh-clone replay",
        "main merge receipt",
        "IGNITION-20260816-123",
        "CURRENT_STATE_SYNC_INVARIANT",
    ):
        if marker not in changelog_text:
            issues.append(f"STATE-CHANGELOG.md: missing pre-release marker {marker!r}")

    manifests = {
        "knowledge": ("knowledge.r0", "knowledge.read_foundation"),
        "research": ("research.reos-light", "research.coordinate_obligations"),
        "writing": ("writing.zhiyuan", "writing.apply_editorial_method"),
        "maintenance": ("maintenance.repository", "maintenance.inspect_repository"),
    }
    for pack, (pack_id, capability) in manifests.items():
        path = ROOT / "packs" / pack / "manifest.json"
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"pack {pack}: manifest cannot be read: {exc}")
            continue
        if manifest.get("pack_id") != pack_id:
            issues.append(f"pack {pack}: pack_id={manifest.get('pack_id')!r}, expected {pack_id!r}")
        if capability not in manifest.get("capabilities_provided", []):
            issues.append(f"pack {pack}: missing capability {capability!r}")
        if "runtime.pack_registry" not in manifest.get("required_runtime_capabilities", []):
            issues.append(f"pack {pack}: missing runtime.pack_registry requirement")
        if "runtime.pack_bus" not in manifest.get("required_runtime_capabilities", []):
            issues.append(f"pack {pack}: missing runtime.pack_bus requirement")

    return issues


def main() -> int:
    issues = validate()
    if issues:
        print("AGENT_PLATFORM_HUMAN_SURFACE=FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(
        "AGENT_PLATFORM_HUMAN_SURFACE=PASS "
        f"surfaces={len(SURFACE_RULES)} map=0.9.0 registry=91 "
        "visible=79 edges=84 hidden=12 packs=4"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
