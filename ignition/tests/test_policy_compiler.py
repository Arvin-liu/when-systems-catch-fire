from __future__ import annotations

from dataclasses import replace
import unittest

from agent_runtime.policy_compiler import EffectivePolicy, MonotonicPolicyCompiler, PolicyCompileError, StalePolicyError


def source(name: str, *, caps: tuple[str, ...] = ("read.files", "write.files"), reads: tuple[str, ...] = ("src", "docs"), writes: tuple[str, ...] = ("out",), intents: tuple[str, ...] = ("READ_SHARED", "WRITE_EXCLUSIVE"), **extra: object) -> dict[str, object]:
    value: dict[str, object] = {
        "policy_ref": name,
        "allowed_capabilities": list(caps),
        "allowed_reads": list(reads),
        "allowed_writes": list(writes),
        "resource_intents": list(intents),
        "network_allowed": False,
        "device_allowed": False,
        "message_allowed": False,
        "remote_mutation_allowed": False,
        "approval_requirements": [],
        "forbidden_effects": [],
        "budget": {"max_actions": 10, "max_seconds": 30, "max_output_bytes": 1000},
        "expires_at": "2026-08-18T00:00:00Z",
    }
    value.update(extra)
    return value


class PolicyCompilerTests(unittest.TestCase):
    def inputs(self) -> dict[str, object]:
        return {
            "charter": source("charter", forbidden_effects=["owner_acceptance", "truth_authority"]),
            "workspace_policy": source("workspace", caps=("read.files", "write.files")),
            "agent_profile": source("profile", caps=("read.files", "write.files")),
            "task_envelope": source("task", caps=("read.files",), requested_capabilities=["read.files"], requested_reads=["src"], requested_writes=["out"], requested_resource_intents=["READ_SHARED"], task_id="task-1"),
            "pack_manifest": source("pack", caps=("read.files", "write.files")),
            "executor_ceiling": source("executor", caps=("read.files", "write.files")),
            "episode_budget": source("episode", caps=("read.files", "write.files"), budget={"max_actions": 4, "max_seconds": 12, "max_output_bytes": 400}),
            "approval_state": {},
            "route_ref": "executor.reference",
            "policy_id": "policy-1",
        }

    def test_intersection_digest_and_narrowing_trace(self) -> None:
        policy = MonotonicPolicyCompiler().compile(**self.inputs())
        self.assertEqual(policy.effective_capabilities, ("read.files",))
        self.assertEqual(policy.budget["max_actions"], 4)
        self.assertEqual(policy.network_allowed, False)
        self.assertGreaterEqual(len(policy.proof_trace), 10)
        self.assertEqual(len(policy.digest), 64)
        child = replace(policy, effective_capabilities=(), write_scope=(), budget={"max_actions": 1, "max_seconds": 5, "max_output_bytes": 100}, digest="child")
        self.assertTrue(MonotonicPolicyCompiler.is_narrower(policy, child))

    def test_escalation_denial_approval_and_stale_digest(self) -> None:
        compiler = MonotonicPolicyCompiler()
        inputs = self.inputs()
        inputs["task_envelope"] = source("task", caps=("read.files", "network"), requested_capabilities=["network"], requested_network=True, requested_reads=["src"], requested_writes=["out"], requested_resource_intents=["READ_SHARED"], task_id="task-1")
        with self.assertRaises(PolicyCompileError):
            compiler.compile(**inputs)
        inputs = self.inputs()
        inputs["approval_state"] = {"decision": "ALLOW", "requested_action_ref": "other-action", "approved_action_refs": ["other-action"]}
        with self.assertRaises(PolicyCompileError):
            compiler.compile(**inputs)
        policy = compiler.compile(**self.inputs())
        with self.assertRaises(StalePolicyError):
            policy.assert_digest("0" * 64)
        self.assertFalse(policy.permits(policy_digest=policy.digest, required_capabilities=("write.files",), reads=("src",)))

    def test_pack_or_executor_cannot_expand_parent(self) -> None:
        inputs = self.inputs()
        inputs["pack_manifest"] = source("pack", caps=("read.files", "write.files", "network"))
        with self.assertRaises(PolicyCompileError):
            MonotonicPolicyCompiler().compile(**inputs)


if __name__ == "__main__":
    unittest.main()
