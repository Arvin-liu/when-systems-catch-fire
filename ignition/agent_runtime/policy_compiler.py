"""Monotonic, provider-neutral Effective Policy compilation for R2.

Every input is treated as a ceiling or a requested subset.  Compilation can
only intersect sets, take the minimum of budgets/expiry, and union stronger
prohibitions.  An external approval can satisfy an already declared approval
requirement; it cannot manufacture a capability or override an OS denial.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Mapping, Sequence

from agent_kernel.contracts import _id, sha256_json


POLICY_SCHEMA = "os-control-plane-effective-policy-r1"
POLICY_SOURCES = (
    "charter",
    "workspace_policy",
    "agent_profile",
    "task_envelope",
    "pack_manifest",
    "executor_ceiling",
    "episode_budget",
)
BOOLEAN_DIMENSIONS = ("network", "device", "message", "remote_mutation")
FORBIDDEN_ALWAYS = frozenset({"owner_acceptance", "truth_authority", "epistemic_upgrade", "hidden_reasoning"})


class PolicyCompileError(ValueError):
    """Raised when a policy composition would be ambiguous or widening."""


class StalePolicyError(PolicyCompileError):
    """Raised when an action presents an old policy digest."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise PolicyCompileError(f"{field} must be a mapping")
    return value


def _set(source: Mapping[str, Any], *keys: str) -> set[str] | None:
    for key in keys:
        if key in source:
            value = source[key]
            if isinstance(value, str) or not isinstance(value, Sequence):
                raise PolicyCompileError(f"{key} must be an array of strings")
            result = {item for item in value if isinstance(item, str) and item}
            if len(result) != len(value):
                raise PolicyCompileError(f"{key} must contain only non-empty strings")
            return result
    return None


def _bool(source: Mapping[str, Any], *keys: str, default: bool | None = None) -> bool | None:
    for key in keys:
        if key in source:
            value = source[key]
            if not isinstance(value, bool):
                raise PolicyCompileError(f"{key} must be boolean")
            return value
    return default


def _budget(source: Mapping[str, Any]) -> dict[str, float | int] | None:
    raw = source.get("budget")
    if raw is None and any(key in source for key in ("max_actions", "max_seconds", "max_output_bytes")):
        raw = {key: source[key] for key in ("max_actions", "max_seconds", "max_output_bytes") if key in source}
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise PolicyCompileError("budget must be a mapping")
    result: dict[str, float | int] = {}
    for key in ("max_actions", "max_seconds", "max_output_bytes"):
        if key in raw:
            value = raw[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise PolicyCompileError(f"budget.{key} must be positive")
            result[key] = value
    if not result:
        raise PolicyCompileError("budget must declare at least one positive ceiling")
    return result


def _expiry(source: Mapping[str, Any]) -> str | None:
    value = source.get("expires_at", source.get("expiry"))
    if value is None:
        return None
    if not isinstance(value, str):
        raise PolicyCompileError("expires_at must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PolicyCompileError("expires_at must be an ISO-8601 string") from exc
    if parsed.tzinfo is None:
        raise PolicyCompileError("expires_at must include a timezone")
    return value


def _ref(source: Mapping[str, Any], fallback: str) -> str:
    for key in ("policy_ref", "profile_ref", "pack_id", "executor_id", "scope_id", "source_ref", "id"):
        value = source.get(key)
        if isinstance(value, str) and value:
            return value
    return fallback


def _path_allowed(path: str, patterns: set[str]) -> bool:
    return path in patterns or any(pattern.endswith("/*") and path.startswith(pattern[:-1]) for pattern in patterns)


@dataclass(frozen=True)
class EffectivePolicy:
    """The only authority artifact accepted by the R2 action boundary."""

    policy_id: str
    route_ref: str
    effective_capabilities: tuple[str, ...]
    read_scope: tuple[str, ...]
    write_scope: tuple[str, ...]
    network_allowed: bool
    device_allowed: bool
    message_allowed: bool
    remote_mutation_allowed: bool
    resource_intents: tuple[str, ...]
    approval_requirements: tuple[str, ...]
    approval_satisfied: bool
    budget: Mapping[str, float | int]
    forbidden_effects: tuple[str, ...]
    expires_at: str | None
    source_policy_refs: tuple[str, ...]
    proof_trace: tuple[Mapping[str, Any], ...]
    digest: str

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "schema": POLICY_SCHEMA,
            "policy_id": self.policy_id,
            "route_ref": self.route_ref,
            "effective_capabilities": list(self.effective_capabilities),
            "read_scope": list(self.read_scope),
            "write_scope": list(self.write_scope),
            "network_allowed": self.network_allowed,
            "device_allowed": self.device_allowed,
            "message_allowed": self.message_allowed,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "resource_intents": list(self.resource_intents),
            "approval_requirements": list(self.approval_requirements),
            "approval_satisfied": self.approval_satisfied,
            "budget": dict(self.budget),
            "forbidden_effects": list(self.forbidden_effects),
            "expires_at": self.expires_at,
            "source_policy_refs": list(self.source_policy_refs),
            "proof_trace": [dict(item) for item in self.proof_trace],
        }

    def to_dict(self) -> dict[str, Any]:
        data = self.unsigned_dict()
        data["digest"] = self.digest
        return data

    def assert_digest(self, presented_digest: str) -> None:
        if presented_digest != self.digest:
            raise StalePolicyError("stale policy digest rejected")

    def permits(
        self,
        *,
        policy_digest: str,
        required_capabilities: Sequence[str] = (),
        reads: Sequence[str] = (),
        writes: Sequence[str] = (),
        effects: Sequence[str] = (),
        approval_class: str | None = None,
        budget: Mapping[str, float | int] | None = None,
    ) -> bool:
        self.assert_digest(policy_digest)
        if not set(required_capabilities).issubset(self.effective_capabilities):
            return False
        if not all(_path_allowed(path, set(self.read_scope)) for path in reads):
            return False
        if not all(_path_allowed(path, set(self.write_scope)) for path in writes):
            return False
        for effect in effects:
            if effect in self.forbidden_effects:
                return False
            if effect == "network" and not self.network_allowed:
                return False
            if effect == "device" and not self.device_allowed:
                return False
            if effect == "message" and not self.message_allowed:
                return False
            if effect == "remote_mutation" and not self.remote_mutation_allowed:
                return False
        if approval_class and approval_class in self.approval_requirements and not self.approval_satisfied:
            return False
        if budget:
            for key, value in budget.items():
                if key not in self.budget or value > self.budget[key]:
                    return False
        return True


class MonotonicPolicyCompiler:
    """Compile independent policy ceilings using only narrowing operations."""

    def compile(
        self,
        *,
        charter: Mapping[str, Any],
        workspace_policy: Mapping[str, Any] | Any,
        agent_profile: Mapping[str, Any],
        task_envelope: Mapping[str, Any],
        pack_manifest: Mapping[str, Any],
        executor_ceiling: Mapping[str, Any],
        episode_budget: Mapping[str, Any],
        approval_state: Mapping[str, Any] | None = None,
        route_ref: str = "unrouted",
        policy_id: str = "effective-policy-r1",
    ) -> EffectivePolicy:
        sources = {
            "charter": _mapping(charter, "charter"),
            "workspace_policy": _mapping(workspace_policy, "workspace_policy"),
            "agent_profile": _mapping(agent_profile, "agent_profile"),
            "task_envelope": _mapping(task_envelope, "task_envelope"),
            "pack_manifest": _mapping(pack_manifest, "pack_manifest"),
            "executor_ceiling": _mapping(executor_ceiling, "executor_ceiling"),
            "episode_budget": _mapping(episode_budget, "episode_budget"),
        }
        _id(policy_id, "policy_id")
        _id(route_ref, "route_ref")
        parent_caps = self._intersect_dimension(
            {name: sources[name] for name in ("charter", "workspace_policy", "agent_profile")},
            ("allowed_capabilities", "capabilities", "capability_tokens", "permission_ceiling"),
            "parent capabilities",
        )
        for name in ("pack_manifest", "executor_ceiling"):
            declared = _set(sources[name], "allowed_capabilities", "capabilities", "capability_tokens", "permission_ceiling")
            if declared is None:
                raise PolicyCompileError(f"{name} has no declared capability ceiling")
            if not declared.issubset(parent_caps):
                raise PolicyCompileError(f"{name} attempts to widen parent capabilities: {sorted(declared - parent_caps)}")
        requested_caps = _set(sources["task_envelope"], "requested_capabilities", "allowed_capabilities") or set()
        caps = self._intersect_dimension(sources, ("allowed_capabilities", "capabilities", "capability_tokens", "permission_ceiling"), "capabilities")
        if not requested_caps.issubset(caps):
            raise PolicyCompileError(f"task requests capabilities outside the effective ceiling: {sorted(requested_caps - caps)}")
        effective_caps = requested_caps

        reads = self._requested_scope(sources, "reads", ("allowed_reads", "read_scope", "workspace_read_scope"))
        writes = self._requested_scope(sources, "writes", ("allowed_writes", "write_scope", "workspace_write_scope"))
        intents = self._requested_scope(sources, "resource_intents", ("resource_intents", "allowed_resource_intents"))
        if not intents:
            raise PolicyCompileError("task must declare at least one resource intent")

        forbidden: set[str] = set(FORBIDDEN_ALWAYS)
        proof: list[Mapping[str, Any]] = []
        for name, source in sources.items():
            raw = _set(source, "forbidden_effects", "hard_prohibitions", "prohibited_actions") or set()
            forbidden.update(raw)
        for dimension in BOOLEAN_DIMENSIONS:
            values: list[bool] = []
            for name, source in sources.items():
                value = _bool(source, f"{dimension}_allowed", f"allow_{dimension}")
                if value is not None:
                    values.append(value)
            if not values:
                raise PolicyCompileError(f"{dimension} has no declared ceiling")
            result = all(values)
            proof.append({"dimension": dimension, "operation": "minimum_boolean", "inputs": values, "result": result, "narrow_only": True})
            requested = _bool(sources["task_envelope"], f"requested_{dimension}", f"{dimension}_requested", default=False)
            if requested and not result:
                raise PolicyCompileError(f"task requests denied effect: {dimension}")
        if "network" in forbidden and _bool(sources["task_envelope"], "requested_network", "network_requested", default=False):
            raise PolicyCompileError("charter/policy forbids requested network effect")
        requested_effects = _set(sources["task_envelope"], "requested_effects", "effects") or set()
        denied_effects = requested_effects.intersection(forbidden)
        if denied_effects:
            raise PolicyCompileError(f"task requests forbidden effects: {sorted(denied_effects)}")

        approval_requirements = set()
        for name, source in sources.items():
            approval_requirements.update(_set(source, "approval_requirements", "required_approval_classes") or set())
        requested_approval = _set(sources["task_envelope"], "requested_approval_classes", "approval_classes") or set()
        approval = _mapping(approval_state or {}, "approval_state")
        approved_refs = _set(approval, "approved_action_refs", "action_refs") or set()
        requested_ref = approval.get("requested_action_ref")
        approval_satisfied = bool(approval.get("decision") == "ALLOW" and requested_ref and requested_ref in approved_refs)
        if requested_approval and not requested_approval.issubset(approval_requirements):
            raise PolicyCompileError("approval request is not predeclared by the effective policy")
        if approval.get("decision") == "ALLOW" and requested_ref and not requested_ref.startswith(str(sources["task_envelope"].get("task_id", ""))):
            raise PolicyCompileError("approval is not bound to the declared task")

        budgets = []
        for name, source in sources.items():
            value = _budget(source)
            if value is not None:
                budgets.append((name, value))
        if not budgets:
            raise PolicyCompileError("no budget ceiling was declared")
        budget: dict[str, float | int] = {}
        for key in ("max_actions", "max_seconds", "max_output_bytes"):
            values = [value[key] for _, value in budgets if key in value]
            if values:
                budget[key] = min(values)
                proof.append({"dimension": f"budget.{key}", "operation": "minimum", "inputs": values, "result": budget[key], "narrow_only": True})

        expiries = [value for source in sources.values() if (value := _expiry(source)) is not None]
        expires_at = min(expiries) if expiries else None
        if expiries:
            proof.append({"dimension": "expires_at", "operation": "earliest_expiry", "inputs": expiries, "result": expires_at, "narrow_only": True})
        refs = tuple(sorted({_ref(source, name) for name, source in sources.items()}))
        proof.extend([
            {"dimension": "capabilities", "operation": "intersection_then_task_subset", "source_count": len(sources), "result": sorted(effective_caps), "narrow_only": True},
            {"dimension": "read_scope", "operation": "intersection_then_task_subset", "result": sorted(reads), "narrow_only": True},
            {"dimension": "write_scope", "operation": "intersection_then_task_subset", "result": sorted(writes), "narrow_only": True},
            {"dimension": "resource_intents", "operation": "intersection_then_task_subset", "result": sorted(intents), "narrow_only": True},
            {"dimension": "forbidden_effects", "operation": "union_stronger_restrictions", "result": sorted(forbidden), "narrow_only": True},
            {"dimension": "approval", "operation": "predeclared_requirement_only", "result": approval_satisfied, "narrow_only": True},
        ])
        bools = {
            dimension: all(
                _bool(source, f"{dimension}_allowed", f"allow_{dimension}")
                for source in sources.values()
                if _bool(source, f"{dimension}_allowed", f"allow_{dimension}") is not None
            )
            for dimension in BOOLEAN_DIMENSIONS
        }
        artifact = EffectivePolicy(
            policy_id=policy_id,
            route_ref=route_ref,
            effective_capabilities=tuple(sorted(effective_caps)),
            read_scope=tuple(sorted(reads)),
            write_scope=tuple(sorted(writes)),
            network_allowed=bools["network"],
            device_allowed=bools["device"],
            message_allowed=bools["message"],
            remote_mutation_allowed=bools["remote_mutation"],
            resource_intents=tuple(sorted(intents)),
            approval_requirements=tuple(sorted(approval_requirements)),
            approval_satisfied=approval_satisfied,
            budget=budget,
            forbidden_effects=tuple(sorted(forbidden)),
            expires_at=expires_at,
            source_policy_refs=refs,
            proof_trace=tuple(proof),
            digest="",
        )
        digest = sha256_json(artifact.unsigned_dict())
        return EffectivePolicy(**{**artifact.__dict__, "digest": digest})

    def _intersect_dimension(self, sources: Mapping[str, Mapping[str, Any]], keys: Sequence[str], dimension: str) -> set[str]:
        values: list[set[str]] = []
        for name, source in sources.items():
            value = _set(source, *keys)
            if value is None:
                raise PolicyCompileError(f"{name} has no declared {dimension} ceiling")
            values.append(value)
        result = set.intersection(*values) if values else set()
        if not result:
            raise PolicyCompileError(f"effective {dimension} ceiling is empty")
        return result

    def _requested_scope(self, sources: Mapping[str, Mapping[str, Any]], dimension: str, keys: Sequence[str]) -> set[str]:
        ceilings: list[set[str]] = []
        for name, source in sources.items():
            value = _set(source, *keys)
            if value is None:
                raise PolicyCompileError(f"{name} has no declared {dimension} ceiling")
            ceilings.append(value)
        result = set.intersection(*ceilings)
        task = sources["task_envelope"]
        requested = _set(task, f"requested_{dimension}", dimension) or result
        if not requested.issubset(result):
            raise PolicyCompileError(f"task requests {dimension} outside the effective ceiling: {sorted(requested - result)}")
        return requested

    @staticmethod
    def is_narrower(parent: EffectivePolicy, child: EffectivePolicy) -> bool:
        """Return true only when every child authority dimension is narrower."""

        if not set(child.effective_capabilities).issubset(parent.effective_capabilities):
            return False
        if not set(child.read_scope).issubset(parent.read_scope) or not set(child.write_scope).issubset(parent.write_scope):
            return False
        if not set(child.resource_intents).issubset(parent.resource_intents):
            return False
        for child_value, parent_value in (
            (child.network_allowed, parent.network_allowed),
            (child.device_allowed, parent.device_allowed),
            (child.message_allowed, parent.message_allowed),
            (child.remote_mutation_allowed, parent.remote_mutation_allowed),
        ):
            if child_value and not parent_value:
                return False
        if not set(parent.forbidden_effects).issubset(child.forbidden_effects):
            return False
        for key, value in child.budget.items():
            if key not in parent.budget or value > parent.budget[key]:
                return False
        if parent.expires_at and (not child.expires_at or child.expires_at > parent.expires_at):
            return False
        return True


__all__ = ["EffectivePolicy", "MonotonicPolicyCompiler", "POLICY_SCHEMA", "PolicyCompileError", "StalePolicyError"]
