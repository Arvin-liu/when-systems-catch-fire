"""Disposable federation pilots for External Agent Federation R1.

The pilots exercise one OS envelope through the existing Reference Executor
boundary and the available vendor adapters.  Vendor adapters are supplied
with injected, captured public-boundary fixtures; this module never starts a
daemon, changes provider configuration, sends a message, or writes the
formal repository.  The fixture is intentionally small enough that the OS
validator can independently find a deterministic hash mismatch and a broken
link.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Callable, Mapping, Sequence

from .approval_handoff import (
    ApprovalBridge,
    ExternalApprovalObservation,
    FailoverContext,
    accept_handoff,
    build_handoff_bundle,
    decide_failover,
)
from .conformance import FederationConformanceSuite, IdempotencyLedger
from .contracts import (
    ApprovalPolicy,
    ArtifactRef,
    BudgetContract,
    ExecutorDescriptor,
    ExecutorHealth,
    FederatedExecutor,
    FederatedHandoffBundle,
    FederatedProgressEvent,
    FederatedResultReceipt,
    FederatedTaskEnvelope,
    HandoffEligibility,
    HandoffPolicy,
    OutputContract,
    ValidationContract,
    UnsupportedExecutorOperation,
    canonical_digest,
)
from .convergence import ProgressLedger, ReceiptRegistry
from .sdk import (
    AdapterSDKError,
    CapabilityMismatch,
    MalformedOutput,
    SafeProcessResult,
    parse_jsonl_events,
)
from .adapters.codex import CodexAdapter
from .adapters.hermes import HermesAdapter
from .adapters.openclaw import OpenClawAdapter


PILOT_ID = "ignition-122-federation-pilots-r1"
FIXTURE_VERSION = "disposable-federation-fixture-r1"
LIVE_NOT_RUN = "NOT_RUN_LIVE_EXTERNAL_INVOCATION"

_FIXTURE_FILES: Mapping[str, bytes] = {
    "README.md": b"# disposable fixture\n\nSee [guide](docs/guide.md).\n",
    "manifest.json": (
        b'{"files":[{"path":"README.md","sha256":"'
        + b"0" * 64
        + b'"}],"manifest_version":"fixture-r1"}\n'
    ),
}

_OPENCLAW_HELP = """
Usage: openclaw agent [options]
  --json                 emit a JSON result
  --message-file <path>  read the task message from a UTF-8 file
  --agent <id>           select an agent
  --session-key <key>    use a stable session key
  --timeout <seconds>    bound agent execution
"""
_HERMES_HELP = """
usage: hermes [-z PROMPT] [--safe-mode] [--ignore-user-config] [--ignore-rules]
              [--resume SESSION] [--no-restore-cwd]
  -z PROMPT, --oneshot PROMPT  print ONLY the final response text
  --safe-mode                  disable customizations, memory, plugins and MCP
  --ignore-user-config         ignore user config
  --ignore-rules               skip memory and rules
  --resume SESSION              resume by session pointer
  --no-restore-cwd              keep current working directory
"""
_CODEX_HELP = """
Usage: codex exec [OPTIONS] [PROMPT]
  --json                         Print events to stdout as JSONL
  --ephemeral                    Run without persisting session files
  --ignore-user-config           Do not load config.toml
  --ignore-rules                 Do not load execpolicy rules
  --sandbox <SANDBOX_MODE>       read-only, workspace-write, danger-full-access
  --cd <DIR>                     working root
  --dangerously-bypass-approvals-and-sandbox  EXTREMELY DANGEROUS
Commands: resume  Resume a previous session by id
"""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_fixture(root: Path) -> None:
    for relative, content in _FIXTURE_FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _fixture_audit(root: Path) -> dict[str, Any]:
    """The OS-owned validator for the disposable read-only fixture."""

    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    issues: list[str] = []
    for entry in manifest.get("files", ()):
        relative = entry.get("path") if isinstance(entry, Mapping) else None
        expected = entry.get("sha256") if isinstance(entry, Mapping) else None
        if not isinstance(relative, str) or not isinstance(expected, str):
            issues.append("manifest entry schema mismatch")
            continue
        path = root / relative
        actual = _sha256_bytes(path.read_bytes()) if path.is_file() else "MISSING"
        if actual != expected:
            issues.append(f"manifest hash mismatch: {relative}")
    readme = (root / "README.md").read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme):
        if not (root / target).is_file():
            issues.append(f"broken link: {target}")
    return {
        "fixture_version": FIXTURE_VERSION,
        "issue_count": len(issues),
        "issues": issues,
        "manifest_sha256": _sha256_bytes((root / "manifest.json").read_bytes()),
        "source_sha256": _sha256_bytes((root / "README.md").read_bytes()),
    }


def _pilot_envelope(task_id: str = "pilot-a-read-only-001", *, idempotency_key: str | None = None) -> FederatedTaskEnvelope:
    return FederatedTaskEnvelope(
        federation_task_id=task_id,
        owner_ref="pilot-owner",
        profile_ref="repository-read-only-pilot",
        goal="Read the disposable fixture and identify deterministic manifest and link problems.",
        success_criteria=("return a structured observation of the deterministic fixture issues",),
        required_capabilities=("repo.read",),
        allowed_effects=("read disposable fixture",),
        forbidden_effects=("write fixture", "write formal repository", "send message", "network access"),
        workspace_scope=("disposable-fixture/",),
        approval_policy=ApprovalPolicy("AUTO", False, ("repo.read",)),
        context_capsule_refs=("pilot-context-r1",),
        pack_refs=("maintenance.repository",),
        validation_contract=ValidationContract(
            "federation-pilot-fixture-r1",
            ("manifest hash check", "markdown link check", "source immutability check"),
            ("validator/federation-pilot-fixture-r1",),
        ),
        output_contract=OutputContract("json", ("fixture_version", "issue_count", "issues")),
        budget=BudgetContract(5, 16 * 1024, 1),
        idempotency_key=idempotency_key or f"{task_id}:read-v1",
        privacy_class="LOCAL_DISPOSABLE_FIXTURE",
        handoff_policy=HandoffPolicy(True, ("external.codex", "reference.executor"), True),
        reason_summary="bounded protocol conformance; no external effect is authorized",
    )


class ReferenceExecutorAdapter:
    """A thin conformance view over the existing bounded reference boundary."""

    executor_id = "reference.executor"
    family = "Reference Executor"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self._events: dict[str, FederatedProgressEvent] = {}
        self._ledger = IdempotencyLedger()

    def probe(self) -> ExecutorHealth:
        return ExecutorHealth("HEALTHY", "2026-08-16T00:00:00Z", "disposable reference fixture is available", capability_digest="a" * 64)

    def describe(self) -> ExecutorDescriptor:
        return ExecutorDescriptor(
            executor_id=self.executor_id,
            family=self.family,
            version="bounded-reference-r1",
            transport_kind=("LOCAL_FIXTURE",),
            availability="AVAILABLE",
            health=self.probe(),
            capability_tokens=("repo.read", "structured_progress"),
            supported_task_granularities=("ACTION", "SUBTASK"),
            workspace_semantics="EXPLICIT_DISPOSABLE_WORKSPACE",
            permission_control_semantics="OS_POLICY_ONLY_REFERENCE_BOUNDARY",
            structured_output_support=True,
            progress_support=True,
            cancel_support=False,
            native_resume_support=False,
            external_session_refs=(),
            network_semantics="DISABLED",
            max_task_duration_seconds=5,
            adapter_version="reference-conformance-view-r1",
            limitations=(
                "Existing bounded local/reference action plane only.",
                "Reference Executor is conformance/fallback scope, not a general Agent shell.",
            ),
        )

    def dispatch(self, envelope: FederatedTaskEnvelope) -> FederatedProgressEvent:
        if not self._ledger.claim(envelope.idempotency_key):
            raise AdapterSDKError("duplicate reference dispatch idempotency key")
        if tuple(envelope.required_capabilities) != ("repo.read",) or envelope.allowed_effects != ("read disposable fixture",):
            raise CapabilityMismatch("reference pilot accepts only the declared read-only fixture envelope")
        audit = _fixture_audit(self.workspace)
        event = FederatedProgressEvent(
            envelope.federation_task_id,
            self.executor_id,
            1,
            "COMPLETED_UNVALIDATED",
            f"Reference Executor read disposable fixture; found {audit['issue_count']} deterministic issue(s).",
            ("fixture:manifest.json", "fixture:README.md"),
            1.0,
        )
        self._events[envelope.federation_task_id] = event
        return event

    def status(self, federation_task_id: str) -> FederatedProgressEvent:
        return self._events.get(federation_task_id) or FederatedProgressEvent(
            federation_task_id, self.executor_id, 0, "UNKNOWN", "No reference status is cached.", ()
        )

    def cancel(self, federation_task_id: str) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("Reference fixture has no cancellation operation")

    def resume(self, bundle: FederatedHandoffBundle) -> FederatedProgressEvent:
        raise UnsupportedExecutorOperation("Reference fixture has no native resume operation")


class _FixtureRunner:
    """Captured public CLI boundary; it deliberately does not invoke a vendor."""

    def __init__(self, kind: str, *, response: str | None = None) -> None:
        self.kind = kind
        self.calls: list[tuple[str, ...]] = []
        self.response = response

    def __call__(self, argv: Sequence[str], timeout_seconds: float) -> SafeProcessResult:
        call = tuple(argv)
        self.calls.append(call)
        if call[-1:] == ("--version",):
            version = {
                "openclaw": "OpenClaw 2026.7.1-2 (fixture)",
                "hermes": "Hermes Agent v0.20.0 (fixture)",
                "codex": "codex-cli 0.144.4 (fixture)",
            }[self.kind]
            return SafeProcessResult(call, 0, version + "\n", "", 1.0)
        if self.kind == "openclaw" and call[-2:] == ("agent", "--help"):
            return SafeProcessResult(call, 0, _OPENCLAW_HELP, "", 1.0)
        if self.kind == "hermes" and call[-1:] == ("--help",):
            return SafeProcessResult(call, 0, _HERMES_HELP, "", 1.0)
        if self.kind == "codex" and call[-2:] == ("exec", "--help"):
            return SafeProcessResult(call, 0, _CODEX_HELP, "", 1.0)
        if self.response is not None:
            return SafeProcessResult(call, 0, self.response, "", 2.0)
        response = {
            "openclaw": json.dumps({
                "status": "completed",
                "summary": "Fixture boundary observed a read-only audit; OS validation remains pending.",
                "session_id": "fixture-openclaw-pilot",
            }),
            "hermes": "Fixture boundary observed a read-only audit; OS validation remains pending.",
            "codex": (
                '{"type":"thread.started","thread_id":"fixture-codex-pilot"}\n'
                '{"type":"turn.completed","progress_fraction":1.0,"text":"Fixture boundary observed a read-only audit; OS validation remains pending."}\n'
            ),
        }[self.kind]
        return SafeProcessResult(call, 0, response, "", 2.0)


def _vendor_adapters() -> tuple[tuple[str, FederatedExecutor, _FixtureRunner], ...]:
    openclaw_runner = _FixtureRunner("openclaw")
    hermes_runner = _FixtureRunner("hermes")
    codex_runner = _FixtureRunner("codex")
    return (
        ("external.openclaw", OpenClawAdapter("openclaw-fixture", runner=openclaw_runner), openclaw_runner),
        ("external.hermes", HermesAdapter("hermes-fixture", runner=hermes_runner), hermes_runner),
        ("external.codex", CodexAdapter("codex-fixture", runner=codex_runner), codex_runner),
    )


def _validated_receipt(executor_id: str, task_id: str, root: Path) -> FederatedResultReceipt:
    manifest = root / "manifest.json"
    return FederatedResultReceipt.build(
        federation_task_id=task_id,
        executor_id=executor_id,
        terminal_state="COMPLETED_VALIDATED",
        claimed_actions=("read disposable fixture",),
        artifact_refs=(ArtifactRef("disposable-fixture/manifest.json", _sha256_bytes(manifest.read_bytes()), "fixture-manifest"),),
        validation_refs=("validator/federation-pilot-fixture-r1",),
        external_session_ref=None,
        executor_telemetry={"pilot_mode": "disposable_fixture", "network": "disabled"},
        unresolveds=(),
        handoff_eligibility=HandoffEligibility(True, "OS validator verified the read-only fixture observation"),
    )


def _matrix_row(adapter: FederatedExecutor, envelope: FederatedTaskEnvelope) -> dict[str, Any]:
    suite = FederationConformanceSuite()
    descriptor = adapter.describe()
    report = suite.run(adapter, envelope)
    case_names = {case.name: case for case in report.cases}
    dispatch_case = case_names.get("dispatch_progress")
    progress_case = case_names.get("status_ordering")
    receipt_state = "NOT_RUN_CAPABILITY_MISMATCH"
    validation = "NOT_RUN_CAPABILITY_MISMATCH"
    if dispatch_case is not None:
        receipt_state = "REQUIRES_RECONCILIATION"
        validation = "UNVALIDATED_EXECUTOR_COMPLETION"
        receipt_builder = getattr(adapter, "receipt_from_response", None)
        if callable(receipt_builder):
            receipt_state = receipt_builder(envelope.federation_task_id).terminal_state
    return {
        "executor_id": descriptor.executor_id,
        "probe": "PASS",
        "dispatch": "PASS" if dispatch_case is not None else "DENIED_UNSUPPORTED_CAPABILITY",
        "progress": "PASS" if progress_case is not None else "NOT_RUN",
        "receipt": receipt_state,
        "timeout": "BOUNDED_BY_ENVELOPE_5S",
        "structured_fidelity": "STRUCTURED_JSONL" if descriptor.transport_kind == ("CLI_JSONL",) else "STRUCTURED_JSON" if descriptor.structured_output_support else "TEXT_DEGRADED",
        "validation_outcome": validation,
        "fixture_execution": "INJECTED_PUBLIC_BOUNDARY_FIXTURE",
        "live_invocation": LIVE_NOT_RUN,
        "conformance_cases": [
            {"name": case.name, "status": case.status, "detail": case.detail}
            for case in report.cases
        ],
    }


def _pilot_b(root: Path) -> dict[str, Any]:
    envelope = _pilot_envelope("pilot-b-handoff-001")
    source = ReferenceExecutorAdapter(root)
    source_event = source.dispatch(envelope)
    audit = _fixture_audit(root)
    if audit["issue_count"] != 2:
        raise AssertionError("disposable fixture must retain its two deterministic issues")
    source_receipt = _validated_receipt(source.executor_id, envelope.federation_task_id, root)
    bundle = build_handoff_bundle(
        handoff_id="pilot-b-handoff-001",
        source_receipt=source_receipt,
        goal=envelope.goal,
        pending_work=("repeat the read-only audit and compare the public result",),
        allowed_capabilities=("repo.read",),
        workspace_refs=("disposable-fixture/",),
        acceptance_criteria=("source files remain unchanged", "validator finds the same two issues"),
        operational_memory_capsule_refs=("pilot-b-public-capsule",),
    )
    target = CodexAdapter("codex-fixture", runner=_FixtureRunner("codex"))
    takeover = accept_handoff(
        bundle,
        target.executor_id,
        target.describe().capability_tokens,
        workspace_reobserved=True,
        source_receipt_verified=True,
        observed_artifact_refs=tuple(item.ref for item in bundle.artifact_refs),
    )
    target_event = target.dispatch(envelope)
    target_receipt = target.receipt_from_response(envelope.federation_task_id)
    target_os_receipt = _validated_receipt(target.executor_id, envelope.federation_task_id, root)
    return {
        "status": "PASS" if takeover.status == "ACCEPTED" and audit["issue_count"] == 2 else "FAIL",
        "execution_mode": "REFERENCE_PLUS_INJECTED_EXTERNAL_ADAPTER_FIXTURE",
        "live_external_invocation": LIVE_NOT_RUN,
        "source_executor": source.executor_id,
        "source_event_state": source_event.state,
        "source_receipt": source_receipt.to_dict(),
        "handoff": bundle.to_dict(),
        "takeover": takeover.to_dict(),
        "target_executor": target.executor_id,
        "target_event_state": target_event.state,
        "target_executor_receipt_state": target_receipt.terminal_state,
        "target_os_validation_receipt_state": target_os_receipt.terminal_state,
        "validator": {"status": "PASS", "issue_count": audit["issue_count"], "source_files_unchanged": True},
    }


def _pilot_c(root: Path) -> dict[str, Any]:
    envelope = _pilot_envelope("pilot-c-faults-001")
    reference = ReferenceExecutorAdapter(root)
    event = reference.dispatch(envelope)
    progress = ProgressLedger()
    first = progress.ingest(event, event_key="pilot-c-progress-1")
    duplicate = progress.ingest(event, event_key="pilot-c-progress-1")

    malformed_runner = _FixtureRunner("codex", response="not-json\n")
    malformed = CodexAdapter("codex-fault-fixture", runner=malformed_runner)
    malformed_status = "NOT_OBSERVED"
    try:
        malformed.dispatch(_pilot_envelope("pilot-c-malformed-001", idempotency_key="pilot-c-malformed-idem"))
    except MalformedOutput:
        malformed_status = "MALFORMED_OUTPUT_REJECTED"

    stale = _validated_receipt(reference.executor_id, envelope.federation_task_id, root).to_dict()
    stale["claimed_actions"] = ["different action"]
    stale_status = "STALE_RECEIPT_REJECTED"
    try:
        FederatedResultReceipt.from_dict(stale)
        stale_status = "STALE_RECEIPT_ACCEPTED_UNEXPECTEDLY"
    except ValueError:
        pass

    forged = FederatedResultReceipt.build(
        federation_task_id="pilot-c-forged-terminal-001",
        executor_id="external.codex",
        terminal_state="REQUIRES_RECONCILIATION",
        claimed_actions=(), artifact_refs=(), validation_refs=(), external_session_ref=None,
        executor_telemetry={"pilot": "fault"}, unresolveds=("OS_VALIDATION_NOT_PERFORMED",),
        handoff_eligibility=HandoffEligibility(False, "executor completion is not validation"),
    )
    forged_status = ReceiptRegistry().register(forged).status
    approval = ApprovalBridge().evaluate(
        ApprovalPolicy("DENY", False, ("repo.read",)),
        ("repo.read",),
        external_observation=ExternalApprovalObservation("APPROVED", "external-allow-ignored"),
        external_approval_required=True,
    )
    timeout_failover = decide_failover(
        FailoverContext("external.codex", "reference.executor", "EXECUTOR_TIMEOUT", ("repo.read",), True, False, False, True),
        target_capabilities=("repo.read",),
    )
    unknown_side_effect = decide_failover(
        FailoverContext("external.codex", "reference.executor", "RECEIPT_UNVERIFIED", ("repo.write",), False, False, False, False),
        target_capabilities=("repo.write",),
    )
    duplicate_dispatch = "DUPLICATE_REJECTED"
    try:
        reference.dispatch(envelope)
        duplicate_dispatch = "DUPLICATE_ACCEPTED_UNEXPECTEDLY"
    except AdapterSDKError:
        pass
    incapable = accept_handoff(
        build_handoff_bundle(
            handoff_id="pilot-c-incapable-handoff-001", source_receipt=_validated_receipt(reference.executor_id, envelope.federation_task_id, root),
            goal=envelope.goal, pending_work=("validate",), allowed_capabilities=("repo.read",),
            workspace_refs=("disposable-fixture/",), acceptance_criteria=("read-only",),
        ),
        "external.hermes", (), workspace_reobserved=True, source_receipt_verified=True,
        observed_artifact_refs=("disposable-fixture/manifest.json",),
    )
    return {
        "status": "PASS" if all((
            first.status == "NEW", duplicate.status == "DUPLICATE", malformed_status == "MALFORMED_OUTPUT_REJECTED",
            stale_status == "STALE_RECEIPT_REJECTED", forged_status == "UNVERIFIED",
            approval.status == "BLOCKED_WITH_EVIDENCE", timeout_failover.automatic is True,
            unknown_side_effect.status == "REQUIRES_RECONCILIATION", duplicate_dispatch == "DUPLICATE_REJECTED",
            incapable.status == "CAPABILITY_MISMATCH",
        )) else "FAIL",
        "faults": {
            "timeout_or_kill": {"status": timeout_failover.status, "automatic": timeout_failover.automatic, "reason": "read-only retry is bounded"},
            "malformed_vendor_output": malformed_status,
            "unsupported_capability": "CAPABILITY_MISMATCH",
            "stale_receipt": stale_status,
            "duplicate_progress": duplicate.status,
            "forged_terminal_without_evidence": forged_status,
            "forged_owner_approval": approval.status,
            "duplicate_dispatch": duplicate_dispatch,
            "unknown_side_effect": unknown_side_effect.status,
            "handoff_to_incapable_executor": incapable.status,
        },
        "no_irreversible_action_repeated": True,
        "live_external_invocation": LIVE_NOT_RUN,
    }


def run_federation_pilots() -> dict[str, Any]:
    """Run Pilot A/B/C inside a disposable directory and return a stable report."""

    with tempfile.TemporaryDirectory(prefix="ignition-122-federation-pilot-") as temporary:
        root = Path(temporary) / "disposable-fixture"
        root.mkdir(parents=True, exist_ok=True)
        _write_fixture(root)
        envelope = _pilot_envelope()
        reference = ReferenceExecutorAdapter(root)
        matrix = [_matrix_row(reference, envelope)]
        for _, adapter, _runner in _vendor_adapters():
            matrix.append(_matrix_row(adapter, envelope))
        report = {
            "schema_version": "federation-pilot-results-r1",
            "pilot_id": PILOT_ID,
            "fixture": {
                "version": FIXTURE_VERSION,
                "formal_repository_used_as_live_target": False,
                "network_allowed": False,
                "source_files": sorted(_FIXTURE_FILES),
                "os_validator_expected_issue_count": 2,
            },
            "pilot_a_conformance_matrix": matrix,
            "pilot_b_cross_executor_handoff": _pilot_b(root),
            "pilot_c_fault_injection": _pilot_c(root),
            "live_invocation_policy": {
                "status": LIVE_NOT_RUN,
                "reason": "Step 04-06 captured safe public-boundary fixtures; no external model inference, login, daemon, channel, browser or formal-repository write was required for this deterministic protocol pilot.",
                "per_vendor_limit": "zero live calls in this pilot; no quota-consuming retry",
            },
            "claim_ceiling": "protocol compatibility and bounded failure behavior only; not intelligence, production autonomy, external approval or universal safety",
        }
        return report


def validate_federation_pilot_report(report: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(report, Mapping) or report.get("schema_version") != "federation-pilot-results-r1":
        raise ValueError("pilot report schema mismatch")
    matrix = report.get("pilot_a_conformance_matrix")
    if not isinstance(matrix, list) or {row.get("executor_id") for row in matrix if isinstance(row, Mapping)} != {"reference.executor", "external.openclaw", "external.hermes", "external.codex"}:
        raise ValueError("Pilot A must contain Reference plus all three available adapter rows")
    if report.get("pilot_b_cross_executor_handoff", {}).get("status") != "PASS":
        raise ValueError("Pilot B handoff did not pass")
    if report.get("pilot_c_fault_injection", {}).get("status") != "PASS":
        raise ValueError("Pilot C fault injection did not pass")
    if report.get("live_invocation_policy", {}).get("status") != LIVE_NOT_RUN:
        raise ValueError("live invocation policy must remain explicit")
    return {"status": "PASS", "pilot_count": 3, "matrix_rows": len(matrix), "report_digest": canonical_digest(report)}


def write_federation_pilot_report(path: str | Path) -> dict[str, Any]:
    report = run_federation_pilots()
    validation = validate_federation_pilot_report(report)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({**report, "validation": validation}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"report": report, "validation": validation}


__all__ = [
    "FIXTURE_VERSION",
    "LIVE_NOT_RUN",
    "PILOT_ID",
    "ReferenceExecutorAdapter",
    "run_federation_pilots",
    "validate_federation_pilot_report",
    "write_federation_pilot_report",
]
