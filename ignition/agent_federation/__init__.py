"""External Agent Federation R1: vendor-neutral OS/executor contracts."""

from .contracts import (
    ApprovalPolicy,
    ArtifactRef,
    BudgetContract,
    ExecutorDescriptor,
    ExecutorHealth,
    ExternalSessionRef,
    FederatedExecutor,
    FederatedHandoffBundle,
    FederatedProgressEvent,
    FederatedResultReceipt,
    FederatedTaskEnvelope,
    FederationContractError,
    HandoffEligibility,
    HandoffPolicy,
    OutputContract,
    UnsupportedExecutorOperation,
    ValidationContract,
    canonical_digest,
)
from .router import (
    CandidateEvaluation,
    ExecutorRoutingProfile,
    FederationRouter,
    RoutingDecision,
    RoutingError,
    RoutingPolicy,
    RoutingRequest,
    load_routing_policy,
)
from .approval_handoff import (
    ApprovalBridge,
    ApprovalBridgeDecision,
    ApprovalHandoffError,
    ExternalApprovalObservation,
    FailoverContext,
    FailoverDecision,
    HandoffTakeoverDecision,
    accept_handoff,
    build_handoff_bundle,
    decide_failover,
)
from .convergence import (
    AbsorptionResult,
    ConvergenceError,
    FederationConvergence,
    FederationMemoryAbsorber,
    MemoryProjection,
    ProgressIngestResult,
    ProgressLedger,
    ReceiptIngestResult,
    ReceiptRegistry,
    project_approval,
    project_progress,
    project_receipt,
    project_recovery,
)
from .pilots import (
    FIXTURE_VERSION,
    LIVE_NOT_RUN,
    PILOT_ID,
    ReferenceExecutorAdapter,
    run_federation_pilots,
    validate_federation_pilot_report,
    write_federation_pilot_report,
)
from .live_bridge import LiveCapabilityLease, LiveDispatchEnvelope, LiveDispatchStateMachine, LiveExecutorReceipt, LiveTransitionError
from .live_transport import LiveProcessResult, LiveProcessTransport, LiveTransportError, interface_digest, parse_bounded_jsonl

__all__ = [
    "ApprovalPolicy", "ArtifactRef", "BudgetContract", "ExecutorDescriptor", "ExecutorHealth",
    "ExternalSessionRef", "FederatedExecutor", "FederatedHandoffBundle", "FederatedProgressEvent",
    "FederatedResultReceipt", "FederatedTaskEnvelope", "FederationContractError", "HandoffEligibility",
    "HandoffPolicy", "OutputContract", "UnsupportedExecutorOperation", "ValidationContract", "canonical_digest",
    "CandidateEvaluation", "ExecutorRoutingProfile", "FederationRouter", "RoutingDecision", "RoutingError",
    "RoutingPolicy", "RoutingRequest", "load_routing_policy",
    "ApprovalBridge", "ApprovalBridgeDecision", "ApprovalHandoffError", "ExternalApprovalObservation",
    "FailoverContext", "FailoverDecision", "HandoffTakeoverDecision", "accept_handoff",
    "build_handoff_bundle", "decide_failover",
    "AbsorptionResult", "ConvergenceError", "FederationConvergence", "FederationMemoryAbsorber", "MemoryProjection",
    "ProgressIngestResult", "ProgressLedger", "ReceiptIngestResult", "ReceiptRegistry", "project_approval",
    "project_progress", "project_receipt", "project_recovery",
    "FIXTURE_VERSION", "LIVE_NOT_RUN", "PILOT_ID", "ReferenceExecutorAdapter",
    "run_federation_pilots", "validate_federation_pilot_report", "write_federation_pilot_report",
    "LiveCapabilityLease", "LiveDispatchEnvelope", "LiveDispatchStateMachine", "LiveExecutorReceipt", "LiveTransitionError",
    "LiveProcessResult", "LiveProcessTransport", "LiveTransportError", "interface_digest", "parse_bounded_jsonl",
]
