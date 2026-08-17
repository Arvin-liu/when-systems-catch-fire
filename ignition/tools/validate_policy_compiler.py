#!/usr/bin/env python3
"""Negative and monotonicity gate for Effective Policy R1."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_runtime.policy_compiler import MonotonicPolicyCompiler, PolicyCompileError
from tests.test_policy_compiler import PolicyCompilerTests


def main() -> int:
    fixture = PolicyCompilerTests().inputs()
    compiler = MonotonicPolicyCompiler()
    policy = compiler.compile(**fixture)
    child_fixture = dict(fixture)
    child_fixture["task_envelope"] = dict(fixture["task_envelope"], requested_capabilities=["read.files"], requested_reads=["src"], requested_writes=[], requested_resource_intents=["READ_SHARED"])
    child_fixture.update(policy_id="policy-child", route_ref="executor.reference.v2")
    child = compiler.compile(**child_fixture)
    narrow = compiler.is_narrower(policy, child)
    fixture["pack_manifest"] = dict(fixture["pack_manifest"], allowed_capabilities=["read.files", "write.files", "network"])
    try:
        compiler.compile(**fixture)
    except PolicyCompileError:
        pack_escalation = True
    else:
        pack_escalation = False
    print(f"MONOTONIC_POLICY_R1={'PASS' if narrow and pack_escalation else 'FAIL'}")
    print(f"CHILD_POLICY_NARROWER={'PASS' if narrow else 'FAIL'}")
    print(f"PACK_ESCALATION={'REJECTED' if pack_escalation else 'ACCEPTED'}")
    print(f"POLICY_DIGEST={policy.digest}")
    return 0 if narrow and pack_escalation else 1


if __name__ == "__main__":
    raise SystemExit(main())
