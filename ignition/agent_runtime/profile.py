"""Agent Profile R1 projection into bounded runtime and Supervisor inputs."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_kernel import AgentProfile

from .actions import ApprovalClass, ExecutionPacket
from .r1_runtime import R1RunSpec
from .transport import action_plan_hash


class ProfileProjectionError(ValueError):
    """Raised when a profile cannot legally project a requested run."""


_APPROVAL_RANK = {
    ApprovalClass.AUTO_ALLOWED_SAFE.value: 0,
    ApprovalClass.BOUNDED_WRITE_REQUIRES_APPROVAL.value: 1,
    ApprovalClass.COMMAND_REQUIRES_APPROVAL.value: 2,
    ApprovalClass.DESTRUCTIVE_NOT_AVAILABLE_R1.value: 3,
}


@dataclass(frozen=True)
class ProfileProjection:
    stable_agent_id: str
    role: str
    effective_capabilities: tuple[str, ...]
    allowed_packs: tuple[str, ...]
    preferred_tool_classes: tuple[str, ...]
    forbidden_tool_classes: tuple[str, ...]
    approval_thresholds: dict[str, str]
    budget_defaults: dict[str, int | float]
    memory_policy: str
    update_authority: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "stable_agent_id": self.stable_agent_id,
            "role": self.role,
            "effective_capabilities": list(self.effective_capabilities),
            "allowed_packs": list(self.allowed_packs),
            "preferred_tool_classes": list(self.preferred_tool_classes),
            "forbidden_tool_classes": list(self.forbidden_tool_classes),
            "approval_thresholds": dict(self.approval_thresholds),
            "budget_defaults": dict(self.budget_defaults),
            "memory_policy": self.memory_policy,
            "update_authority": self.update_authority,
        }


def _scope_projection(profile: AgentProfile, declared_scope: Mapping[str, Any]) -> dict[str, Any]:
    required = {"scope_id", "allowed_capabilities", "network_allowed"}
    if set(declared_scope) != required:
        raise ProfileProjectionError("declared capability scope has an invalid shape")
    declared = tuple(str(item) for item in declared_scope["allowed_capabilities"])
    if not declared:
        raise ProfileProjectionError("declared capability scope must not be empty")
    if declared_scope["network_allowed"] is not False:
        raise ProfileProjectionError("profile projection cannot enable network")
    effective = tuple(sorted(set(declared) & set(profile.allowed_capability_classes)))
    if not effective:
        raise ProfileProjectionError("profile narrows the declared scope to no usable capability")
    return {
        "scope_id": declared_scope["scope_id"],
        "allowed_capabilities": list(effective),
        "network_allowed": False,
    }


def _profile_threshold(profile: AgentProfile, packet: ExecutionPacket) -> str:
    thresholds = profile.approval_threshold_map
    required = packet.approval_class
    for key in (*packet.required_capabilities, packet.kind):
        candidate = thresholds.get(key)
        if candidate and _APPROVAL_RANK[candidate] > _APPROVAL_RANK[required]:
            required = candidate
    if required == ApprovalClass.DESTRUCTIVE_NOT_AVAILABLE_R1.value:
        raise ProfileProjectionError("profile threshold requests an unavailable destructive approval class")
    return required


def project_profile(profile: AgentProfile, spec: R1RunSpec) -> tuple[R1RunSpec, ProfileProjection]:
    """Return a legal narrowed R1 spec and a public projection receipt.

    A profile never adds a capability, pack, write root, executable, network
    permission or Charter authority. Approval thresholds may only move an
    action toward a stronger typed approval class.
    """

    scope = _scope_projection(profile, spec.capability_scope)
    effective = set(scope["allowed_capabilities"])
    projected_packets: list[ExecutionPacket] = []
    for packet in spec.actions:
        missing = sorted(set(packet.required_capabilities) - effective)
        if missing:
            raise ProfileProjectionError(f"profile {profile.stable_agent_id} cannot run {packet.action_id}; capabilities narrowed out: {missing}")
        forbidden = sorted((set(packet.required_capabilities) | {packet.kind}) & set(profile.forbidden_tool_classes))
        if forbidden:
            raise ProfileProjectionError(f"profile forbids tool classes for {packet.action_id}: {forbidden}")
        if packet.network_requested:
            raise ProfileProjectionError("profile projection cannot authorize a network action")
        projected_packets.append(replace(packet, approval_class=_profile_threshold(profile, packet)))

    if projected_packets:
        plan_digest = action_plan_hash(projected_packets)
        projected_packets = [replace(packet, source_plan_hash=plan_digest) for packet in projected_packets]

    workspace = spec.workspace
    defaults = profile.budget_default_map
    workspace_changes: dict[str, Any] = {}
    for key in ("max_actions", "max_output_bytes", "max_writes"):
        if key in defaults:
            workspace_changes[key] = min(getattr(workspace, key), int(defaults[key]))
    try:
        narrowed_workspace = replace(workspace, **workspace_changes) if workspace_changes else workspace
        projected_spec = replace(
            spec,
            profile_ref=profile.stable_agent_id,
            capability_scope=scope,
            workspace=narrowed_workspace,
            actions=tuple(projected_packets),
        )
    except (TypeError, ValueError) as exc:
        raise ProfileProjectionError(f"profile projection produced an invalid narrowed R1 spec: {exc}") from exc
    return projected_spec, ProfileProjection(
        stable_agent_id=profile.stable_agent_id,
        role=profile.role,
        effective_capabilities=tuple(scope["allowed_capabilities"]),
        allowed_packs=profile.allowed_packs,
        preferred_tool_classes=profile.preferred_tool_classes,
        forbidden_tool_classes=profile.forbidden_tool_classes,
        approval_thresholds=profile.approval_threshold_map,
        budget_defaults=profile.budget_default_map,
        memory_policy=profile.memory_policy,
        update_authority=profile.update_authority,
    )


def select_packs(
    profile: AgentProfile,
    available_pack_ids: Sequence[str],
    requested_pack_ids: Sequence[str] = (),
) -> tuple[str, ...]:
    """Select only declared profile-allowed packs; never infer more authority."""

    available = set(str(item) for item in available_pack_ids)
    requested = set(str(item) for item in requested_pack_ids)
    if not requested:
        requested = set(profile.allowed_packs)
    disallowed = sorted(requested - set(profile.allowed_packs))
    unavailable = sorted(requested - available)
    if disallowed:
        raise ProfileProjectionError(f"requested packs are outside profile allowlist: {disallowed}")
    if unavailable:
        raise ProfileProjectionError(f"requested packs are not available: {unavailable}")
    return tuple(sorted(requested))


def load_profile_registry(path: str | Path) -> dict[str, AgentProfile]:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileProjectionError(f"profile registry is unreadable: {exc}") from exc
    raw_profiles = data.get("profiles") if isinstance(data, Mapping) else data
    if not isinstance(raw_profiles, list):
        raise ProfileProjectionError("profile registry must contain a profiles array")
    profiles: dict[str, AgentProfile] = {}
    for raw in raw_profiles:
        profile = AgentProfile.from_dict(raw)
        if profile.stable_agent_id in profiles:
            raise ProfileProjectionError(f"duplicate profile: {profile.stable_agent_id}")
        profiles[profile.stable_agent_id] = profile
    if not profiles:
        raise ProfileProjectionError("profile registry must not be empty")
    return profiles


def apply_profiles_to_episode(episode: Any, profiles: Mapping[str, AgentProfile]) -> Any:
    """Project each child using the profile named by its R1 ``profile_ref``."""

    projected_children = []
    receipts = []
    for child in episode.children:
        profile = profiles.get(child.run_spec.profile_ref)
        if profile is None:
            raise ProfileProjectionError(f"no profile is registered for child {child.run_id}: {child.run_spec.profile_ref}")
        projected_spec, receipt = project_profile(profile, child.run_spec)
        projected_children.append(replace(child, run_spec=projected_spec))
        receipts.append(receipt.to_dict())
    return replace(episode, children=tuple(projected_children))


__all__ = [
    "ProfileProjection",
    "ProfileProjectionError",
    "apply_profiles_to_episode",
    "load_profile_registry",
    "project_profile",
    "select_packs",
]
