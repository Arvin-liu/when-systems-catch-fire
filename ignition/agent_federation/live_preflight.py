"""Machine preflight for bounded, no-inference live executor selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .live_adapters import LiveAdapterError, LiveCodexAdapter, LiveHermesAdapter, LiveOpenClawAdapter
from .live_bridge import LIVE_DISPATCH_SCHEMA, LiveCapabilityLease, LiveDispatchEnvelope
from .live_privacy import sanitize_public_summary


LIVE_PREFLIGHT_SCHEMA = "ignition-136-live-preflight-r1"


@dataclass(frozen=True)
class LivePreflightEntry:
    executor_id: str
    adapter_id: str
    version: str
    eligibility: str
    blockers: tuple[str, ...]
    binary_digest: str | None
    interface_digest: str | None
    workspace_semantics: str
    structured_output_semantics: str
    auth_observed: bool
    read_only_guard_observed: bool
    argv_shape: tuple[str, ...]
    estimated_initial_invocations: int
    billing_authority: str = "NO_NEW_BILLING_AUTHORITY"
    retry_policy: str = "NO_BLIND_RETRY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id, "adapter_id": self.adapter_id, "version": self.version,
            "eligibility": self.eligibility, "blockers": list(self.blockers),
            "binary_digest": self.binary_digest, "interface_digest": self.interface_digest,
            "workspace_semantics": self.workspace_semantics, "structured_output_semantics": self.structured_output_semantics,
            "auth_observed": self.auth_observed, "read_only_guard_observed": self.read_only_guard_observed,
            "argv_shape": list(self.argv_shape), "estimated_initial_invocations": self.estimated_initial_invocations,
            "billing_authority": self.billing_authority, "retry_policy": self.retry_policy,
        }


@dataclass(frozen=True)
class LivePreflightReport:
    entries: tuple[LivePreflightEntry, ...]
    selected_executor_id: str | None
    selection_reason: str
    status: str = "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": LIVE_PREFLIGHT_SCHEMA, "status": self.status,
            "entries": [entry.to_dict() for entry in self.entries],
            "selected_executor_id": self.selected_executor_id, "selection_reason": self.selection_reason,
            "no_new_billing_authority": True, "claim_ceiling": "No-inference public preflight only; eligibility is not live completion.",
        }


def _shape(argv: tuple[str, ...], workspace: Path) -> tuple[str, ...]:
    shaped: list[str] = []
    for item in argv:
        if item == str(workspace):
            shaped.append("<DISPOSABLE_WORKSPACE>")
        elif item.startswith("/"):
            shaped.append(Path(item).name)
        elif item.startswith("IGNITION_LIVE_SYNTHETIC_READONLY_TASK"):
            shaped.append("<SYNTHETIC_PROMPT>")
        else:
            shaped.append(item)
    return tuple(shaped)


def _envelope(*, executor_id: str, adapter_id: str, lease_id: str) -> LiveDispatchEnvelope:
    return LiveDispatchEnvelope(
        schema_version=LIVE_DISPATCH_SCHEMA, task_id="IGNITION-20260823-136", dispatch_id=f"preflight-{executor_id}",
        attempt_id=f"preflight-attempt-{executor_id}", executor_id=executor_id, adapter_id=adapter_id,
        capability_id="live.readonly.synthetic", capability_lease_ref=lease_id, workspace_ref="DISPOSABLE_FIXTURE_ROOT",
        workspace_mode="DISPOSABLE_READ_ONLY", permission_ceiling=("repo.read",), side_effect_class="READ_ONLY_SYNTHETIC",
        network_class="INFERENCE_TRANSPORT_ONLY", intent_capsule_ref=None, synthetic_input_ref="fixture://IGNITION-20260823-136",
        synthetic_input_digest="a" * 64, success_criteria=("return the exact synthetic fixture result",),
        output_contract={"format": "json", "required_fields": ["nonce", "line_count", "field_value", "checksum_prefix"]},
        deadline="2026-08-24T00:00:00Z", timeout_seconds=120, retry_policy="NO_BLIND_RETRY",
        reconciliation_policy="REQUIRE_ON_TIMEOUT_OR_UNKNOWN_EFFECT", budget_authority="NO_NEW_BILLING_AUTHORITY",
        provenance={"controller": "pointfire-os", "phase": "preflight-only"},
    )


def _entry(
    adapter: Any,
    *,
    workspace: Path,
    lease: LiveCapabilityLease,
    auth_observed: bool,
    read_only_guard_observed: bool,
) -> LivePreflightEntry:
    argv_shape: tuple[str, ...] = ("PROBE_ONLY",)
    if lease.live_eligibility == "ELIGIBLE_FOR_LIVE_READONLY" and not isinstance(adapter, LiveOpenClawAdapter):
        try:
            argv_shape = _shape(adapter.build_argv(_envelope(executor_id=lease.executor_id, adapter_id=adapter.adapter_id, lease_id=lease.lease_id)), workspace)
        except LiveAdapterError as exc:
            lease = LiveCapabilityLease.build(**{**lease.to_dict(), "live_eligibility": "SKIPPED_INTERFACE_UNSUPPORTED", "eligibility_blockers": (*lease.eligibility_blockers, "ARGV_BUILD_FAILED:" + type(exc).__name__)})
    return LivePreflightEntry(
        executor_id=lease.executor_id, adapter_id=adapter.adapter_id, version=sanitize_public_summary(lease.executor_version),
        eligibility=lease.live_eligibility, blockers=lease.eligibility_blockers, binary_digest=lease.binary_digest,
        interface_digest=lease.interface_digest, workspace_semantics=lease.workspace_semantics,
        structured_output_semantics=lease.structured_output_semantics, auth_observed=auth_observed,
        read_only_guard_observed=read_only_guard_observed, argv_shape=argv_shape,
        estimated_initial_invocations=1 if lease.live_eligibility == "ELIGIBLE_FOR_LIVE_READONLY" else 0,
    )


def run_live_preflight(
    workspace: str | Path,
    *,
    observed_at: str,
    expires_at: str,
    ttl_seconds: float,
    authentication_observed: Mapping[str, bool],
    read_only_guard_observed: bool,
    transports: Mapping[str, Any] | None = None,
    preferred_executor_id: str = "external.hermes",
) -> LivePreflightReport:
    root = Path(workspace)
    if not root.is_absolute() or not root.is_dir():
        raise LiveAdapterError("preflight requires an existing absolute disposable workspace")
    transports = dict(transports or {})
    adapters = (
        LiveCodexAdapter(root, transport=transports.get("external.codex"), authentication_observed=bool(authentication_observed.get("external.codex", False))),
        LiveHermesAdapter(root, transport=transports.get("external.hermes"), authentication_observed=bool(authentication_observed.get("external.hermes", False)), read_only_guard_observed=read_only_guard_observed),
        LiveOpenClawAdapter(root, transport=transports.get("external.openclaw")),
    )
    entries: list[LivePreflightEntry] = []
    for adapter in adapters:
        lease_id = "preflight-lease-" + adapter.executor_id
        try:
            lease = adapter.observe_lease(lease_id=lease_id, observed_at=observed_at, expires_at=expires_at, ttl_seconds=ttl_seconds)
        except LiveAdapterError as exc:
            entry = LivePreflightEntry(
                executor_id=adapter.executor_id, adapter_id=adapter.adapter_id, version="UNOBSERVED",
                eligibility="SKIPPED_EXECUTOR_UNAVAILABLE", blockers=("PUBLIC_PROBE_FAILED:" + type(exc).__name__,),
                binary_digest=None, interface_digest=None, workspace_semantics="UNOBSERVED", structured_output_semantics="UNOBSERVED",
                auth_observed=bool(authentication_observed.get(adapter.executor_id, False)), read_only_guard_observed=read_only_guard_observed,
                argv_shape=("PROBE_FAILED",), estimated_initial_invocations=0,
            )
        else:
            entry = _entry(adapter, workspace=root, lease=lease, auth_observed=bool(authentication_observed.get(adapter.executor_id, False)), read_only_guard_observed=read_only_guard_observed)
        entries.append(entry)
    eligible = {entry.executor_id for entry in entries if entry.eligibility == "ELIGIBLE_FOR_LIVE_READONLY"}
    selected = preferred_executor_id if preferred_executor_id in eligible else next((entry.executor_id for entry in entries if entry.executor_id in eligible), None)
    reason = "preferred bounded one-shot executor; selection is policy/request based, not intelligence ranking" if selected else "no executor satisfied the bounded preflight"
    return LivePreflightReport(tuple(entries), selected, reason)


__all__ = ["LIVE_PREFLIGHT_SCHEMA", "LivePreflightEntry", "LivePreflightReport", "run_live_preflight"]
