from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from agent_kernel import AgentProfile
from agent_runtime.profile import ProfileProjectionError, load_profile_registry, project_profile, select_packs
from agent_runtime.r1_runtime import R1RunSpec
from agent_runtime.supervisor import ChildRunSpec, EpisodeBudget, EpisodeSpec, Supervisor
from tests.test_supervisor import packet
from agent_runtime.actions import ActionKind, ApprovalClass, RollbackClass, WorkspacePolicy
from agent_runtime.transport import action_plan_hash


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data/agent-runtime/agent-profiles-r1.json"


def spec(root: Path, run_id: str, *, capability: str = "write.files", action_kind: str = ActionKind.WRITE_FILE.value) -> R1RunSpec:
    p = packet(run_id, f"action-{run_id}", f"{run_id}.txt")
    if action_kind != ActionKind.WRITE_FILE.value:
        raise AssertionError("profile tests currently use the shared bounded write fixture")
    return R1RunSpec(
        run_id=run_id,
        profile_ref="human-surface-writer",
        goal={"statement": "project profile into a bounded run", "success_conditions": ["typed"], "prohibited_actions": ["network"]},
        workspace=WorkspacePolicy(str(root), (".",), (".",), (), max_actions=8, max_writes=8, max_output_bytes=65536),
        capability_scope={"scope_id": f"scope-{run_id}", "allowed_capabilities": ["read.files", capability], "network_allowed": False},
        actions=(p,),
        reasoner={"type": "scripted"},
        executor={"type": "local_workspace", "class_id": "local-workspace-executor"},
        validator={"type": "command_exit"},
        lease_ttl_seconds=10,
        fault_injection={},
    )


class AgentProfileR1Tests(unittest.TestCase):
    def test_registry_has_three_capability_profiles_and_pack_selection_is_bounded(self) -> None:
        profiles = load_profile_registry(PROFILE_PATH)
        self.assertEqual(set(profiles), {"repository-maintainer", "bounded-researcher", "human-surface-writer"})
        self.assertEqual(select_packs(profiles["bounded-researcher"], ("research.reos-light", "knowledge.r0")), ("knowledge.r0", "research.reos-light"))
        with self.assertRaises(ProfileProjectionError):
            select_packs(profiles["bounded-researcher"], ("maintenance.repository",))

    def test_projection_narrows_scope_and_strengthens_approval(self) -> None:
        profiles = load_profile_registry(PROFILE_PATH)
        with tempfile.TemporaryDirectory(prefix="profile-projection-") as temp:
            projected, receipt = project_profile(profiles["human-surface-writer"], spec(Path(temp), "run-profile"))
            self.assertEqual(projected.profile_ref, "human-surface-writer")
            self.assertEqual(projected.capability_scope["allowed_capabilities"], ["read.files", "write.files"])
            self.assertEqual(projected.actions[0].approval_class, ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value)
            self.assertEqual(projected.actions[0].source_plan_hash, action_plan_hash(projected.actions))
            self.assertEqual(receipt.allowed_packs, ("knowledge.r0", "writing.zhiyuan"))
            self.assertLessEqual(projected.workspace.max_actions, 10)

    def test_profile_cannot_expand_a_researcher_into_a_writer(self) -> None:
        profiles = load_profile_registry(PROFILE_PATH)
        with tempfile.TemporaryDirectory(prefix="profile-negative-") as temp:
            with self.assertRaises(ProfileProjectionError):
                project_profile(profiles["bounded-researcher"], spec(Path(temp), "run-write"))

    def test_profile_projection_drives_supervisor_approval(self) -> None:
        profiles = load_profile_registry(PROFILE_PATH)
        with tempfile.TemporaryDirectory(prefix="profile-supervisor-") as temp:
            root = Path(temp)
            run = spec(root, "run-profile")
            episode = EpisodeSpec(
                episode_id="episode-profile", job_id="job-profile", created_by="test-owner",
                capability_scope_id="episode-scope", allowed_capabilities=("read.files", "write.files"),
                budget=EpisodeBudget(max_actions=4, max_seconds=30, max_output_bytes=4096),
                children=(ChildRunSpec(run_id=run.run_id, run_spec=run),),
            )
            supervisor = Supervisor(root / "episode")
            first = supervisor.start(episode, profiles=profiles)
            self.assertEqual(first["profile_refs"]["run-profile"], "human-surface-writer")
            self.assertEqual(first["terminal"]["state"], "EPISODE_WAITING_FOR_APPROVAL")
            pending = Supervisor(root / "episode").pending_approvals()[0]
            final = Supervisor(root / "episode").approve("run-profile", pending["request_id"], "allow", authority_id="owner-1")
            self.assertEqual(final["terminal"]["state"], "EPISODE_COMPLETED_VALIDATED")

    def test_legacy_r0_profile_remains_parseable_without_personality_fields(self) -> None:
        raw = __import__("json").loads((ROOT / "data/agent-runtime/agent-profile-r0.json").read_text(encoding="utf-8"))
        profile = AgentProfile.from_dict(raw)
        self.assertTrue(profile.prohibited_self_escalation)
        self.assertFalse(hasattr(profile, "personality"))


if __name__ == "__main__":
    unittest.main()
