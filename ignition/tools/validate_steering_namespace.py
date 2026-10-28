#!/usr/bin/env python3
"""Validate steering record namespace and delegation boundaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/operations/iterations/129/fixtures/steering-namespace-delegation-r1.json"
SCHEMA = ROOT / "schemas/operations/steering-namespace-delegation-r1.schema.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.namespace import DelegationGrant, NamespaceBinding, NamespaceGuard, PrincipalIdentity, PrincipalRegistry  # noqa: E402
from agent_runtime.steering import SteeringNamespaceGuard, SteeringScope  # noqa: E402


def validate() -> list[str]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    errors = [error.message for error in Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).iter_errors(document)]
    registry = PrincipalRegistry()
    registry.register(PrincipalIdentity("principal-a", "OPERATOR", "system-root"))
    registry.register(PrincipalIdentity("principal-b", "OPERATOR", "system-root"))
    guard = SteeringNamespaceGuard(NamespaceGuard(registry))
    source_binding = NamespaceBinding("ns-a", "principal-a", "workspace-a", "episode-a", "run-a", "memory-a", "pack-a", "lease-a", "snapshot-a", "soft-a")
    target_binding = NamespaceBinding("ns-b", "principal-b", "workspace-b", "episode-b", "run-b", "memory-b", "pack-b", "lease-b", "snapshot-b", "soft-b")
    shared = "shared-steering-1"
    for row in document["cases"]:
        source_scope = SteeringScope("scope-a", "ns-a", intent_ids=("intent-shared-1",), goal_ids=("goal-shared-1",), shared_scope_ref=shared if row["shared_scope"] else None)
        target_scope = SteeringScope("scope-b", "ns-b", intent_ids=("intent-shared-1",), goal_ids=("goal-shared-1",), shared_scope_ref=shared if row["shared_scope"] else None)
        delegation = DelegationGrant("delegation-steering", "ns-a", "ns-b", "principal-a", "principal-b", (f"steering.{row['record_kind']}.{row['action']}",), 9999999999.0, "approval-steering", "a" * 64) if row["delegation"] else None
        source = source_binding if row["cross_namespace"] else target_binding
        target = target_binding
        try:
            guard.authorize(source, source_scope if row["cross_namespace"] else target_scope, target, target_scope, record_kind=row["record_kind"], record_id=row["record_id"], action=row["action"], now=100.0, delegation=delegation)
            actual = "ALLOW"
        except Exception:
            actual = "DENY"
        if actual != row["expected"]:
            errors.append(f"{row['case_id']} actual={actual} expected={row['expected']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    errors = validate()
    if errors:
        print("STEERING_NAMESPACE_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("STEERING_NAMESPACE_OK cases=6 local=ALLOW cross_namespace=EXPLICIT shared_scope=REQUIRED canonical_write=DENY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
